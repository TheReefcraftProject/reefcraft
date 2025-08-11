# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Frame scheduler that advances one or more pipelines."""

from __future__ import annotations

from typing import Iterable, List

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


