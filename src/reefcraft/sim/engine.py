# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simulation engine used for driving updates."""

import warp as wp

from reefcraft.sim.compute_lbm import ComputeLBM
from reefcraft.sim.llabres import LlabresGrowthModel
from reefcraft.sim.state import SimState
from reefcraft.sim.timer import Timer
from reefcraft.utils.logger import logger


class Engine:
    """A thin wrapper that controls a :class:`Timer` and coordinates simulation components."""

    def __init__(self) -> None:
        """Prepare the engine for execution."""
        wp.init()
        dev = wp.get_device()
        logger.info(f"Warp version:    {wp.config.version}")
        logger.info(f"Default device:  {dev}")
        logger.info(f"Device class:    {dev.__class__.__name__}")

        self.timer = Timer()
        self.state = SimState()
        self.model = LlabresGrowthModel(self.state)
        self.water = ComputeLBM()

    # ------------------------------------------------------------------------
    # Timer control
    # ------------------------------------------------------------------------

    def play(self) -> None:
        """Start or resume the simulation."""
        self.timer.start()

    def pause(self) -> None:
        """Pause the simulation."""
        self.timer.pause()

    def reset(self) -> None:
        """Reset the simulation and pause."""
        self.pause()
        self.timer.reset()
        self.model.reset()
        # Optionally: reset self.state or water if needed

    def get_time(self) -> float:
        """Return the current simulation time."""
        return self.timer.time

    @property
    def is_playing(self) -> bool:
        """Return True if the simulation is currently playing."""
        return self.timer.is_running

    # ------------------------------------------------------------------------
    # Simulation API
    # ------------------------------------------------------------------------

    def update(self) -> float:
        """Advance the simulation state if timer is running."""
        if not self.is_playing:
            return self.timer.time

        self.model.update(self.timer.time, self.state)
        self.water.step(self.model.get_numpy())
        return self.timer.time
