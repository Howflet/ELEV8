from enum import Enum
from datetime import datetime, timezone

class Direction(Enum):
    UP = 1
    DOWN = -1
    IDLE = 0

class Door(Enum):
    OPEN = 1
    CLOSED = 0

class Elevator:
    def __init__(self, elevator_id, current_floor, direction, capacity, current_passengers):
        self.elevator_id = elevator_id
        self.current_floor = current_floor
        self.direction = direction
        self.capacity = capacity
        self.current_passengers = current_passengers
        self.door = Door.CLOSED
        self.destination_floor = []
        self.last_stopped_floor = None
        self.dwell_ticks_remaining = 0

    def tick(self):
        self.last_stopped_floor = None
        if not self.destination_floor:
            self.direction = Direction.IDLE
            return

        # If already at a destination, stop here immediately (avoids wrong-direction initialization)
        if self.current_floor in self.destination_floor:
            self.destination_floor.remove(self.current_floor)
            self.last_stopped_floor = self.current_floor
            self.stop_at_floor()
            return

        # Set direction if idle — go toward the nearest destination first (LOOK)
        if self.direction == Direction.IDLE:
            target = min(self.destination_floor, key=lambda f: abs(f - self.current_floor))
            self.direction = Direction.UP if target > self.current_floor else Direction.DOWN

        next_dest = self.get_next_destination()

        # No destinations left in current direction — flip
        if next_dest is None:
            self.direction = Direction.UP if self.direction == Direction.DOWN else Direction.DOWN
            next_dest = self.get_next_destination()
            if next_dest is None:
                self.direction = Direction.IDLE
                return

        self.move()

    def move(self):
        self.current_floor += self.direction.value
        print(f"Elevator {self.elevator_id} moving {self.direction.name} — now at floor {self.current_floor + 1}")

    def stop_at_floor(self):
        print(f"Elevator {self.elevator_id} stopped at floor {self.current_floor + 1}")

    def open_doors(self):
        self.door = Door.OPEN
        print(f"Elevator {self.elevator_id} doors are now open")

    def close_doors(self):
        self.door = Door.CLOSED
        print(f"Elevator {self.elevator_id} doors are now closed")

    def board(self, passengers):
        for p in passengers:
            self.current_passengers.append(p)
            p.status = "boarding"
            p.boarded_at = datetime.now(timezone.utc).isoformat()
            self.add_destination(p.destination_floor)
            print(f"Passenger {p.passenger_id} boarded Elevator {self.elevator_id} at floor {self.current_floor + 1}")

    def alight(self, floor):
        alighting = [p for p in self.current_passengers if p.destination_floor == floor]
        for p in alighting:
            self.current_passengers.remove(p)
            p.status = "leaving"
            p.arrived_at = datetime.now(timezone.utc).isoformat()
            print(f"Passenger {p.passenger_id} exited Elevator {self.elevator_id} at floor {floor + 1}")

    def atDestination(self):
        return self.current_floor in self.destination_floor

    def add_destination(self, destination_floor):
        if destination_floor not in self.destination_floor:
            self.destination_floor.append(destination_floor)
            self.destination_floor.sort()

    def get_next_destination(self):
        if self.direction == Direction.UP:
            for floor in self.destination_floor:
                if floor >= self.current_floor:
                    return floor
        elif self.direction == Direction.DOWN:
            for floor in reversed(self.destination_floor):
                if floor <= self.current_floor:
                    return floor
        return None
