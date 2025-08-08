# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simulation engine with fixed time step, real-time stats, and background execution."""

import threading
import time

import warp as wp

from reefcraft.sim.state import SimState
from reefcraft.utils.logger import logger


class Engine:
    """Simulation engine with fixed time stepping, real-time rate stats, and optional background thread."""

    def __init__(self, dt: float = 0.01) -> None:
        """Initialize the engine with fixed time step and start the background thread."""
        wp.init()
        dev = wp.get_device()
        logger.info(f"Warp version:    {wp.config.version}")
        logger.info(f"Default device:  {dev}")
        logger.info(f"Device class:    {dev.__class__.__name__}")

        self.dt: float = dt
        self.sim_time: float = 0.0
        self.running: bool = False

        logger.debug("CREATE SIMSTATE")
        self.state = SimState()
        # self.water = ComputeLBM()
        # self.model = LlabresGrowthModel(self.state)

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Performance tracking
        self.step_rate_hz: float = 0.0  # Recent steps per second
        self.sim_speed_ratio: float = 0.0  # How fast simulation runs vs real time
        self._step_counter: int = 0
        self._last_rate_time: float = time.perf_counter()

        self.start_threaded()

    def __del__(self) -> None:
        """Ensure background thread is stopped during cleanup."""
        self.stop_threaded()

    def __enter__(self) -> "Engine":
        """Enter the runtime context related to this object.

        Returns:
            Engine: The engine instance itself.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        """Exit the runtime context and perform cleanup.

        Stops any threaded operations and handles exceptions if needed.

        Args:
            exc_type: The type of the exception (if any).
            exc_value: The exception instance (if any).
            traceback: The traceback object (if any).
        """
        self.stop_threaded()

    # ------------------------------------------------------------------------
    # Simulation control
    # ------------------------------------------------------------------------

    def play(self) -> None:
        """Start or resume the simulation."""
        self.running = True

    def pause(self) -> None:
        """Pause the simulation."""
        self.running = False

    def reset(self) -> None:
        """Reset the simulation state and time."""
        self.pause()
        self.sim_time = 0.0
        self.step_rate_hz = 0.0
        self.sim_speed_ratio = 0.0
        self._step_counter = 0
        self._last_rate_time = time.perf_counter()
        # self.model.reset()
        # TODO Loop through corals and reset each state
        # Optionally reset self.state or self.water if needed

    def set_dt(self, dt: float) -> None:
        """Set the fixed simulation time step."""
        self.dt = max(1e-6, min(dt, 0.1))  # Clamp to safe range

    @property
    def is_playing(self) -> bool:
        """Indicates whether the engine is currently running.

        Returns:
            bool: True if the engine is running, False otherwise.
        """
        return self.running

    def get_time(self) -> float:
        """Get the current simulation time.

        Returns:
            float: The current simulation time in seconds.
        """
        return self.sim_time

    # ------------------------------------------------------------------------
    # Simulation stepping
    # ------------------------------------------------------------------------

    def step(self) -> float:
        """Advance the simulation by one step and update tracking stats."""
        # self.model.update(self.sim_time, self.state)
        # self.water.step(self.model.get_numpy())
        self.state.step(self.dt)
        self.sim_time += self.dt

        # Performance tracking
        self._step_counter += 1
        now = time.perf_counter()
        elapsed = now - self._last_rate_time

        if elapsed > 0.5:
            self.step_rate_hz = self._step_counter / elapsed
            self.sim_speed_ratio = self.step_rate_hz * self.dt
            self._step_counter = 0
            self._last_rate_time = now

        return self.sim_time

    def update(self) -> float:
        """Advance the simulation if running."""
        return self.step() if self.running else self.sim_time

    # ------------------------------------------------------------------------
    # Background execution loop
    # ------------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Internal background loop."""
        while not self._stop_event.is_set():
            if self.running:
                self.step()
            time.sleep(0.001)  # Avoid 100% CPU

    def start_threaded(self) -> None:
        """Start the simulation loop in a background thread."""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop_threaded(self) -> None:
        """Stop the background simulation loop."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
            self._thread = None
