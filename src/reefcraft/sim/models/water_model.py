# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Model adapter around LBM water solver to participate in the compute graph.

This module provides the WaterModel class, which serves as a bridge between
the Lattice Boltzmann Method (LBM) water simulation and the Reefcraft compute
graph system. The WaterModel adapts the low-level LBM solver to conform to
the Model protocol, enabling it to participate in dependency-aware execution.

The WaterModel manages:
- Water field simulation (density, pressure, velocity)
- Coral mesh boundary conditions
- Data store integration for field output
- LBM solver coordination and stepping

This model is typically executed first in the simulation pipeline, as other
models (like corals) depend on the water environment for their calculations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from reefcraft.sim.compute_lbm import ComputeLBM
from reefcraft.sim.model import Model

if TYPE_CHECKING:
    from reefcraft.sim.data_store import DataStore


class WaterModel(Model):
    """Adapter that exposes the LBM solver as a graph model.

    The WaterModel class wraps the Lattice Boltzmann Method (LBM) water
    simulation solver and makes it compatible with the Reefcraft compute
    graph system. It implements the Model protocol and provides a clean
    interface for water simulation within the larger ecosystem simulation.

    The model simulates fluid dynamics including:
    - Density field evolution
    - Pressure distribution
    - Velocity field calculation
    - Boundary condition handling with coral meshes

    The WaterModel is designed to run early in the simulation pipeline
    since other models depend on the water environment for their calculations.

    Attributes:
        name: Human-readable identifier for the model
        inputs: Declarative input specification for the compute graph
        outputs: Declarative output specification for the compute graph
        substeps: Number of substeps per simulation frame (None = use default)
        update_rate_hz: Target update frequency (None = use default)
        _lbm: Internal LBM solver instance
        _pending_coral_mesh: Coral mesh data waiting to be applied
        _store: Optional shared data store for I/O operations
    """

    def __init__(self) -> None:
        """Initialize the water model with default configuration.

        Creates a new WaterModel instance with the LBM solver and sets up
        the input/output specifications for the compute graph. The model
        starts with no coral mesh and no data store attached.
        """
        self.name = "Water"
        self.inputs = {"coral_mesh": "Coral Mesh (verts, faces)"}
        self.outputs = {
            "water.density": "Density Field",
            "water.pressure": "Pressure Field",
            "water.velocity": "Velocity Field",
            "water.velocity_magnitude": "Velocity Magnitude",
        }
        self.substeps: int | None = None
        self.update_rate_hz: float | None = None
        self._lbm = ComputeLBM()
        self._pending_coral_mesh: tuple | None = None
        self._store: "DataStore" | None = None

    def set_coral_mesh(self, mesh: tuple) -> None:
        """Provide coral mesh for boundary conditions.

        Sets the coral mesh data that will be used as boundary conditions
        in the water simulation. The mesh consists of vertices and faces
        stored as Warp arrays for efficient GPU computation.

        Args:
            mesh: Tuple containing (vertices, faces) as Warp arrays.
                  Vertices should be 3D positions, faces should be triangle indices.

        Example:
            >>> water_model = WaterModel()
            >>> vertices = wp.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
            >>> faces = wp.array([[0, 1, 2]])
            >>> water_model.set_coral_mesh((vertices, faces))
        """
        self._pending_coral_mesh = mesh

    def attach_store(self, store: "DataStore") -> None:
        """Optional injection of a shared DataStore for I/O by key.

        Connects a data store to the water model, enabling it to publish
        simulation results and potentially read input data. This method
        is called automatically by the compute graph system.

        Args:
            store: The data store instance to attach for I/O operations.

        Note:
            This method is optional - the water model can function without
            a data store, but won't be able to share results with other models.
        """
        self._store = store

    def step(self, dt: float) -> None:
        """Execute one simulation step.

        Advances the water simulation by one time step. This method:
        1. Checks for coral mesh updates from the data store
        2. Applies any pending coral mesh as boundary conditions
        3. Steps the LBM solver forward in time

        The method automatically handles coral mesh updates if a data store
        is attached and contains coral mesh data.

        Args:
            dt: Time step for the simulation frame in seconds.
                Note: The LBM solver may use its own internal time stepping.

        Example:
            >>> water_model = WaterModel()
            >>> # Execute a 10ms simulation step
            >>> water_model.step(dt=0.01)
            >>> # Water fields have now advanced by one step
        """
        # Pull coral mesh from the store if present
        if self._store is not None and self._store.has("coral.0.mesh"):
            self._pending_coral_mesh = self._store.get("coral.0.mesh")

        if self._pending_coral_mesh is not None:
            self._lbm.update_mesh(self._pending_coral_mesh)
            self._pending_coral_mesh = None
        self._lbm.step(dt)

    def get_field_numpy(self) -> dict:
        """Retrieve water simulation fields as numpy arrays.

        Returns the current state of all water simulation fields in a
        format suitable for visualization, analysis, or coupling with
        other simulation components. The fields are also published to
        the data store if one is attached.

        Returns:
            Dictionary containing water field data with keys:
            - 'density': Fluid density field as numpy array
            - 'pressure': Pressure field as numpy array
            - 'velocity': Velocity vector field as numpy array
            - 'velocity_magnitude': Scalar velocity magnitude field

        Example:
            >>> water_model = WaterModel()
            >>> fields = water_model.get_field_numpy()
            >>> print(f"Density field shape: {fields['density'].shape}")
            >>> print(f"Velocity range: {fields['velocity_magnitude'].min():.3f} to {fields['velocity_magnitude'].max():.3f}")

        Note:
            If a data store is attached, all fields are automatically
            published with "water." prefix for other models to access.
        """
        fields = self._lbm.get_field_numpy()
        # Also publish to store for other models/visualization
        if self._store is not None:
            for k, v in fields.items():
                self._store.put(f"water.{k}", v)
        return fields
