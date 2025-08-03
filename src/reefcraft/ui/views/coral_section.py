# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""A section of UI controls for Coral management."""

import pygfx as gfx

from reefcraft.sim.engine import Engine
from reefcraft.ui.control import Control
from reefcraft.ui.icon_button import IconButton
from reefcraft.ui.label import Label, TextAlign
from reefcraft.ui.layout import Group, Layout, LayoutDirection
from reefcraft.utils.logger import logger


class CoralSection(Group):
    """UI Section to add and change corals in the simulation."""

    def __init__(self, scene: gfx.Scene, engine: Engine) -> None:
        """Create a new coral ui layout."""
        super().__init__(
            scene=scene,
            direction=LayoutDirection.VERTICAL,
            margin=0,
        )
        self.engine = engine
        self.controls = [
            Layout(
                scene,
                controls=[
                    Control(width=10),
                    Label(scene, text="CORALS", width=226, align=TextAlign.LEFT, font_color="#F3F6FA"),
                    IconButton(
                        scene,
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
            # Additional coral widgets can be dynamically inserted here
        ]

    def _on_add_coral(self) -> None:
        logger.debug("ADD CORAL")
        # Add logic to modify engine state and inject new coral widgets
