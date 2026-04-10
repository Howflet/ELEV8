import threading
from datetime import datetime, timezone
import elevator


class Building:
    DWELL_BASE    = 2   # ticks doors stay open with no passengers
    DWELL_PER_PAX = 1   # extra ticks per boarding/alighting passenger

    def __init__(self, name, floors, num_elevators, pending_requests, elevator_capacity=10,
                 floor_access=None, abandon_after_seconds=90):
        self.name = name
        self.floors = floors
        self.num_elevators = num_elevators
        self.elevator_capacity = elevator_capacity
        self.pending_requests = pending_requests
        self.elevators = [elevator.Elevator(i, 0, elevator.Direction.IDLE, elevator_capacity, []) for i in range(num_elevators)]
        self.waiting = {}                                   # floor -> [Passenger]
        self.floor_access = floor_access or {}             # {floor_int: min_access_level}
        self.abandon_after_seconds = float(abandon_after_seconds)  # 0 = never
        self.floor_stats = {}  # {floor_int: {"served": int, "total_wait": float, "max_wait": float}}
        self._lock = threading.Lock()

    def add_request(self, passenger):
        # Access check before acquiring lock — floor_access is immutable during a sim run
        required = self.floor_access.get(passenger.destination_floor, 0)
        if passenger.access_level < required:
            raise PermissionError(
                f"Floor {passenger.destination_floor + 1} requires access level {required}, "
                f"passenger has level {passenger.access_level}"
            )
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
        """Pick the best elevator using LOOK-algorithm cost estimates."""
        best, best_score = None, float('inf')
        for elev in self.elevators:
            score = self._dispatch_score(elev, passenger)
            if score < best_score:
                best_score = score
                best = elev
        return best

    def _dispatch_score(self, elev, passenger):
        """
        LOOK-algorithm cost estimate: the number of floor-hops the elevator must
        travel before it can reach and serve this passenger.  Lower = better.

        Cases ranked best → worst:
          1. Elevator idle or no queued stops            → pure distance
          2. Same direction, elevator hasn't passed yet  → will pick up en route
          3. Opposite direction heading toward floor     → finish sweep, reverse, arrive
          4. Same direction, elevator already past floor → full extra sweep required
        """
        if len(elev.current_passengers) >= elev.capacity:
            return float('inf')

        floor   = passenger.current_floor
        pax_dir = passenger.direction
        e_floor = elev.current_floor
        e_dir   = elev.direction

        # Idle / no stops queued: straight-line distance
        if e_dir == elevator.Direction.IDLE or not elev.destination_floor:
            return abs(e_floor - floor)

        top    = max(elev.destination_floor)
        bottom = min(elev.destination_floor)

        # ── Best: heading toward passenger in their travel direction ─────────
        if e_dir == elevator.Direction.UP and pax_dir == elevator.Direction.UP and e_floor <= floor:
            return floor - e_floor          # picks up en route, zero reversal cost
        if e_dir == elevator.Direction.DOWN and pax_dir == elevator.Direction.DOWN and e_floor >= floor:
            return e_floor - floor

        # ── Moderate: heading toward floor but in opposite direction ─────────
        # Must finish current sweep, reverse, then travel to the floor.
        if e_dir == elevator.Direction.DOWN and pax_dir == elevator.Direction.UP:
            return (e_floor - bottom) + (floor - bottom)
        if e_dir == elevator.Direction.UP and pax_dir == elevator.Direction.DOWN:
            return (top - e_floor) + (top - floor)

        # ── Worst: same direction but elevator has already passed the floor ──
        # Must complete current sweep, do a full reverse sweep, then return.
        if e_dir == elevator.Direction.UP and pax_dir == elevator.Direction.UP:
            return (top - e_floor) + (top - bottom) + (floor - bottom)
        if e_dir == elevator.Direction.DOWN and pax_dir == elevator.Direction.DOWN:
            return (e_floor - bottom) + (top - bottom) + (top - floor)

        return abs(e_floor - floor)  # unreachable fallback

    def tick(self):
        with self._lock:
            # ── Abandonment check ────────────────────────────────────────────
            if self.abandon_after_seconds > 0:
                now = datetime.now(timezone.utc)
                for floor in list(self.waiting.keys()):
                    remaining = []
                    for p in self.waiting[floor]:
                        ts = getattr(p, 'requested_at', None)
                        if ts and (now - datetime.fromisoformat(ts)).total_seconds() > self.abandon_after_seconds:
                            p.status = "abandoned"
                            print(f"Passenger {p.passenger_id} gave up waiting at floor {floor + 1}")
                            continue
                        remaining.append(p)
                    if remaining:
                        self.waiting[floor] = remaining
                    else:
                        del self.waiting[floor]
                        # Clean up the pickup destination from elevators if no rider still needs this floor
                        needed = any(
                            any(rp.destination_floor == floor for rp in e.current_passengers)
                            for e in self.elevators
                        )
                        if not needed:
                            for e in self.elevators:
                                if floor in e.destination_floor:
                                    e.destination_floor.remove(floor)

            # ── Elevator movement + boarding ─────────────────────────────────
            for elev in self.elevators:
                # Dwell phase: doors open, elevator stationary
                if elev.dwell_ticks_remaining > 0:
                    elev.dwell_ticks_remaining -= 1
                    if elev.dwell_ticks_remaining == 0:
                        elev.close_doors()
                    continue

                elev.tick()

                if elev.last_stopped_floor is not None:
                    floor = elev.last_stopped_floor

                    # Alight first to free capacity
                    before_alight = len(elev.current_passengers)
                    elev.alight(floor)
                    alighted = before_alight - len(elev.current_passengers)

                    # Direction-aware boarding:
                    # If no remaining destinations the elevator is effectively idle — board everyone.
                    # Otherwise only board passengers going in the elevator's current direction.
                    boarded = 0
                    if floor in self.waiting:
                        available = elev.capacity - len(elev.current_passengers)
                        if available > 0:
                            waiting_here = self.waiting[floor]
                            idle_elevator = (not elev.destination_floor or
                                             elev.direction == elevator.Direction.IDLE)
                            if idle_elevator:
                                compatible = list(waiting_here)
                                wrong_way  = []
                            else:
                                # Determine the direction the elevator will actually travel next.
                                # If no destinations remain in the current direction, it will reverse.
                                effective_dir = elev.direction
                                if elev.get_next_destination() is None:
                                    effective_dir = (elevator.Direction.UP
                                                     if elev.direction == elevator.Direction.DOWN
                                                     else elevator.Direction.DOWN)
                                compatible = [p for p in waiting_here if p.direction == effective_dir]
                                wrong_way  = [p for p in waiting_here if p.direction != effective_dir]

                            to_board = compatible[:available]
                            leftover  = compatible[available:] + wrong_way

                            elev.board(to_board)
                            boarded = len(to_board)

                            # Record wait time in floor stats for each boarded passenger
                            for p in to_board:
                                ts = getattr(p, 'requested_at', None)
                                if ts and p.boarded_at:
                                    wait = (datetime.fromisoformat(p.boarded_at) -
                                            datetime.fromisoformat(ts)).total_seconds()
                                    s = self.floor_stats.setdefault(
                                        p.current_floor,
                                        {"served": 0, "total_wait": 0.0, "max_wait": 0.0}
                                    )
                                    s["served"]     += 1
                                    s["total_wait"] += wait
                                    s["max_wait"]    = max(s["max_wait"], wait)

                            if leftover:
                                self.waiting[floor] = leftover
                            else:
                                del self.waiting[floor]

                    # Open doors and set dwell duration
                    pax_activity = alighted + boarded
                    elev.dwell_ticks_remaining = self.DWELL_BASE + pax_activity * self.DWELL_PER_PAX
                    elev.open_doors()

            # Re-dispatch any waiting passengers not covered by an elevator with space
            self._ensure_all_waiting_dispatched()

    def _ensure_all_waiting_dispatched(self):
        for floor in list(self.waiting.keys()):
            passengers = self.waiting.get(floor)
            if not passengers:
                continue
            has_coverage = any(
                floor in elev.destination_floor and len(elev.current_passengers) < elev.capacity
                for elev in self.elevators
            )
            if not has_coverage:
                candidates = [e for e in self.elevators if len(e.current_passengers) < e.capacity]
                if candidates:
                    # Use LOOK scoring with the first waiting passenger as representative
                    best = min(candidates, key=lambda e: self._dispatch_score(e, passengers[0]))
                    best.add_destination(floor)
