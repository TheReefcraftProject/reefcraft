# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Maintain the data state of the simulation."""

from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
import warp as wp

from reefcraft.sim.compute_lbm import ComputeLBM
from reefcraft.sim.growth_model_factory import CoralModel, GrowthModelFactory
from reefcraft.utils.logger import logger

if TYPE_CHECKING:
    from reefcraft.sim.growth_model import GrowthModel


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
        self.vertices = None
        self.indices = None
        self.model_factory = model_factory
        self._model: GrowthModel | None = None
        self._location: CoralLocation = CoralLocation.CENTER

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

    def get_render_mesh(self) -> dict:
        """Retrieve the mesh data with left-handed (Y-up) coords for rendering."""
        # TODO: Add a check for None for the arrays
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
    """The data context for the simulation including all simulation state."""

    def __init__(self) -> None:
        """Initialize the simulation."""
        self.corals = []
        self.water = ComputeLBM()
        self.model_factory = GrowthModelFactory(self)
        # self.velocity_field: np.ndarray

    def add_coral(self) -> CoralState:
        """Add another coral state into the system and return it."""
        new_coral = CoralState(self.model_factory)
        self.corals.append(new_coral)
        return new_coral

    def get_fields(self) -> dict:
        """Return the fields for the state of the environment."""
        return self.water.get_field_numpy()

    def step(self, dt: float) -> None:
        """Advance the simulation state by a single dt."""
        self.water.step(dt)
