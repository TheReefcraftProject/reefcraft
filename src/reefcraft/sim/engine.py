# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simulation engine with fixed time step, real-time stats, and background execution.

This module provides the core simulation engine for the Reefcraft project. The Engine
class manages a fixed time-stepping simulation loop with real-time performance tracking,
background execution capabilities, and integration with the Warp physics framework.

The engine coordinates between the simulation pipeline, scheduler, and state management
to provide a robust foundation for coral reef ecosystem simulations.

Example:
    >>> engine = Engine(dt=0.01)
    >>> engine.play()
    >>> # Simulation runs in background thread
    >>> time.sleep(1.0)
    >>> print(f"Sim time: {engine.get_time():.2f}s")
    >>> print(f"Step rate: {engine.step_rate_hz:.1f} Hz")
    >>> engine.pause()
"""

import threading
import time

import warp as wp

from reefcraft.sim.pipeline import Pipeline
from reefcraft.sim.scheduler import Scheduler
from reefcraft.sim.state import SimState
from reefcraft.utils.logger import logger


class Engine:
    """Simulation engine with fixed time stepping, real-time rate stats, and optional background thread.

    The Engine class serves as the central coordinator for the simulation system. It manages
    the simulation loop, time stepping, performance monitoring, and background execution.
    The engine integrates with Warp for GPU-accelerated physics computations and provides
    a clean interface for controlling simulation execution.

    The engine operates in two modes:
    - Manual stepping: Call step() or update() explicitly
    - Background execution: Automatic stepping in a background thread

    Attributes:
        dt: Fixed time step for simulation advancement (seconds)
        sim_time: Current simulation time (seconds)
        running: Whether the simulation is currently active
        state: Simulation state container with graph and data store
        pipeline: Computational pipeline for executing simulation steps
        scheduler: Task scheduler for coordinating pipeline execution
        step_rate_hz: Current simulation step rate (steps per second)
        sim_speed_ratio: Ratio of simulation speed to real time
    """

    def __init__(self, dt: float = 0.01) -> None:
        """Initialize the engine with fixed time step and start the background thread.

        Sets up the Warp physics framework, creates the simulation infrastructure
        (state, pipeline, scheduler), and starts the background execution thread.
        The engine is ready to run immediately after initialization.

        Args:
            dt: Fixed time step for simulation advancement in seconds. Defaults to 0.01s.
                Must be positive and will be clamped to safe range [1e-6, 0.1].

        Note:
            The background thread starts automatically. Use stop_threaded() to stop it
            if you need manual control over the simulation loop.

        Example:
            >>> # Create engine with 20ms time step
            >>> engine = Engine(dt=0.02)
            >>> # Engine is ready to run
            >>> engine.play()
        """
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
        # Create pipeline and scheduler to drive the compute graph
        self.pipeline = Pipeline(name="main", graph=self.state.graph, store=self.state.store)
        self.scheduler = Scheduler([self.pipeline])

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Performance tracking
        self.step_rate_hz: float = 0.0  # Recent steps per second
        self.sim_speed_ratio: float = 0.0  # How fast simulation runs vs real time
        self._step_counter: int = 0
        self._last_rate_time: float = time.perf_counter()

        self.start_threaded()

    def __del__(self) -> None:
        """Ensure background thread is stopped during cleanup.

        Called automatically when the Engine instance is garbage collected.
        Ensures proper cleanup of background resources to prevent resource leaks.
        """
        self.stop_threaded()

    def __enter__(self) -> "Engine":
        """Enter the runtime context related to this object.

        Enables the Engine to be used as a context manager, ensuring proper
        cleanup when exiting the context.

        Returns:
            Engine: The engine instance itself.

        Example:
            >>> with Engine(dt=0.01) as engine:
            ...     engine.play()
            ...     time.sleep(1.0)
            ...     # Engine automatically cleaned up on exit
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        """Exit the runtime context and perform cleanup.

        Stops any threaded operations and handles exceptions if needed.
        This method is called automatically when exiting a context manager.

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
        """Start or resume the simulation.

        Sets the running flag to True, allowing the simulation to advance
        in the background thread. If the simulation was paused, it will
        resume from where it left off.

        Example:
            >>> engine = Engine()
            >>> engine.play()  # Start simulation
            >>> time.sleep(0.5)
            >>> engine.pause()  # Pause
            >>> engine.play()   # Resume
        """
        self.running = True

    def pause(self) -> None:
        """Pause the simulation.

        Sets the running flag to False, stopping the simulation from advancing.
        The simulation state is preserved and can be resumed later with play().

        Example:
            >>> engine = Engine()
            >>> engine.play()
            >>> # Let simulation run for a bit
            >>> time.sleep(1.0)
            >>> engine.pause()  # Pause to examine state
            >>> current_time = engine.get_time()
        """
        self.running = False

    def reset(self) -> None:
        """Reset the simulation state and time.

        Pauses the simulation and resets all timing and performance metrics
        to their initial values. The simulation state is cleared and ready
        for a fresh run.

        Note:
            This method resets timing and performance tracking but does not
            currently reset the simulation state (coral positions, water state, etc.).
            TODO: Implement full state reset functionality.

        Example:
            >>> engine = Engine()
            >>> engine.play()
            >>> time.sleep(1.0)
            >>> print(f"Sim time: {engine.get_time():.2f}s")
            >>> engine.reset()
            >>> print(f"After reset: {engine.get_time():.2f}s")  # Prints: 0.00s
        """
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
        """Set the fixed simulation time step.

        Changes the time step used for simulation advancement. The new value
        is clamped to a safe range to prevent numerical instability or
        excessive computational load.

        Args:
            dt: New time step in seconds. Will be clamped to range [1e-6, 0.1].

        Example:
            >>> engine = Engine(dt=0.01)
            >>> print(f"Initial dt: {engine.dt}")
            >>> engine.set_dt(0.005)  # Set to 5ms
            >>> print(f"New dt: {engine.dt}")
        """
        self.dt = max(1e-6, min(dt, 0.1))  # Clamp to safe range

    @property
    def is_playing(self) -> bool:
        """Indicates whether the engine is currently running.

        A read-only property that returns the current running state.
        Useful for conditional logic and status checking.

        Returns:
            bool: True if the engine is running, False otherwise.

        Example:
            >>> engine = Engine()
            >>> print(f"Initially running: {engine.is_playing}")
            >>> engine.play()
            >>> print(f"After play(): {engine.is_playing}")
        """
        return self.running

    def get_time(self) -> float:
        """Get the current simulation time.

        Returns the accumulated simulation time since the last reset.
        This represents the total time that has been simulated, not
        the wall-clock time the engine has been running.

        Returns:
            float: The current simulation time in seconds.

        Example:
            >>> engine = Engine(dt=0.01)
            >>> engine.play()
            >>> time.sleep(0.1)  # Wait 100ms real time
            >>> sim_time = engine.get_time()
            >>> print(f"Simulated {sim_time:.2f}s in 0.1s real time")
        """
        return self.sim_time

    # ------------------------------------------------------------------------
    # Simulation stepping
    # ------------------------------------------------------------------------

    def step(self) -> float:
        """Advance the simulation by one time step and update tracking stats.

        Executes one complete simulation step by:
        1. Running the scheduler/pipeline/graph computation
        2. Advancing simulation time by dt
        3. Updating performance metrics (step rate, speed ratio)

        This method is called automatically by the background thread when
        running, but can also be called manually for controlled stepping.

        Returns:
            float: The new simulation time after the step.

        Example:
            >>> engine = Engine(dt=0.01)
            >>> initial_time = engine.get_time()
            >>> new_time = engine.step()
            >>> print(f"Advanced from {initial_time:.3f}s to {new_time:.3f}s")
        """
        # Advance the simulation via the scheduler/pipeline/graph
        self.scheduler.frame(self.dt)
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
        """Advance the simulation if running.

        A convenience method that only advances the simulation when
        the running flag is True. Useful for manual stepping loops
        that want to respect the play/pause state.

        Returns:
            float: The current simulation time (may or may not have advanced).

        Example:
            >>> engine = Engine(dt=0.01)
            >>> # Manual stepping loop
            >>> for _ in range(100):
            ...     engine.update()  # Only steps if running
            ...     time.sleep(0.001)
        """
        return self.step() if self.running else self.sim_time

    # ------------------------------------------------------------------------
    # Background execution loop
    # ------------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Internal background loop for continuous simulation execution.

        This method runs in a separate thread and continuously advances
        the simulation when the running flag is True. It includes a small
        sleep to prevent excessive CPU usage.

        The loop runs until the stop event is set, typically when
        stop_threaded() is called or the engine is destroyed.
        """
        while not self._stop_event.is_set():
            if self.running:
                self.step()
            time.sleep(0.001)  # Avoid 100% CPU

    def start_threaded(self) -> None:
        """Start the simulation loop in a background thread.

        Creates and starts a daemon thread that runs the simulation loop.
        If a thread is already running, this method does nothing. The
        background thread allows the simulation to run independently
        while the main thread handles other tasks.

        Note:
            The thread is started automatically in __init__. This method
            is provided for manual control if needed.

        Example:
            >>> engine = Engine()
            >>> # Thread already started automatically
            >>> engine.stop_threaded()
            >>> # ... do other work ...
            >>> engine.start_threaded()  # Restart if needed
        """
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop_threaded(self) -> None:
        """Stop the background simulation loop.

        Signals the background thread to stop and waits for it to complete.
        This ensures clean shutdown and prevents resource leaks. The method
        is called automatically during cleanup.

        Example:
            >>> engine = Engine()
            >>> # ... use engine ...
            >>> engine.stop_threaded()  # Clean shutdown
        """
        if hasattr(self, "_stop_event"):
            self._stop_event.set()
        if hasattr(self, "_thread") and self._thread:
            self._thread.join()
            self._thread = None
