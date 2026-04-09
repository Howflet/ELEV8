import sys
import time
import threading
from datetime import datetime, timezone
from io import StringIO

from building import Building
from passenger import Passenger


class Simulation:
    def __init__(self, building, tick_rate=1.0):
        self.building = building
        self.tick_rate = tick_rate
        self.tick_count = 0
        self.running = False
        self._next_passenger_id = 1
        self._id_lock = threading.Lock()
        self._all_passengers = {}   # pid -> Passenger (every passenger ever submitted)
        self._log_lines = []        # captured event output from each tick
        self._log_lock = threading.Lock()

    def tick(self):
        self.tick_count += 1

        # Advance transient statuses before this tick
        with self._id_lock:
            passengers = list(self._all_passengers.values())
        for p in passengers:
            if p.status == "boarding":
                p.status = "riding"
            elif p.status == "leaving":
                p.status = "arrived"

        # Capture stdout so elevator print() calls go to the event log, not the terminal
        old_stdout = sys.stdout
        sys.stdout = buf = StringIO()
        self.building.tick()
        sys.stdout = old_stdout

        lines = [l for l in buf.getvalue().splitlines() if l.strip()]
        with self._log_lock:
            self._log_lines.extend(lines)
            self._log_lines = self._log_lines[-12:]

    def run(self, max_ticks=None):
        self.running = True
        while self.running:
            self.tick()
            if max_ticks and self.tick_count >= max_ticks:
                self.running = False
                break
            time.sleep(self.tick_rate)

    def start_background(self):
        self.running = True
        t = threading.Thread(target=self.run, daemon=True)
        t.start()
        return t

    def add_request(self, current_floor, destination_floor, access_level):
        with self._id_lock:
            pid = self._next_passenger_id
            self._next_passenger_id += 1
        p = Passenger(pid, current_floor, destination_floor, access_level)
        p.requested_at = datetime.now(timezone.utc).isoformat()
        with self._id_lock:
            self._all_passengers[pid] = p
        self.building.add_request(p)
        return pid

    def cancel_request(self, passenger_id):
        return self.building.cancel_request(passenger_id)

    def get_state(self):
        with self.building._lock:
            elevators_data = []
            for elev in self.building.elevators:
                elevators_data.append({
                    "elevator_id": elev.elevator_id,
                    "current_floor": elev.current_floor,
                    "direction": elev.direction.name,
                    "door": elev.door.name,
                    "capacity": elev.capacity,
                    "destination_floors": list(elev.destination_floor),
                    "passengers": [
                        {
                            "passenger_id": p.passenger_id,
                            "destination_floor": p.destination_floor,
                            "status": p.status,
                        }
                        for p in elev.current_passengers
                    ],
                })

            waiting_data = {}
            for floor, passengers in self.building.waiting.items():
                waiting_data[str(floor)] = [
                    {
                        "passenger_id": p.passenger_id,
                        "destination_floor": p.destination_floor,
                        "requested_at": getattr(p, "requested_at", None),
                        "status": p.status,
                    }
                    for p in passengers
                ]

            with self._log_lock:
                log_lines = list(self._log_lines)

            return {
                "tick": self.tick_count,
                "tick_rate": self.tick_rate,
                "floors": self.building.floors,
                "elevators": elevators_data,
                "waiting": waiting_data,
                "log": log_lines,
            }
