import time
from building import Building
from passenger import Passenger

class Simulation:
    def __init__(self, building, tick_rate=1.0):
        self.building = building
        self.tick_rate = tick_rate
        self.tick_count = 0
        self.running = False

    def tick(self):
        self.tick_count += 1
        print(f"\n--- Tick {self.tick_count} ---")
        self.building.tick()

    def run(self, max_ticks=None):
        self.running = True
        while self.running:
            self.tick()
            if max_ticks and self.tick_count >= max_ticks:
                self.running = False
                break
            time.sleep(self.tick_rate)
        print(f"\nSimulation ended after {self.tick_count} ticks.")
