import random

from building import Building
from passenger import Passenger
from simulation import Simulation
from visualizer import Visualizer


def run(building_name, floors, num_elevators, passengers, tick_rate=1.0, max_ticks=None):
    building = Building(building_name, floors=floors, num_elevators=num_elevators, pending_requests=[])
    sim = Simulation(building, tick_rate=tick_rate)
    for p in passengers:
        sim.add_request(p.current_floor, p.destination_floor, p.access_level)
    sim.start_background()
    viz = Visualizer(sim)
    viz.run(max_ticks=max_ticks)


# --- Scenario definitions ---

def scenario_basic():
    """Three passengers, two elevators, 10-floor building."""
    run(
        building_name="Tower One",
        floors=10,
        num_elevators=2,
        passengers=[
            Passenger(1, current_floor=0, destination_floor=5, access_level=1),
            Passenger(2, current_floor=3, destination_floor=8, access_level=1),
            Passenger(3, current_floor=7, destination_floor=1, access_level=1),
        ],
    )


def scenario_rush_hour():
    """Many passengers heading up from the ground floor."""
    run(
        building_name="Tower One",
        floors=15,
        num_elevators=3,
        passengers=[
            Passenger(1, current_floor=0, destination_floor=10, access_level=1),
            Passenger(2, current_floor=0, destination_floor=12, access_level=1),
            Passenger(3, current_floor=0, destination_floor=7,  access_level=1),
            Passenger(4, current_floor=0, destination_floor=14, access_level=1),
            Passenger(5, current_floor=0, destination_floor=3,  access_level=1),
        ],
        max_ticks=40,
    )


def scenario_single_elevator():
    """One elevator handling passengers across a tall building."""
    run(
        building_name="Slim Tower",
        floors=20,
        num_elevators=1,
        passengers=[
            Passenger(1, current_floor=0,  destination_floor=19, access_level=1),
            Passenger(2, current_floor=10, destination_floor=2,  access_level=1),
            Passenger(3, current_floor=5,  destination_floor=15, access_level=1),
        ],
    )


def scenario_midday():
    """
    120 passengers spread across all floors simulating mid-day traffic:
      - Lunch outbound: upper floors heading to lobby (floor 0)
      - Lunch return:   lobby heading back to upper floors
      - Inter-floor:    meetings and movement between mid floors
    """
    rng = random.Random(42)
    floors = 20
    passengers = []
    pid = 1

    # Lunch outbound — floors 5-19 heading to lobby
    for _ in range(40):
        src = rng.randint(5, floors - 1)
        passengers.append(Passenger(pid, current_floor=src, destination_floor=0, access_level=1))
        pid += 1

    # Lunch return — lobby heading to floors 5-19
    for _ in range(40):
        dst = rng.randint(5, floors - 1)
        passengers.append(Passenger(pid, current_floor=0, destination_floor=dst, access_level=1))
        pid += 1

    # Inter-floor traffic — random src/dst pairs on mid floors
    for _ in range(40):
        src = rng.randint(1, floors - 1)
        dst = rng.randint(1, floors - 1)
        while dst == src:
            dst = rng.randint(1, floors - 1)
        passengers.append(Passenger(pid, current_floor=src, destination_floor=dst, access_level=1))
        pid += 1

    run(
        building_name="Midday Tower",
        floors=floors,
        num_elevators=8,
        passengers=passengers,
        tick_rate=0.5,
    )


# --- Entry point ---

SCENARIOS = {
    "1": ("Basic (3 passengers, 2 elevators, 10 floors)",          scenario_basic),
    "2": ("Rush hour (5 passengers, 3 elevators, 15 floors)",      scenario_rush_hour),
    "3": ("Single elevator (3 passengers, 1 elevator, 20 floors)", scenario_single_elevator),
    "4": ("Mid-day (120 passengers, 8 elevators, 20 floors)",      scenario_midday),
}

if __name__ == "__main__":
    print("Select a scenario:")
    for key, (label, _) in SCENARIOS.items():
        print(f"  {key}. {label}")

    choice = input("\nEnter number: ").strip()
    if choice in SCENARIOS:
        _, fn = SCENARIOS[choice]
        fn()
    else:
        print(f"Invalid choice: {choice!r}")
