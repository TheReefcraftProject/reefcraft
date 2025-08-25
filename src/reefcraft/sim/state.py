# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Maintain the data state of the simulation and schedule model execution.

This module provides the core state management for the Reefcraft simulation system.
It defines the SimState class which serves as the central coordinator for all
simulation data, models, and execution scheduling.

The module includes:
- CoralState: Individual coral entity management
- CoralLocation: Predefined coral placement positions
- SimState: Global simulation state and model coordination
- Automatic coral creation and model registration
- Integration with the compute graph and data store

The state system automatically creates a default coral on startup and manages
the execution order of all simulation models through dependency-aware scheduling.
"""

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
    from reefcraft.sim.models.growth_model import GrowthModel

# Configuration: Default coral growth model to create on startup
# Set to None to disable auto-creation, or change to another model like CoralModel.PORAG
DEFAULT_CORAL_MODEL = CoralModel.LLABRES


class CoralLocation(Enum):
    """Enumerated possible fixed locations for the corals to reside.

    Defines predefined positions where corals can be placed in the simulation
    environment. These locations are used for consistent coral placement and
    can be referenced by name for easy positioning.

    Each location is defined as a 3D coordinate tuple (x, y, z) where:
    - x: left/right position (negative = left, positive = right)
    - y: up/down position (typically 0 for ground level)
    - z: front/back position (negative = back, positive = front)
    """

    CENTER = (0.0, 0.0, 0.0)
    LEFT = (-0.3, 0.0, 0.0)
    RIGHT = (0.3, 0.0, 0.0)
    FRONT = (0.0, 0.0, 0.3)


class CoralState:
    """A base class for all coral morphological models.

    CoralState represents a single coral entity in the simulation. It manages
    the coral's mesh data, growth model, position, and provides interfaces
    for rendering and physics simulation.

    Each coral maintains:
    - Unique identifier and position
    - 3D mesh data (vertices and indices)
    - Growth model instance for simulation
    - Location enum for consistent positioning

    The class provides methods for mesh manipulation, coordinate system
    conversion (right-handed for physics, left-handed for rendering),
    and integration with the growth simulation system.

    Attributes:
        coral_id: Unique identifier for this coral instance
        vertices: Warp array containing vertex positions
        indices: Warp array containing face indices
        model_factory: Factory for creating growth models
        _model: Current growth model instance
        _model_enum: Enum value of the current model type
        _location: Current location enum value
        position: 3D position vector derived from location
    """

    def __init__(self, model_factory: GrowthModelFactory) -> None:
        """Initialize the coral data state within the sim.

        Creates a new coral instance with default values. The coral starts
        at the center location with no mesh data and no growth model.

        Args:
            model_factory: Factory instance for creating growth models.
        """
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
        """Get the current growth model name.

        Returns the string representation of the current growth model.
        If no model is set, returns an empty string.

        Returns:
            Name of the current growth model, or empty string if none.
        """
        return self._model_enum.name if self._model_enum else ""

    @model.setter
    def model(self, value: str) -> None:
        """Set the growth model by string name.

        Changes the coral's growth model to the specified type. The model
        name is case-insensitive and must match one of the available
        CoralModel enum values.

        Args:
            value: String name of the growth model (e.g., "LLABRES", "PORAG").

        Note:
            If an invalid model name is provided, a warning is logged and
            the current model remains unchanged.

        Example:
            >>> coral = CoralState(factory)
            >>> coral.model = "llabres"  # Case-insensitive
            >>> print(coral.model)  # "LLABRES"
        """
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
        """Get the current location name.

        Returns the string representation of the coral's current location.

        Returns:
            Name of the current location (e.g., "CENTER", "LEFT").
        """
        return self._location.name

    @location.setter
    def location(self, value: str) -> None:
        """Set the coral's location by string name.

        Changes the coral's position to one of the predefined locations.
        The location name is case-insensitive and must match one of the
        CoralLocation enum values.

        Args:
            value: String name of the location (e.g., "center", "left").

        Note:
            If an invalid location name is provided, a warning is logged
            and the current location remains unchanged.

        Example:
            >>> coral = CoralState(factory)
            >>> coral.location = "left"
            >>> print(coral.position)  # (-0.3, 0.0, 0.0)
        """
        try:
            self._location = CoralLocation[value.upper()]
            self.position = self._location.value  # Vector3
            logger.debug(f"Set location to {self._location.name} at {self.position}")
        except KeyError:
            logger.warning(f"Unknown coral location: {value}")

    def set_mesh(self, vertices: wp.array, indices: wp.array) -> None:
        """Set the mesh data directly.

        Assigns the 3D mesh data for this coral. The mesh consists of
        vertex positions and face indices stored as Warp arrays for
        efficient GPU computation.

        Args:
            vertices: Warp array containing 3D vertex positions.
            indices: Warp array containing face indices (triangles).
        """
        self.vertices = vertices
        self.indices = indices

    def get_render_mesh(self) -> dict | None:
        """Retrieve the mesh data with left-handed (Y-up) coords for rendering.

        Converts the internal mesh data to a format suitable for rendering
        systems that expect left-handed coordinates with Y pointing up.
        This involves swapping the Y and Z coordinates.

        Returns:
            Dictionary containing 'vertices' and 'indices' as numpy arrays,
            or None if the mesh has not been initialized yet.

        Note:
            The returned mesh is in left-handed coordinate system (Y-up)
            suitable for most rendering engines.
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
        """Advance the simulation state by a single dt.

        Updates the coral's growth model if one is assigned. This method
        is called by the simulation engine during each time step.

        Args:
            dt: Time step for the simulation frame in seconds.
        """
        if self._model is not None:
            self._model.update(dt)

    """possible options for LBM accessing?"""

    def get_physics_mesh(self) -> dict:
        """Return the original right-handed (Z-up) mesh for physics/coupling.

        Provides the mesh data in the original coordinate system used by
        the physics simulation. This maintains the right-handed coordinate
        system with Z pointing up.

        Returns:
            Dictionary containing 'vertices' and 'indices' as numpy arrays.
            Returns empty dict if mesh is not initialized.

        Note:
            The returned mesh is in right-handed coordinate system (Z-up)
            suitable for physics simulation and coupling with other systems.
        """
        if self.vertices is None or self.indices is None:
            return {}
        return {
            "vertices": np.array(self.vertices.numpy(), copy=True),
            "indices": np.array(self.indices.numpy(), copy=True),
        }

    def get_physics_wp(self) -> tuple[wp.array, wp.array] | tuple[None, None]:
        """Return the warp arrays directly (no copies).

        Provides direct access to the underlying Warp arrays without
        creating copies. This is useful for efficient GPU computation
        where the data doesn't need to be converted to numpy.

        Returns:
            Tuple of (vertices, indices) as Warp arrays, or (None, None)
            if the mesh has not been initialized.

        Note:
            The returned arrays are the original data - modifications
            will affect the coral's mesh directly.
        """
        if self.vertices is None or self.indices is None:
            return None, None
        return self.vertices, self.indices


class SimState:
    """Global data context and model scheduler for the simulation.

    SimState serves as the central coordinator for the entire simulation.
    It manages the global state, coordinates model execution, and provides
    a unified interface for accessing simulation data.

    The class maintains:
    - Collection of coral entities
    - Compute graph for execution scheduling
    - Shared data store for model communication
    - Model factory for creating growth models
    - Water model for environmental simulation

    SimState automatically creates a default coral on startup and manages
    the execution order of all models through dependency-aware scheduling.
    The water model is always registered first, and corals depend on it.

    Attributes:
        corals: List of all coral entities in the simulation
        graph: Compute graph for managing model execution order
        store: Shared data store for model I/O operations
        model_factory: Factory for creating coral growth models
        _water: Water simulation model instance
    """

    def __init__(self) -> None:
        """Initialize the simulation state and compute graph.

        Sets up the complete simulation infrastructure including:
        - Empty coral collection
        - Compute graph with data store attachment
        - Model factory for coral creation
        - Water model registration
        - Automatic default coral creation

        The water model is registered first with node_id "water", and
        subsequent corals will depend on it for proper execution order.
        """
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

        self.time = 0.0
        self.last_dt = 0.01

    def add_coral(self) -> CoralState:
        """Add another coral state into the system, register its model, and return it.

        Creates a new coral with the default LLABRES growth model and
        registers it with the compute graph. The coral is automatically
        assigned a unique ID and positioned at the center location.

        Returns:
            The newly created coral instance.

        Example:
            >>> sim_state = SimState()
            >>> new_coral = sim_state.add_coral()
            >>> print(f"Added coral {new_coral.coral_id} with {new_coral.model} model")
        """
        return self.add_coral_with_model(CoralModel.LLABRES)

    def add_coral_with_model(self, model: CoralModel) -> CoralState:
        """Add a coral with the specified model and register it with the graph.

        Creates a new coral with the specified growth model type and
        integrates it into the simulation system. The coral is registered
        with the compute graph with a dependency on the water model.

        Args:
            model: The growth model type to use for this coral.

        Returns:
            The newly created coral instance.

        Note:
            The coral is automatically assigned a unique ID and registered
            in the compute graph with priority 10 and a dependency on "water".
            The growth model is configured with 3 substeps for finer simulation.

        Example:
            >>> sim_state = SimState()
            >>> coral = sim_state.add_coral_with_model(CoralModel.PORAG)
            >>> print(f"Added {coral.model} coral at {coral.location}")
        """
        coral = CoralState(self.model_factory)
        # Set desired growth model before registration
        coral.model = model.name
        coral.coral_id = len(self.corals)
        self.corals.append(coral)
        if coral._model is not None:
            setattr(coral._model, "substeps", 3)
            self.graph.add_model(coral._model, node_id=f"coral.{coral.coral_id}", requires=["water"], priority=10)
        return coral

    def get_fields(self) -> dict:
        """Return the fields for the state of the environment.

        Retrieves the current water simulation fields including density,
        pressure, velocity, and velocity magnitude. These fields represent
        the environmental conditions that affect coral growth.

        Returns:
            Dictionary containing water field data as numpy arrays.

        Example:
            >>> sim_state = SimState()
            >>> fields = sim_state.get_fields()
            >>> print(f"Water density range: {fields['water.density'].min():.3f} to {fields['water.density'].max():.3f}")
        """
        return self._water.get_field_numpy()

    @property
    def water(self):
        """Access the water model for UI compatibility."""
        return self._water

    def step(self, dt: float) -> None:
        """Advance all registered models by a single dt via the compute graph.

        Executes one simulation step for all registered models in the
        correct dependency order. The compute graph ensures that models
        execute in the proper sequence (e.g., water before corals).

        Args:
            dt: Time step for the simulation frame in seconds.

        Note:
            This method delegates all simulation execution to the compute
            graph, which handles dependency resolution and execution ordering.
            The entire simulation now runs under the compute graph system.
        """
        # Entire simulation now runs under the compute graph
        self.graph.step(dt)
