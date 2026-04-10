import sys
import time
import threading
from datetime import datetime, timezone
from io import StringIO

from building import Building
from passenger import Passenger


class Simulation:
    def __init__(self, building, seconds_per_floor=1.0):
        self.building = building
        self.seconds_per_floor = seconds_per_floor
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
            time.sleep(self.seconds_per_floor)

    def start_background(self):
        self.running = True
        t = threading.Thread(target=self.run, daemon=True)
        t.start()
        return t

    def stop_background(self):
        self.running = False

    def add_request(self, current_floor, destination_floor, access_level):
        with self._id_lock:
            pid = self._next_passenger_id
            self._next_passenger_id += 1
        p = Passenger(pid, current_floor, destination_floor, access_level)
        p.requested_at = datetime.now(timezone.utc).isoformat()
        with self._id_lock:
            self._all_passengers[pid] = p
        try:
            self.building.add_request(p)
        except PermissionError as e:
            p.status = "denied"
            return None, str(e)
        return pid, "ok"

    def cancel_request(self, passenger_id):
        return self.building.cancel_request(passenger_id)

    def get_state(self):
        # Snapshot passengers outside the building lock to avoid lock-order issues
        with self._id_lock:
            all_pax = list(self._all_passengers.values())
            terminated = [
                {
                    "passenger_id": p.passenger_id,
                    "destination_floor": p.destination_floor,
                    "status": p.status,
                    "requested_at": getattr(p, "requested_at", None),
                }
                for p in all_pax
                if p.status in ("abandoned", "denied")
            ][-20:]

        # Compute summary metrics from completed trips
        complete = [
            p for p in all_pax
            if p.arrived_at and p.boarded_at and getattr(p, "requested_at", None)
        ]
        if complete:
            waits    = [(datetime.fromisoformat(p.boarded_at)  - datetime.fromisoformat(p.requested_at)).total_seconds() for p in complete]
            journeys = [(datetime.fromisoformat(p.arrived_at)  - datetime.fromisoformat(p.boarded_at)).total_seconds()   for p in complete]
            avg_wait    = round(sum(waits)    / len(waits),    1)
            avg_journey = round(sum(journeys) / len(journeys), 1)
        else:
            avg_wait = avg_journey = 0.0

        with self.building._lock:
            elevators_data = []
            for elev in self.building.elevators:
                elevators_data.append({
                    "elevator_id": elev.elevator_id,
                    "current_floor": elev.current_floor,
                    "direction": elev.direction.name,
                    "door": elev.door.name,
                    "dwell_ticks_remaining": elev.dwell_ticks_remaining,
                    "capacity": elev.capacity,
                    "destination_floors": list(elev.destination_floor),
                    "passengers": [
                        {
                            "passenger_id": p.passenger_id,
                            "destination_floor": p.destination_floor,
                            "status": p.status,
                            "requested_at": getattr(p, "requested_at", None),
                            "boarded_at": p.boarded_at,
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

            floor_stats = {
                str(f): {
                    "served":   s["served"],
                    "avg_wait": round(s["total_wait"] / s["served"], 1),
                    "max_wait": round(s["max_wait"], 1),
                }
                for f, s in self.building.floor_stats.items()
                if s["served"] > 0
            }

            return {
                "tick": self.tick_count,
                "seconds_per_floor": self.seconds_per_floor,
                "name": self.building.name,
                "floors": self.building.floors,
                "elevators": elevators_data,
                "waiting": waiting_data,
                "log": log_lines,
                "floor_access": {str(k): v for k, v in self.building.floor_access.items()},
                "abandon_after_seconds": self.building.abandon_after_seconds,
                "terminated_passengers": terminated,
                "floor_stats": floor_stats,
                "summary": {
                    "total_served":    len(complete),
                    "avg_wait_secs":   avg_wait,
                    "avg_journey_secs": avg_journey,
                },
            }
