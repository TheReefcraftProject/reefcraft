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
    """A thin wrapper that controls a :class:`Timer`."""

    def __init__(self) -> None:
        """Prepare the engine for execution."""
        # Initialize NVIDIA Warp and log the device
        wp.init()
        dev = wp.get_device()
        logger.info(f"Warp version:    {wp.config.version}")
        logger.info(f"Default device:  {dev}")  # calls dev.__str__()
        logger.info(f"Device class:    {dev.__class__.__name__}")

        # Create the internal engine classes
        self.timer = Timer()
        self.state = SimState()
        self.model = LlabresGrowthModel()
        self.water = ComputeLBM()

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
        self.model.reset()

    def get_time(self) -> float:
        """Return the current simulation time."""
        return self.timer.time

    # ------------------------------------------------------------------------
    # Simulation API
    # ------------------------------------------------------------------------

    def update(self) -> float:
        """Advance the simulation state."""
        self.model.update(self.timer.time, self.state)
        self.water.step(self.model.get_numpy())
        return self.timer.time
