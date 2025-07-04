# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

from __future__ import annotations

from .timer import Timer
from llabres_growth import LlabresSurface

class Engine:
    """A thin wrapper that controls a :class:`Timer`."""

    def __init__(self) -> None:
        self.timer = Timer()
        self.surface = LlabresSurface(grid_size=20)
        self.surface.reset()

    def start(self) -> None:
        self.timer.start()

    def pause(self) -> None:
        self.timer.pause()

    def reset(self) -> None:
        self.timer.reset()
        self.surface.reset()

    def update(self) -> None:
        """Advance the simulation state."""
        if not self.timer._paused:
            self.surface.step(threshold=0.8, amount=0.001)

    def get_time(self) -> float:
        return self.timer.time
