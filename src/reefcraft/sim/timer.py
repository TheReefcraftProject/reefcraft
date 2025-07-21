# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Utility class for tracking elapsed simulation time."""

import time


class Timer:
    """A simple wrapper around ``time.perf_counter``."""

    def __init__(self) -> None:
        """Create a new timer in the paused state."""
        self._start = time.perf_counter()
        self._elapsed = 0.0
        self._paused = True

    def start(self) -> None:
        """Start or resume the timer."""
        if self._paused:
            self._start = time.perf_counter() - self._elapsed
            self._paused = False

    def pause(self) -> None:
        """Pause the timer and record elapsed time."""
        if not self._paused:
            self._elapsed = time.perf_counter() - self._start
            self._paused = True

    def reset(self) -> None:
        """Reset the timer to zero and pause it."""
        self._start = time.perf_counter()
        self._elapsed = 0.0
        self._paused = True

    @property
    def time(self) -> float:
        """Current elapsed time in seconds."""
        return self._elapsed if self._paused else time.perf_counter() - self._start
