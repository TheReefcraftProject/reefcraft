# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple simulation engine used for driving updates."""

from __future__ import annotations

import taichi as ti

from .timer import Timer
from .volume import Volume


class Engine:
    """A thin wrapper that controls a :class:`Timer`."""

    def __init__(self) -> None:
        """Initialize the engine state."""
        if not getattr(ti, "is_initialized", lambda: False)():
            ti.init(arch=ti.vulkan)
        self.timer = Timer()
        self.volume = Volume()

    def start(self) -> None:
        """Start or resume the timer."""
        self.timer.start()

    def pause(self) -> None:
        """Pause the timer."""
        self.timer.pause()

    def reset(self) -> None:
        """Reset the timer to the initial state."""
        self.timer.reset()

    def update(self) -> None:
        """Advance the simulation state."""
        pass

    def get_time(self) -> float:
        """Return the current simulation time."""
        return self.timer.time
