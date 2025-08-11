# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simulation model protocol for compute-graph scheduling."""

from __future__ import annotations

from typing import Protocol


class Model(Protocol):
    """Protocol for a simulation model that can be stepped by the engine.

    A model encapsulates computation over some subset of the global state. It
    should be side-effecting on provided state objects and must be safe to call
    at a fixed rate.
    """

    name: str

    # Optional declarative I/O for DAG planning and UI auto-generation
    inputs: dict[str, str] | None  # key -> human label (or type name)
    outputs: dict[str, str] | None
    # Optional scheduling hints
    substeps: int | None
    update_rate_hz: float | None

    def step(self, dt: float) -> None:  # pragma: no cover - protocol
        """Advance the model by a fixed time step."""
        ...



