# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Scheduler for driving simulation pipelines.

This module provides the Scheduler class, which coordinates the execution
of multiple simulation pipelines during each simulation frame. The scheduler
ensures that all pipelines execute in the correct order and with consistent
timing.

The scheduler is designed to be simple and efficient, managing a collection
of pipelines and executing them sequentially during each frame update.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from reefcraft.sim.pipeline import Pipeline


class Scheduler:
    """Drive a set of pipelines each frame.

    The Scheduler class manages a collection of simulation pipelines and
    coordinates their execution during each simulation frame. It provides
    a simple interface for adding pipelines and executing them in sequence.

    The scheduler is designed to be lightweight and focused, delegating
    the actual simulation work to the individual pipelines while ensuring
    consistent timing and execution order.

    Attributes:
        _pipelines: List of pipelines managed by this scheduler.
    """

    def __init__(self, pipelines: Iterable["Pipeline"] | None = None) -> None:
        """Initialize the scheduler with optional initial pipelines.

        Creates a new scheduler instance that can manage multiple simulation
        pipelines. If pipelines are provided, they are added to the scheduler
        immediately.

        Args:
            pipelines: Optional iterable of pipelines to add initially.
                      If None, the scheduler starts with no pipelines.

        Example:
            >>> from reefcraft.sim.pipeline import Pipeline
            >>> from reefcraft.sim.graph import ComputeGraph
            >>> from reefcraft.sim.data_store import DataStore
            >>>
            >>> # Create pipeline components
            >>> graph = ComputeGraph()
            >>> store = DataStore()
            >>> pipeline = Pipeline("main", graph, store)
            >>>
            >>> # Create scheduler with the pipeline
            >>> scheduler = Scheduler([pipeline])
            >>> print(f"Scheduler has {len(scheduler._pipelines)} pipeline(s)")
        """
        self._pipelines: list["Pipeline"] = list(pipelines or [])

    def add_pipeline(self, pipeline: "Pipeline") -> None:
        """Add a new pipeline to the scheduler.

        Registers a pipeline with the scheduler, making it available for
        execution during frame updates. The pipeline will be executed in
        the order it was added.

        Args:
            pipeline: The pipeline instance to add to the scheduler.

        Example:
            >>> scheduler = Scheduler()
            >>> new_pipeline = Pipeline("secondary", graph, store)
            >>> scheduler.add_pipeline(new_pipeline)
            >>> print(f"Added pipeline: {new_pipeline.name}")
        """
        self._pipelines.append(pipeline)

    def frame(self, dt: float) -> None:
        """Execute one simulation frame across all pipelines.

        Advances all registered pipelines by one simulation step using
        the specified time step. Each pipeline's step() method is called
        in the order they were added to the scheduler.

        Args:
            dt: Time step for the simulation frame in seconds.

        Example:
            >>> scheduler = Scheduler([pipeline1, pipeline2])
            >>> # Execute one 10ms simulation frame
            >>> scheduler.frame(dt=0.01)
            >>> # All pipelines have now advanced by one step
        """
        for pipe in self._pipelines:
            pipe.step(dt)
