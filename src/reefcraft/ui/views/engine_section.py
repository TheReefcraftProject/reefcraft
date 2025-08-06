# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""A section of UI controls for Engine management."""

import pygfx as gfx

from reefcraft.sim.engine import Engine
from reefcraft.ui.control import Control
from reefcraft.ui.icon_button import IconButton
from reefcraft.ui.label import Label, TextAlign
from reefcraft.ui.layout import Group, Layout, LayoutDirection
from reefcraft.ui.ui_context import UIContext
from reefcraft.utils.logger import logger


class EngineSection(Group):
    """UI Section to add and change corals in the simulation."""

    def __init__(self, context: UIContext, engine: Engine) -> None:
        """Create a new coral ui layout."""
        super().__init__(
            context=context,
            direction=LayoutDirection.VERTICAL,
            margin=0,
        )
        self.engine = engine
        self.controls = [
            Layout(
                context,
                controls=[
                    Control(context, width=10),
                    Label(context, text="SIMULATION", width=250, align=TextAlign.LEFT, font_color="#F3F6FA"),
                ],
                direction=LayoutDirection.HORIZONTAL,
                margin=5,
            ),
            Layout(
                self.context,
                controls=[
                    Control(context, width=24),
                    IconButton(
                        context,
                        "play.png",
                        width=24,
                        height=24,
                        toggle=True,
                        on_toggle=lambda playing: engine.play() if playing else engine.pause(),
                        normal_tint=(0.0, 0.5),
                        hover_tint=(0.0, 1.0),
                        pressed_tint=(194.0, 1.5),  # theme.highlight_color play state
                    ),
                    Label(
                        context,
                        text=lambda: (f"{engine.get_time():6.2f}s  {engine.step_rate_hz:5.1f} Hz   {engine.sim_speed_ratio:4.2f}×"),
                        width=200,
                        align=TextAlign.RIGHT,
                    ),
                ],
                direction=LayoutDirection.HORIZONTAL,
            ),
            Control(context, height=5),
        ]

    def _on_add_coral(self) -> None:
        logger.debug("ADD CORAL")
        # Add logic to modify engine state and inject new coral controls
