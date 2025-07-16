# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple simulation engine used for driving updates."""

from __future__ import annotations

from .timer import Timer
from .reef_space import ReefSpace

class Engine:
    """A thin wrapper that controls a :class:`Timer`."""

    def __init__(self) -> None:
        """Initialize the engine with a new :class:`Timer`."""
        self.timer = Timer()
        self.sim = ReefSpace()
        self.initialize_sim()
    # ------------------------------------------------------------------------
    # Timer control
    # ------------------------------------------------------------------------

    def start(self) -> None:
        """Start or resume the timer."""
        self.timer.start()

    def pause(self) -> None:
        """Pause the timer."""
        self.timer.pause()

    def reset(self) -> None:
        """Reset the timer to the initial state."""
        self.timer.reset()

    def get_time(self) -> float:
        """Return the current simulation time."""
        return self.timer.time

    # ------------------------------------------------------------------------
    # Simulation API
    # ------------------------------------------------------------------------

    def update(self) -> None:
        """Advance the simulation state."""
        self.sim.step()
        v_field = self.sim.get_fields_numpy().get("velocity") # Example grab velocity field

    def initialize_sim(self) -> None:
        """Set up sim, coral model and space"""