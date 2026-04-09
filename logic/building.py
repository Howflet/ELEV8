import threading
import elevator

class Building:
    def __init__(self, name, floors, num_elevators, pending_requests):
        self.name = name
        self.floors = floors
        self.num_elevators = num_elevators
        self.pending_requests = pending_requests
        self.elevators = [elevator.Elevator(i, 0, elevator.Direction.IDLE, 10, []) for i in range(num_elevators)]
        self.waiting = {}  # floor -> [Passenger]
        self._lock = threading.Lock()

    def add_request(self, passenger):
        with self._lock:
            self.pending_requests.append(passenger)
            self._dispatch_elevator()

    def cancel_request(self, passenger_id):
        with self._lock:
            for floor, passengers in list(self.waiting.items()):
                for p in passengers:
                    if p.passenger_id == passenger_id:
                        if p.status != "waiting":
                            return False, "already_boarded"
                        passengers.remove(p)
                        if not passengers:
                            del self.waiting[floor]
                            # Remove orphaned elevator destination if no riding passenger needs it
                            still_needed = any(
                                any(rp.destination_floor == floor for rp in elev.current_passengers)
                                for elev in self.elevators
                            )
                            if not still_needed:
                                for elev in self.elevators:
                                    if floor in elev.destination_floor:
                                        elev.destination_floor.remove(floor)
                        return True, "cancelled"
            return False, "not_found"

    # Private helpers — must be called while self._lock is held
    def _dispatch_elevator(self):
        for passenger in self.pending_requests:
            closest_elevator = self.find_closest_elevator(passenger)
            closest_elevator.add_destination(passenger.current_floor)
            self.waiting.setdefault(passenger.current_floor, []).append(passenger)
        self.pending_requests.clear()

    def find_closest_elevator(self, passenger):
        closest_elevator = None
        min_distance = float('inf')
        for elev in self.elevators:
            distance = abs(elev.current_floor - passenger.current_floor) + len(elev.destination_floor) * 2
            if distance < min_distance:
                min_distance = distance
                closest_elevator = elev
        return closest_elevator

    def tick(self):
        with self._lock:
            for elev in self.elevators:
                elev.tick()
                if elev.last_stopped_floor is not None:
                    floor = elev.last_stopped_floor
                    if floor in self.waiting:
                        available = elev.capacity - len(elev.current_passengers)
                        waiting_here = self.waiting.pop(floor)
                        elev.board(waiting_here[:available])
                        leftover = waiting_here[available:]
                        if leftover:
                            self.waiting[floor] = leftover
                            self._dispatch_to_floor(floor)
                    elev.alight(floor)

    def _dispatch_to_floor(self, floor):
        closest = min(self.elevators, key=lambda e: abs(e.current_floor - floor) + len(e.destination_floor) * 2)
        closest.add_destination(floor)
