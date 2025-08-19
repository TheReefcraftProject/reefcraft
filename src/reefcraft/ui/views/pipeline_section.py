# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""UI section for pipeline model management and visualization.

This module provides the PipelineSection class that creates a user interface
for managing simulation models in the Reefcraft pipeline. The interface displays
currently active models and provides controls for adding new models to the
simulation.

The PipelineSection provides:
- A title bar displaying "PIPELINE"
- An add-model popup menu for selecting new model types
- A dynamic list of currently active models with icons
- Real-time updates when models are added/removed
- Visual representation of different model types (water, coral, etc.)

This UI integrates with the simulation engine to provide real-time
pipeline monitoring and model management capabilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from reefcraft.ui.control import Control
from reefcraft.ui.icon import Icon
from reefcraft.ui.label import Label, TextAlign
from reefcraft.ui.list import LayoutDirection, List
from reefcraft.ui.popup_menu import PopupMenuControl

if TYPE_CHECKING:
    from reefcraft.sim.engine import Engine
    from reefcraft.sim.model import Model
    from reefcraft.ui.ui_context import UIContext


class PipelineSection(List):
    """Pipeline management section with add-model popup and dynamic model list.

    The PipelineSection provides a complete interface for pipeline management,
    including adding new models and displaying currently active ones. It consists
    of a title bar with an add button and a dynamic list of model rows that
    updates automatically when the pipeline changes.

    The section integrates with the simulation engine to:
    - Display all currently active models in the pipeline
    - Provide controls for adding new coral models (LLABRES, PORAG)
    - Show visual indicators for different model types
    - Update automatically when pipeline state changes

    Attributes:
        engine: Reference to the simulation engine for pipeline access
        rows: Container list for dynamically added model rows
        _popup: Popup menu for selecting new model types
        _row_items: List of tuples containing (icon, label) for each model row
        _last_model_count: Tracked count of models for change detection
    """

    def __init__(self, context: UIContext, engine: Engine) -> None:
        """Initialize the pipeline section with the given context and engine.

        Creates a vertical layout containing a title bar with an add button
        and a container for model rows. The title bar displays "PIPELINE"
        and provides the primary interface for adding new models.

        Args:
            context: UI context for rendering and event handling
            engine: Simulation engine for pipeline access and model creation
        """
        super().__init__(context=context, background=True, direction=LayoutDirection.VERTICAL, margin=0)
        self.engine = engine

        # Create header row with title and add button
        header = List(
            context,
            controls=[
                Control(context, width=10),  # Left spacing
                Label(context, text="PIPELINE", width=224, align=TextAlign.LEFT, font_color="#F3F6FA"),
            ],
            direction=LayoutDirection.HORIZONTAL,
            margin=5,
        )

        # Add popup menu for model selection
        self._popup = PopupMenuControl(
            context,
            icon="add.png",
            width=24,
            height=24,
            items=["LLABRES", "PORAG"],
            on_select=self._on_add_model_selected,
        )
        header.add_control(self._popup)
        self.add_control(header)

        # Create container for model rows
        self.rows = List(context=context, direction=LayoutDirection.VERTICAL, spacing=4, margin=4, background=False)
        self.add_control(self.rows)

        # Initialize row tracking
        self._row_items: list[tuple[Icon, Label]] = []
        self._last_model_count: int = 0  # Track when models change

        # Set up automatic row updates
        self._setup_row_updates()

    def _setup_row_updates(self) -> None:
        """Set up automatic row updates when pipeline models change.

        Configures the renderer to call _ensure_rows before each render
        to keep the model list synchronized with the actual pipeline state.
        This avoids per-frame rebuilds and only updates when necessary.
        """

        def _ensure_rows(_event: object | None = None) -> None:
            """Ensure the row list matches the current pipeline models.

            This function is called before each render to check if the
            number of models has changed and rebuild the row list if needed.
            Only updates when the model count changes to avoid unnecessary work.
            """
            models = self.engine.state.graph.models
            current_count = len(models)

            # Only update if the number of models has changed
            if current_count == self._last_model_count:
                return

            self._last_model_count = current_count
            self._rebuild_rows(models)

        # Guard renderer access during headless tests
        renderer = getattr(self.context, "renderer", None)
        if renderer is not None and hasattr(renderer, "add_event_handler"):
            renderer.add_event_handler(_ensure_rows, "before_render")

    def _rebuild_rows(self, models: list) -> None:
        """Rebuild the model row list from scratch.

        Clears all existing rows and creates new ones for each model
        in the pipeline. Each row shows an appropriate icon and the
        model name.

        Args:
            models: List of models currently in the pipeline
        """
        # Clear existing rows and rebuild
        self.rows.controls.clear()
        self._row_items.clear()

        # Add new rows for each model
        for model in models:
            row = self._create_model_row(model)
            self.rows.add_control(row)

    def _create_model_row(self, model: Model) -> List:
        """Create a single row for displaying a model.

        Creates a horizontal layout containing spacing, an icon, and
        a label for the given model. The icon is chosen based on the
        model type (water, coral, etc.).

        Args:
            model: The model object to create a row for

        Returns:
            A List control containing the model row layout
        """
        row = List(context=self.context, direction=LayoutDirection.HORIZONTAL, spacing=6, margin=4, background=False)

        # Get model name and determine icon
        name = getattr(model, "name", model.__class__.__name__)
        lname = name.lower()

        # Choose appropriate icon based on model type
        if lname.startswith("water"):
            icon_name = "water.png"
        elif lname.startswith("llabres") or lname.startswith("porag"):
            icon_name = "coral.png"
        else:
            icon_name = "plus.png"  # Default icon

        # Create row components
        space = Control(self.context, width=16, height=24)
        icon = Icon(self.context, icon=icon_name, width=24, height=24, icon_width=24, icon_height=24)
        label = Label(self.context, text=name, width=194, align=TextAlign.LEFT)

        # Add components to row
        row.add_control(space)
        row.add_control(icon)
        row.add_control(label)

        # Store reference to row components
        self._row_items.append((icon, label))

        return row

    def _on_add_model_selected(self, opt: str) -> None:
        """Handle model selection from the add-model popup menu.

        Creates a new coral model of the selected type and adds it
        to the simulation pipeline. The UI will automatically update
        to show the new model in the list.

        Args:
            opt: The selected model option ("LLABRES" or "PORAG")
        """
        # Import here to avoid circular imports
        from reefcraft.sim.growth_model_factory import CoralModel

        if opt.upper() == "LLABRES":
            self.engine.state.add_coral_with_model(CoralModel.LLABRES)
        elif opt.upper() == "PORAG":
            self.engine.state.add_coral_with_model(CoralModel.PORAG)
