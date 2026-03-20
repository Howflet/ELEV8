import elevator

class Building:
    def __init__(self, name, floors, num_elevators, pending_requests):
        self.name = name
        self.floors = floors
        self.num_elevators = num_elevators
        self.pending_requests = pending_requests
        self.elevators = [elevator.Elevator(i, 0, elevator.Direction.IDLE, 10, []) for i in range(num_elevators)]
        self.waiting = {}  # floor -> [Passenger]
    
    def add_request(self, passenger):
        self.pending_requests.append(passenger)
        self.dispatch_elevator()

    def dispatch_elevator(self):
        for passenger in self.pending_requests:
            closest_elevator = self.find_closest_elevator(passenger)
            closest_elevator.add_destination(passenger.current_floor)
            self.waiting.setdefault(passenger.current_floor, []).append(passenger)
        self.pending_requests.clear()

    def find_closest_elevator(self, passenger):
        closest_elevator = None
        min_distance = float('inf')
        for elevator in self.elevators:
            distance = abs(elevator.current_floor - passenger.current_floor) + len(elevator.destination_floor) * 2
            if distance < min_distance:
                min_distance = distance
                closest_elevator = elevator
        return closest_elevator

    def tick(self):
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
                        self.dispatch_to_floor(floor)
                elev.alight(floor)

    def dispatch_to_floor(self, floor):
        closest = min(self.elevators, key=lambda e: abs(e.current_floor - floor) + len(e.destination_floor) * 2)
        closest.add_destination(floor)