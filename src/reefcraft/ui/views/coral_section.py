# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""A section of UI controls for Coral management."""

import pygfx as gfx

from reefcraft.sim.engine import Engine
from reefcraft.ui.control import Control
from reefcraft.ui.dropdown import Dropdown
from reefcraft.ui.icon_button import IconButton
from reefcraft.ui.label import Label, TextAlign
from reefcraft.ui.list import LayoutDirection, List
from reefcraft.ui.ui_context import UIContext
from reefcraft.utils.logger import logger


class CoralSection(List):
    """UI Section to add and change corals in the simulation."""

    def __init__(self, context: UIContext, engine: Engine) -> None:
        """Create a new coral ui layout."""
        super().__init__(
            context=context,
            background=True,
            direction=LayoutDirection.VERTICAL,
            margin=0,
        )
        self.engine = engine
        self.controls = [
            List(
                context,
                controls=[
                    Control(context, width=10),
                    Label(context, text="CORALS", width=226, align=TextAlign.LEFT, font_color="#F3F6FA"),
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
            ),
            # Additional coral controls can be dynamically inserted here
        ]
        # List of models
        growth_models = ["PORAG", "XLB", "Accretive", "Polyp-Based", "Custom SDF"]

        # Callback when user selects a model
        def on_model_selected(model_name: str) -> None:
            print(f"Selected growth model: {model_name}")
            # You could call `coral.set_growth_model(model_name)` here

        self.add_control(
            List(
                context=context,
                direction=LayoutDirection.HORIZONTAL,
                spacing=6,
                margin=6,
                background=True,
                controls=[
                    Label(
                        context=context,
                        width=120,
                        text="Growth Model",
                        align="left",
                        font_size=13,
                    ),
                    Dropdown(
                        context=context,
                        width=150,
                        height=28,
                        options=growth_models,
                        on_select=on_model_selected,
                    ),
                ],
            )
        )

    def _on_add_coral(self) -> None:
        logger.debug("ADD CORAL")
        # Add logic to modify engine state and inject new coral controls
