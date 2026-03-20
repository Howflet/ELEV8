from elevator import Direction

class Passenger:
    def __init__(self, passenger_id, current_floor, destination_floor, access_level):
        self.passenger_id = passenger_id
        self.current_floor = current_floor
        self.destination_floor = destination_floor
        self.access_level = access_level
        self.direction = Direction.UP if destination_floor > current_floor else Direction.DOWN
        self.status = "waiting"

    def __str__(self):
        return f"Passenger {self.passenger_id} at floor {self.current_floor} going to floor {self.destination_floor}"