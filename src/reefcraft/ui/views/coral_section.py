# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""UI section for coral management and configuration.

This module provides the CoralSection and CoralItem classes that create a user
interface for managing coral entities in the Reefcraft simulation. The interface
allows users to add new corals, change their growth models, and modify their
locations within the reef environment.

The CoralSection provides:
- A title bar with an "ADD" button for creating new corals
- A scrollable list of coral items
- Dynamic addition and removal of coral controls

Each CoralItem provides:
- Coral name display
- Growth model selection (LLABRES, PORAG, TEST-RECT)
- Location selection (from predefined CoralLocation enum)
- Real-time updates to the simulation state

This UI integrates with the simulation engine to maintain synchronization
between the interface and the underlying coral simulation data.
"""

from reefcraft.sim.engine import Engine
from reefcraft.sim.state import CoralLocation, CoralState
from reefcraft.ui.control import Control
from reefcraft.ui.dropdown import Dropdown
from reefcraft.ui.icon_button import IconButton
from reefcraft.ui.label import Label, TextAlign
from reefcraft.ui.list import LayoutDirection, List
from reefcraft.ui.ui_context import UIContext
from reefcraft.utils.logger import logger


class CoralItem(List):
    """Individual coral item control with model and location configuration.

    The CoralItem represents a single coral entity in the UI, providing
    controls for modifying the coral's growth model and location. Each
    coral item maintains its own state and updates the simulation engine
    when changes are made.

    The item displays:
    - A unique coral name (auto-generated)
    - A dropdown for selecting growth models (LLABRES, PORAG, TEST-RECT)
    - A dropdown for selecting coral location within the reef

    Attributes:
        _coral_count: Class-level counter for generating unique coral names
        state: The coral's simulation state object
        name: Human-readable identifier for this coral
        model: Current growth model name
        location: Current location within the reef
        label: Text display for the coral name
        model_dropdown: Dropdown control for model selection
        location_dropdown: Dropdown control for location selection
    """

    _coral_count = 0  # Class-level counter for unique naming

    def __init__(
        self,
        state: CoralState,
        context: UIContext,
    ) -> None:
        """Initialize a new coral item with the given state and context.

        Creates a horizontal layout containing the coral name, model
        selection dropdown, and location selection dropdown. The coral
        is automatically assigned a unique name and initialized with
        the provided state values.

        Args:
            state: The coral's simulation state containing model and location
            context: UI context for rendering and event handling
        """
        super().__init__(
            context=context,
            direction=LayoutDirection.HORIZONTAL,
            spacing=6,
            margin=4,
            background=True,
        )

        self.state: CoralState = state

        # Generate unique coral name
        CoralItem._coral_count += 1
        self.name = f"Coral {CoralItem._coral_count}"

        # Set initial values from state
        self.model = state.model
        self.location = state.location

        # Create coral name label
        self.label = Label(
            context,
            text=self.name,
            width=70,
            align=TextAlign.LEFT,
            font_size=13,
        )

        # Create model selection dropdown
        self.model_dropdown = Dropdown(
            context,
            width=95,
            height=24,
            options=["LLABRES", "PORAG", "TEST-RECT"],
            on_select=self._on_model_change,
        )

        # Create location selection dropdown
        self.location_dropdown = Dropdown(
            context,
            width=80,
            height=24,
            options=[loc.name for loc in CoralLocation],
            on_select=self._on_location_change,
        )

        # Add all controls to the horizontal layout
        self.add_control(self.label)
        self.add_control(self.model_dropdown)
        self.add_control(self.location_dropdown)

    def _on_model_change(self, name: str) -> None:
        """Handle model selection changes.

        Updates the coral's growth model in both the local state and
        the simulation engine. This method is called when the user
        selects a different growth model from the dropdown.

        Args:
            name: The name of the selected growth model
        """
        logger.debug("ADD CORAL")
        self.state.model = name

    def _on_location_change(self, new_location: str) -> None:
        """Handle location selection changes.

        Updates the coral's location in both the local state and
        the simulation engine. This method is called when the user
        selects a different location from the dropdown.

        Args:
            new_location: The name of the selected location
        """
        logger.debug(f"{self.name} location: {new_location}")
        self.location = new_location
        self.state.location = new_location


class CoralSection(List):
    """UI section for managing coral entities in the simulation.

    The CoralSection provides a complete interface for coral management,
    including adding new corals and configuring existing ones. It consists
    of a title bar with an "ADD" button and a scrollable list of coral
    items that can be dynamically added and removed.

    The section integrates with the simulation engine to:
    - Create new coral entities when the ADD button is clicked
    - Maintain synchronization between UI controls and simulation state
    - Provide real-time updates to coral properties

    Attributes:
        engine: Reference to the simulation engine for coral creation
        coral_list: Container list for dynamically added coral items
    """

    def __init__(self, context: UIContext, engine: Engine) -> None:
        """Initialize the coral section with the given context and engine.

        Creates a vertical layout containing a title bar with an ADD
        button and a container for coral items. The title bar displays
        "CORALS" and provides the primary interface for adding new corals.

        Args:
            context: UI context for rendering and event handling
            engine: Simulation engine for creating and managing corals
        """
        super().__init__(
            context=context,
            background=True,
            direction=LayoutDirection.VERTICAL,
            margin=0,
        )
        self.engine = engine

        # Create title bar with ADD button
        self.add_control(
            List(
                context,
                controls=[
                    Control(context, width=10),  # Left spacing
                    Label(context, text="CORALS", width=224, align=TextAlign.LEFT, font_color="#F3F6FA"),
                    IconButton(
                        context,
                        "add.png",
                        width=24,
                        height=24,
                        toggle=False,
                        on_click=self._on_add_coral,
                        normal_tint=(0.0, 0.5),
                        hover_tint=(0.0, 1.0),
                        pressed_tint=(0.0, 1.5),
                    ),
                ],
                direction=LayoutDirection.HORIZONTAL,
                margin=5,
            )
        )

        # Create container for dynamically added coral items
        self.coral_list = List(
            context=context,
            direction=LayoutDirection.VERTICAL,
            spacing=4,
            margin=4,
        )
        self.add_control(self.coral_list)

    def _on_add_coral(self) -> None:
        """Handle ADD button clicks to create new coral entities.

        Creates a new coral in the simulation engine and adds a
        corresponding UI control to the coral list. The new coral
        is initialized with default values and immediately becomes
        available for configuration through the UI.

        Note:
            The engine runs in a background thread, so this method
            only creates the UI item and lets the engine handle
            the actual coral creation asynchronously.
        """
        logger.debug("ADD CORAL")
        coral_state = self.engine.state.add_coral()

        # Create UI item for the new coral
        # The engine's compute graph will handle the store attachment
        # and initial execution in the background thread
        item = CoralItem(
            context=self.context,
            state=coral_state,
        )
        self.coral_list.add_control(item)
