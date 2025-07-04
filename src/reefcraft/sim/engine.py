# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

from __future__ import annotations

from .timer import Timer


class Engine:
    """A thin wrapper that controls a :class:`Timer`."""

    def __init__(self) -> None:
        self.timer = Timer()

    def start(self) -> None:
        self.timer.start()

    def pause(self) -> None:
        self.timer.pause()

    def reset(self) -> None:
        self.timer.reset()

    def update(self) -> None:
        """Advance the simulation state."""
        pass

    def get_time(self) -> float:
        return self.timer.time
