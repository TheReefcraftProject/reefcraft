# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""A section of UI controls for Coral management."""

from collections.abc import Callable

import pygfx as gfx

from reefcraft.sim.engine import Engine
from reefcraft.ui.control import Control
from reefcraft.ui.dropdown import Dropdown
from reefcraft.ui.icon_button import IconButton

# coral_item.py
from reefcraft.ui.label import Label, TextAlign
from reefcraft.ui.list import LayoutDirection, List
from reefcraft.ui.ui_context import UIContext
from reefcraft.utils.logger import logger


class CoralItem(List):
    _coral_count = 0  # Class-level counter

    def __init__(
        self,
        context: UIContext,
        on_model_change: Callable[[str], None],
        on_location_change: Callable[[str], None],
    ) -> None:
        super().__init__(
            context=context,
            direction=LayoutDirection.HORIZONTAL,
            spacing=6,
            margin=4,
            background=True,
        )

        CoralItem._coral_count += 1
        self.name = f"Coral {CoralItem._coral_count}"

        self.label = Label(
            context,
            text=self.name,
            width=100,
            align=TextAlign.LEFT,
            font_size=13,
        )

        self.model_dropdown = Dropdown(
            context,
            width=120,
            height=24,
            options=["PORAG", "XLB", "Accretive", "Polyp-Based", "Custom SDF"],
            on_select=on_model_change,
        )

        self.location_dropdown = Dropdown(
            context,
            width=100,
            height=24,
            options=["Front", "Center", "Left", "Right"],
            on_select=on_location_change,
        )

        self.add_control(self.label)
        self.add_control(self.model_dropdown)
        self.add_control(self.location_dropdown)


class CoralSection(List):
    """UI Section to add and change corals in the simulation."""

    def __init__(self, context: UIContext, engine: Engine) -> None:
        super().__init__(
            context=context,
            background=True,
            direction=LayoutDirection.VERTICAL,
            margin=0,
        )
        self.engine = engine

        # Title bar with ADD button
        self.add_control(
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
            )
        )

        # Container for dynamically added CoralItem controls
        self.coral_list = List(
            context=context,
            direction=LayoutDirection.VERTICAL,
            spacing=4,
            margin=4,
        )
        self.add_control(self.coral_list)

    def _on_add_coral(self) -> None:
        logger.debug("ADD CORAL")
        item = CoralItem(
            context=self.context,
            on_model_change=lambda name: logger.debug(f"{item.name} model: {name}"),
            on_location_change=lambda loc: logger.debug(f"{item.name} location: {loc}"),
        )
        self.coral_list.add_control(item)
