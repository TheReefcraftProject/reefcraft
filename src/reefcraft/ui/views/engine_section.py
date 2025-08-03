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
from reefcraft.utils.logger import logger


class EngineSection(Group):
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
                    Label(scene, text="SIMULATION", width=250, align=TextAlign.LEFT, font_color="#F3F6FA"),
                ],
                direction=LayoutDirection.HORIZONTAL,
                margin=5,
            ),
            Layout(
                self.scene,
                controls=[
                    Control(width=24),
                    IconButton(
                        scene,
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
                        scene,
                        text=lambda: (f"{engine.get_time():6.2f}s  {engine.step_rate_hz:5.1f} Hz   {engine.sim_speed_ratio:4.2f}×"),
                        width=200,
                        align=TextAlign.RIGHT,
                    ),
                ],
                direction=LayoutDirection.HORIZONTAL,
            ),
            Control(height=5),
        ]

    def _on_add_coral(self) -> None:
        logger.debug("ADD CORAL")
        # Add logic to modify engine state and inject new coral widgets
