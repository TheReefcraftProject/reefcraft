# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Factory for coral growth models used in the simulation engine.

This module includes:
- The `CoralModel` enum, defining available coral growth models.
- The `GrowthModelFactory` class, which constructs model instances given a
  `SimState` and `CoralState`.

Each coral growth model uses both simulation-wide and per-coral state
to drive mesh generation and evolution.
"""
from __future__ import annotations

from enum import Enum, auto

from typing import TYPE_CHECKING

from reefcraft.sim.models.growth_model import GrowthModel

if TYPE_CHECKING:  # Avoid runtime circular import
    from reefcraft.sim.state import CoralState, SimState

# from reefcraft.sim.models.test_rect import TestRectGrowthModel


class CoralModel(Enum):
    """Enumerated coral growth models supported by the system."""

    LLABRES = auto()
    PORAG = auto()
    TEST_RECT = auto()


class GrowthModelFactory:
    """Constructs coral growth models using SimState and CoralState context.

    This factory is initialized with a reference to the global SimState
    and used to instantiate specific coral growth models with a given
    CoralModel enum and CoralState.
    """

    def __init__(self, sim_state: "SimState") -> None:
        """Initialize the factory with access to simulation-wide state."""
        self.sim_state: SimState = sim_state

    def create(self, model: CoralModel, coral_state: "CoralState") -> GrowthModel:
        """Instantiate the appropriate coral growth model class.

        Args:
            model: Enum value representing the desired coral growth model.
            coral_state: The CoralState instance this model will control.

        Returns:
            An instance of a class derived from GrowthModel.

        Raises:
            ValueError: If the provided model enum is unrecognized.
        """
        # Local imports to avoid state <-> factory <-> model circular import
        if model is CoralModel.LLABRES:
            from reefcraft.sim.models.llabres import LlabresGrowthModel

            return LlabresGrowthModel(self.sim_state, coral_state)
        elif model is CoralModel.PORAG:
            from reefcraft.sim.models.simple_porag import SimplePoragGrowthModel

            return SimplePoragGrowthModel(self.sim_state, coral_state)
        # elif model is CoralModel.TEST_RECT:
        #     from reefcraft.sim.models.test_rect import TestRectGrowthModel
        #     return TestRectGrowthModel(self.sim_state, coral_state)

        raise ValueError(f"Unhandled CoralModel: {model}")
