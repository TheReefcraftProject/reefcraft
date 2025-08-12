# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Scheduler for driving simulation pipelines."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, List

from reefcraft.sim.pipeline import Pipeline


class Scheduler:
    """Drive a set of pipelines each frame."""

    def __init__(self, pipelines: Iterable[Pipeline] | None = None) -> None:
        self._pipelines: List[Pipeline] = list(pipelines or [])

    def add_pipeline(self, pipeline: Pipeline) -> None:
        self._pipelines.append(pipeline)

    def frame(self, dt: float) -> None:
        for pipe in self._pipelines:
            pipe.step(dt)


