# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Maintain the data state of the simulation and schedule model execution."""

from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
import warp as wp

from reefcraft.sim.data_store import DataStore
from reefcraft.sim.graph import ComputeGraph
from reefcraft.sim.growth_model_factory import CoralModel, GrowthModelFactory
from reefcraft.sim.models.water_model import WaterModel
from reefcraft.utils.logger import logger

if TYPE_CHECKING:
    from reefcraft.sim.growth_model import GrowthModel

# Configuration: Default coral growth model to create on startup
# Set to None to disable auto-creation, or change to another model like CoralModel.PORAG
DEFAULT_CORAL_MODEL = CoralModel.LLABRES


class CoralLocation(Enum):
    """Enumerated possible fixed locations for the corals to reside."""

    CENTER = (0.0, 0.0, 0.0)
    LEFT = (-0.3, 0.0, 0.0)
    RIGHT = (0.3, 0.0, 0.0)
    FRONT = (0.0, 0.0, 0.3)


class CoralState:
    """A base class for all coral morphological models."""

    def __init__(self, model_factory: GrowthModelFactory) -> None:
        """Initialize the coral data state within the sim."""
        self.coral_id: int = -1
        self.vertices = None
        self.indices = None
        self.model_factory = model_factory
        self._model: GrowthModel | None = None
        self._model_enum: CoralModel | None = None
        self._location: CoralLocation = CoralLocation.CENTER
        self.position = self._location.value

    @property
    def model(self) -> str:
        return self._model_enum.name if self._model_enum else ""

    @model.setter
    def model(self, value: str) -> None:
        """Set the growth model by string name."""
        try:
            model_enum: CoralModel = CoralModel[value.upper()]
        except KeyError:
            logger.warning(f"Unknown coral model string: {value}")
            return

        self._model_enum = model_enum
        self._model = self.model_factory.create(model_enum, self)
        logger.debug(f"Instantiated model: {self._model.__class__.__name__}")

    @property
    def location(self) -> str:
        """Translate the enum to a readable string."""
        return self._location.name

    @location.setter
    def location(self, value: str) -> None:
        try:
            self._location = CoralLocation[value.upper()]
            self.position = self._location.value  # Vector3
            logger.debug(f"Set location to {self._location.name} at {self.position}")
        except KeyError:
            logger.warning(f"Unknown coral location: {value}")

    def set_mesh(self, vertices: wp.array, indices: wp.array) -> None:
        """Set the mesh data directly."""
        self.vertices = vertices
        self.indices = indices

    def get_render_mesh(self) -> dict | None:
        """Retrieve the mesh data with left-handed (Y-up) coords for rendering.

        Returns None if the mesh has not been initialized yet.
        """
        if self.vertices is None or self.indices is None:
            return None
        verts_np = np.array(self.vertices.numpy(), copy=True)
        verts_np[:, [1, 2]] = verts_np[:, [2, 1]]  # Swap Y/Z for left-handed view
        return {
            "vertices": verts_np,
            "indices": np.array(self.indices.numpy(), copy=True),
        }

    def step(self, dt: float) -> None:
        """Advance the simulation state by a single dt."""
        if self._model is not None:
            self._model.update(dt)

    """possible options for LBM accessing?"""

    def get_physics_mesh(self) -> dict:
        """Return the original right-handed (Z-up) mesh for physics/coupling."""
        return {
            "vertices": np.array(self.vertices.numpy(), copy=True),
            "indices": np.array(self.indices.numpy(), copy=True),
        }

    def get_physics_wp(self) -> tuple[wp.array, wp.array]:
        """Return the warp arrays directly (no copies)."""
        return self.vertices, self.indices


class SimState:
    """Global data context and model scheduler for the simulation."""

    def __init__(self) -> None:
        """Initialize the simulation state and compute graph."""
        # Data containers
        self.corals: list[CoralState] = []

        # Compute graph, shared data store, and model factory
        self.graph = ComputeGraph()
        self.store = DataStore()
        self.graph.attach_store(self.store)
        self.model_factory = GrowthModelFactory(self)

        # Register core models
        self._water = WaterModel()
        self.graph.add_model(self._water, node_id="water")

        # Auto-create default coral if configured
        if DEFAULT_CORAL_MODEL is not None:
            logger.info(f"Auto-creating default coral with {DEFAULT_CORAL_MODEL.name} model")
            self.add_coral_with_model(DEFAULT_CORAL_MODEL)

    def add_coral(self) -> CoralState:
        """Add another coral state into the system, register its model, and return it."""
        return self.add_coral_with_model(CoralModel.LLABRES)

    def add_coral_with_model(self, model: CoralModel) -> CoralState:
        """Add a coral with the specified model and register it with the graph."""
        coral = CoralState(self.model_factory)
        # Set desired growth model before registration
        coral.model = model.name
        coral.coral_id = len(self.corals)
        self.corals.append(coral)
        if coral._model is not None:  # type: ignore[attr-defined]
            setattr(coral._model, "substeps", 3)
            self.graph.add_model(coral._model, node_id=f"coral.{coral.coral_id}", requires=["water"], priority=10)  # type: ignore[arg-type]
        return coral

    def get_fields(self) -> dict:
        """Return the fields for the state of the environment."""
        return self._water.get_field_numpy()

    def step(self, dt: float) -> None:
        """Advance all registered models by a single dt via the compute graph."""
        # Entire simulation now runs under the compute graph
        self.graph.step(dt)
