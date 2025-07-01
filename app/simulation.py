# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

from reefcraft import seed, sim_value


class SimulationEngine:
    """Starting point for Reefcraft simulation engine"""

    def __init__(self) -> None:
        self._time = 0.0  # curr sim time
        self._running = False  # is sim ticking?
        self._timestep = 1 / 60.0  # ~60 FPS
        self._seed = 12345  # fixed seed
        self._last_val = 0.0  # most recent sim_value output
        self._growth_rate = 1.0  # default growth rate

        seed(self._seed)  # initialize rng

    def start(self) -> None:
        self._running = True
        print("[Engine] Started")

    def pause(self) -> None:
        self._running = False

    def reset(self) -> None:
        self._time = 0.0
        seed(self._seed)
        self._last_val = sim_value(self._time)

    def update(self) -> None:
        if self._running:
            self._time += self._timestep * self._growth_rate
            self._last_val = sim_value(self._time)

    def get_last_value(self) -> float:
        return self._last_val

    def get_time(self) -> float:
        return self._time

    def set_growth_rate(self, rate: float) -> None:
        self._growth_rate = rate
