# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Model adapter around LBM water solver to participate in the compute graph."""

from __future__ import annotations

from typing import Optional

from reefcraft.sim.compute_lbm import ComputeLBM
from reefcraft.sim.model import Model


class WaterModel:
    """Adapter that exposes the LBM solver as a graph model."""

    def __init__(self) -> None:
        self.name = "water"
        self.inputs = {"coral_mesh": "Coral Mesh (verts, faces)"}
        self.outputs = {
            "water.density": "Density Field",
            "water.pressure": "Pressure Field",
            "water.velocity": "Velocity Field",
            "water.velocity_magnitude": "Velocity Magnitude",
        }
        self._lbm = ComputeLBM()
        self._pending_coral_mesh: Optional[tuple] = None
        self._store = None

    def set_coral_mesh(self, mesh: tuple) -> None:
        """Provide coral mesh for boundary conditions (verts, faces as Warp arrays)."""
        self._pending_coral_mesh = mesh

    def attach_store(self, store) -> None:
        """Optional injection of a shared DataStore for I/O by key."""
        self._store = store

    def step(self, dt: float) -> None:  # noqa: ARG002 - dt unused by LBM stepper
        # Pull coral mesh from the store if present
        if self._store is not None and self._store.has("coral.0.mesh"):
            self._pending_coral_mesh = self._store.get("coral.0.mesh")

        if self._pending_coral_mesh is not None:
            self._lbm.update_mesh(self._pending_coral_mesh)
            self._pending_coral_mesh = None
        self._lbm.step(dt)

    # Convenience accessors for visualization/UI
    def get_field_numpy(self) -> dict:
        fields = self._lbm.get_field_numpy()
        # Also publish to store for other models/visualization
        if self._store is not None:
            for k, v in fields.items():
                self._store.put(f"water.{k}", v)
        return fields


