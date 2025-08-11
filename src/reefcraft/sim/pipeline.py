# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Pipeline wrapper around the compute graph and shared data store."""

from __future__ import annotations

from typing import TYPE_CHECKING

from reefcraft.sim.graph import ComputeGraph

if TYPE_CHECKING:
    from reefcraft.sim.data_store import DataStore


class Pipeline:
    """A simple pipeline that advances the compute graph each step."""

    def __init__(self, name: str, graph: ComputeGraph, store: DataStore) -> None:
        self.name = name
        self.graph = graph
        self.store = store

    def prepare(self) -> None:
        # Future: call operator.prepare if provided
        return None

    def step(self, dt: float) -> None:
        self.graph.step(dt)

    def finalize(self) -> None:
        # Future: call operator.finalize if provided
        return None


