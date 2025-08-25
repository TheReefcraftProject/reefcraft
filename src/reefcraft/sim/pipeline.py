# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Pipeline wrapper around the compute graph and shared data store.

This module provides the Pipeline class, which serves as a high-level interface
for executing simulation steps. The Pipeline coordinates between a compute graph
and a data store, providing a clean abstraction for simulation execution.

The Pipeline is designed to be extensible, with hooks for future preparation
and finalization steps that can be added as the simulation system evolves.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reefcraft.sim.data_store import DataStore
    from reefcraft.sim.graph import ComputeGraph


class Pipeline:
    """A simple pipeline that advances the compute graph each step.

    The Pipeline class provides a unified interface for executing simulation
    steps by coordinating between a compute graph and a shared data store.
    It acts as a thin wrapper that can be extended with additional functionality
    such as preparation, finalization, and monitoring hooks.

    The Pipeline is designed to be simple and focused, delegating the actual
    computation to the underlying compute graph while providing a consistent
    interface for the simulation engine.

    Attributes:
        name: Human-readable identifier for the pipeline instance.
        graph: The compute graph that manages model execution order.
        store: Shared data store for model I/O operations.
    """

    def __init__(self, name: str, graph: ComputeGraph, store: "DataStore") -> None:
        """Initialize a new pipeline instance.

        Creates a pipeline that will execute the specified compute graph
        using the provided data store. The pipeline is ready to execute
        immediately after initialization.

        Args:
            name: Human-readable name for the pipeline, useful for logging
                  and debugging purposes.
            graph: The compute graph that defines the execution order and
                   contains the models to be executed.
            store: The data store that models will use for input/output
                   operations during execution.

        Example:
            >>> from reefcraft.sim.graph import ComputeGraph
            >>> from reefcraft.sim.data_store import DataStore
            >>>
            >>> # Create the pipeline components
            >>> graph = ComputeGraph()
            >>> store = DataStore()
            >>>
            >>> # Create the pipeline
            >>> pipeline = Pipeline("main_simulation", graph, store)
            >>> print(f"Pipeline '{pipeline.name}' ready for execution")
        """
        self.name = name
        self.graph = graph
        self.store = store

    def prepare(self) -> None:
        """Prepare the pipeline for execution.

        This method is called before the pipeline begins execution. It's
        designed as a hook for future functionality such as:
        - Initializing models and their state
        - Setting up data structures
        - Validating configuration
        - Allocating resources

        Currently, this method is a no-op but provides a consistent
        interface for future extensions.

        Example:
            >>> pipeline = Pipeline("test", graph, store)
            >>> pipeline.prepare()  # Ready for execution
            >>> pipeline.step(dt=0.01)
        """
        # Future: call operator.prepare if provided
        return None

    def step(self, dt: float) -> None:
        """Execute one simulation step.

        Advances the simulation by executing all models in the compute graph
        with the specified time step. The models execute in dependency order,
        and each model can access the shared data store for I/O operations.

        Args:
            dt: Time step for the simulation frame in seconds.

        Example:
            >>> pipeline = Pipeline("coral_sim", graph, store)
            >>> # Execute a single 10ms simulation step
            >>> pipeline.step(dt=0.01)
            >>> # The compute graph has advanced all models
        """
        self.graph.step(dt)

    def finalize(self) -> None:
        """Finalize the pipeline after execution.

        This method is called after the pipeline has finished execution.
        It's designed as a hook for future functionality such as:
        - Cleaning up resources
        - Saving final state
        - Generating reports
        - Validating results

        Currently, this method is a no-op but provides a consistent
        interface for future extensions.

        Example:
            >>> pipeline = Pipeline("simulation", graph, store)
            >>> pipeline.prepare()
            >>> for _ in range(100):
            ...     pipeline.step(dt=0.01)
            >>> pipeline.finalize()  # Clean up and save results
        """
        # Future: call operator.finalize if provided
        return None
