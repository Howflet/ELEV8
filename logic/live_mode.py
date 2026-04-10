import math
import random
import time
import threading


class LiveModeManager:
    VALID_PATTERNS = {"random", "morning_rush", "evening_rush", "lunch_rush", "auto"}
    _INTERVAL = 0.1  # seconds between Poisson checks (10 Hz)

    # Rush-hour peaks: (hour, sigma) in simulated 24-hour time
    _RUSH_PEAKS = [
        ("morning_rush", 8.5,  0.75),
        ("lunch_rush",   12.0, 0.50),
        ("evening_rush", 17.5, 0.75),
    ]
    _BASELINE_RANDOM_WEIGHT = 0.30  # always-on floor-to-floor baseline in auto mode

    def __init__(self, sim, rate_per_minute=10.0, pattern="random",
                 cafeteria_floor=None, access_level=1,
                 inter_floor_pct=0.20,
                 sim_start_hour=6.0, sim_speed=60.0):
        self._sim             = sim
        self._rate_per_minute = float(rate_per_minute)
        self._pattern         = pattern
        self._cafeteria_floor = cafeteria_floor  # resolved at start() if None
        self._access_level    = access_level
        self._inter_floor_pct = float(inter_floor_pct)   # fraction of trips that are inter-floor
        self._sim_start_hour  = float(sim_start_hour) % 24.0  # simulated hour at spawn time
        self._sim_speed       = float(sim_speed)         # sim-minutes per real-second
        self._running         = False
        self._thread          = None
        self._lock            = threading.Lock()
        self._passengers_spawned = 0
        self._started_at      = None

    # ── public API ──────────────────────────────────────────────────────────────

    def start(self):
        with self._lock:
            if self._running:
                return
            if self._cafeteria_floor is None:
                self._cafeteria_floor = self._sim.building.floors // 2
            self._running = True
            self._started_at = time.time()
            self._passengers_spawned = 0
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        with self._lock:
            self._running = False

    def update(self, rate_per_minute=None, pattern=None, cafeteria_floor=None,
               inter_floor_pct=None, sim_start_hour=None, sim_speed=None):
        with self._lock:
            if rate_per_minute is not None:
                rate_per_minute = float(rate_per_minute)
                if not (0.1 <= rate_per_minute <= 120):
                    raise ValueError("rate_per_minute must be between 0.1 and 120")
                self._rate_per_minute = rate_per_minute
            if pattern is not None:
                if pattern not in self.VALID_PATTERNS:
                    raise ValueError(f"pattern must be one of {sorted(self.VALID_PATTERNS)}")
                self._pattern = pattern
            if cafeteria_floor is not None:
                floors = self._sim.building.floors
                if not (0 <= cafeteria_floor < floors):
                    raise ValueError(f"cafeteria_floor must be between 0 and {floors - 1}")
                self._cafeteria_floor = cafeteria_floor
            if inter_floor_pct is not None:
                inter_floor_pct = float(inter_floor_pct)
                if not (0.0 <= inter_floor_pct <= 1.0):
                    raise ValueError("inter_floor_pct must be between 0.0 and 1.0")
                self._inter_floor_pct = inter_floor_pct
            if sim_start_hour is not None:
                self._sim_start_hour = float(sim_start_hour) % 24.0
            if sim_speed is not None:
                self._sim_speed = float(sim_speed)

    def get_status(self):
        with self._lock:
            uptime = (time.time() - self._started_at) if self._running and self._started_at else None
            sim_hour = self._current_sim_hour() if (self._running and self._started_at) else None
            return {
                "active":             self._running,
                "rate_per_minute":    self._rate_per_minute,
                "pattern":            self._pattern,
                "cafeteria_floor":    self._cafeteria_floor,
                "passengers_spawned": self._passengers_spawned,
                "uptime_seconds":     round(uptime, 1) if uptime is not None else None,
                "inter_floor_pct":    self._inter_floor_pct,
                "sim_hour":           round(sim_hour, 2) if sim_hour is not None else None,
                "sim_speed":          self._sim_speed,
            }

    # ── internal ────────────────────────────────────────────────────────────────

    def _current_sim_hour(self):
        """Return the current simulated hour (0–24) based on elapsed real time."""
        elapsed_real_seconds = time.time() - self._started_at
        elapsed_sim_minutes = elapsed_real_seconds * self._sim_speed
        return (self._sim_start_hour + elapsed_sim_minutes / 60.0) % 24.0

    def _time_blended_pattern(self):
        """
        Sample a concrete pattern name from a Gaussian mixture centred on each
        rush-hour peak, plus a constant baseline for random inter-floor traffic.
        This gives smooth ramp-up and ramp-down instead of abrupt switches.
        """
        h = self._current_sim_hour()

        names   = [name for name, _, _ in self._RUSH_PEAKS] + ["random"]
        weights = [
            math.exp(-0.5 * ((h - peak) / sigma) ** 2)
            for _, peak, sigma in self._RUSH_PEAKS
        ] + [self._BASELINE_RANDOM_WEIGHT]

        return names[self._weighted_choice(weights)]

    def _run_loop(self):
        while True:
            with self._lock:
                if not self._running:
                    break
                rate    = self._rate_per_minute
                pattern = self._pattern
                caf     = self._cafeteria_floor

            if self._should_spawn(rate):
                floors = self._sim.building.floors
                src, dst = self._pick_floors(pattern, floors, caf)
                if src != dst:
                    pid, _ = self._sim.add_request(src, dst, self._access_level)
                    if pid is not None:
                        with self._lock:
                            self._passengers_spawned += 1

            time.sleep(self._INTERVAL)

    def _should_spawn(self, rate_per_minute):
        lam = rate_per_minute / 60.0
        prob = 1.0 - math.exp(-lam * self._INTERVAL)
        return random.random() < prob

    @staticmethod
    def _weighted_choice(weights):
        total = sum(weights)
        r = random.random() * total
        cumulative = 0.0
        for i, w in enumerate(weights):
            cumulative += w
            if r < cumulative:
                return i
        return len(weights) - 1

    def _pick_floors(self, pattern, floors, cafeteria_floor):
        wc = self._weighted_choice

        # Inter-floor injection: a fraction of all trips bypass the active pattern
        # and become pure floor-to-floor movements (meetings, collaboration spaces, etc.)
        if random.random() < self._inter_floor_pct:
            src = wc([1.0] * floors)
            dst_w = [1.0] * floors
            dst_w[src] = 0.0
            return src, wc(dst_w)

        # Resolve "auto" to a concrete pattern via smooth time-of-day blending
        if pattern == "auto":
            pattern = self._time_blended_pattern()

        if pattern == "morning_rush":
            # ~70% of passengers originate from ground floor (floor 0)
            src_w = [1.0] * floors
            src_w[0] += floors * (0.7 / 0.3)
            src = wc(src_w)
            # Destinations weighted toward upper floors
            dst_w = [0.1 + 0.9 * f / (floors - 1) for f in range(floors)]
            dst_w[src] = 0.0
            dst = wc(dst_w)

        elif pattern == "evening_rush":
            # Passengers originate from upper floors (weighted)
            src_w = [0.1 + 0.9 * f / (floors - 1) for f in range(floors)]
            src = wc(src_w)
            # ~70% heading to ground floor
            dst_w = [1.0] * floors
            dst_w[0] += floors * (0.7 / 0.3)
            dst_w[src] = 0.0
            dst = wc(dst_w)

        elif pattern == "lunch_rush":
            caf = cafeteria_floor if cafeteria_floor is not None else floors // 2
            r = random.random()
            if r < 0.40:       # outbound to cafeteria
                src_w = [1.0] * floors
                src_w[caf] = 0.0
                src = wc(src_w)
                dst = caf
            elif r < 0.80:     # return from cafeteria
                src = caf
                dst_w = [1.0] * floors
                dst_w[caf] = 0.0
                dst = wc(dst_w)
            else:              # random inter-floor
                src_w = [1.0] * floors
                src = wc(src_w)
                dst_w = [1.0] * floors
                dst_w[src] = 0.0
                dst = wc(dst_w)

        else:  # "random"
            src_w = [1.0] * floors
            src = wc(src_w)
            dst_w = [1.0] * floors
            dst_w[src] = 0.0
            dst = wc(dst_w)

        return src, dst
