# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

from __future__ import annotations

from .llabres_growth import LlabresSurface
from .mesh_seed import gen_llabres_seed
from .timer import Timer


class Engine:
    """A thin wrapper that controls a :class:`Timer`."""

    def __init__(self) -> None:
        self.timer = Timer()
        verts, faces, edges = gen_llabres_seed(radius=1.0, height=0.1)
        self.surface = LlabresSurface(verts, faces, edges)

    def start(self) -> None:
        self.timer.start()

    def pause(self) -> None:
        self.timer.pause()

    def reset(self) -> None:
        self.timer.reset()
        # self.surface.reset()

    def update(self) -> None:
        """Advance the simulation state."""
        if not self.timer._paused:
            self.surface.compute_norms()
            self.surface.grow(threshold=0.8, amount=0.001)

    def get_time(self) -> float:
        return self.timer.time
