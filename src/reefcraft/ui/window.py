# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Primary window for the application and views."""

from collections.abc import Callable
from pathlib import Path

import pygfx as gfx
from rendercanvas.auto import RenderCanvas

from reefcraft.sim.engine import Engine
from reefcraft.ui.icon import Icon
from reefcraft.ui.icon_button import IconButton
from reefcraft.ui.label import Label, TextAlign
from reefcraft.ui.layout import Group, Layout, LayoutDirection
from reefcraft.ui.panel import Panel
from reefcraft.ui.reef import Reef
from reefcraft.ui.widget import Widget
from reefcraft.utils.logger import logger
from reefcraft.utils.window_style import apply_dark_titlebar_and_icon


class Window:
    """The window is both an OS level window as well as a render canvas and renderer."""

    def __init__(self, engine: Engine, app_root: Path) -> None:
        """Initialize the window and view state."""
        self.engine = engine
        self.canvas = RenderCanvas(size=(1920, 1080), title="Reefcraft", update_mode="continuous", max_fps=60)  # type: ignore

        # Make the window beautiful with dark mode titel bar and an icon
        icon_path = (app_root / "resources" / "icons" / "logo.ico").resolve()
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        # Prepare our pygfx renderer
        self.renderer = gfx.WgpuRenderer(self.canvas)
        self.stats = gfx.Stats(viewport=self.renderer)

        # Create the view of the reef and the ui panel
        self.reef = Reef(self.renderer)
        self.panel = Panel(self.renderer)

        _ = Layout(
            self.panel,
            widgets=[
                Layout(
                    self.panel,
                    widgets=[
                        Icon(
                            self.panel,
                            "logo.png",
                            width=48,
                            height=48,
                        ),
                    ],
                    direction=LayoutDirection.HORIZONTAL,
                ),
                Widget(height=5),
                Group(
                    self.panel,
                    widgets=[
                        Layout(
                            self.panel,
                            widgets=[
                                Widget(width=10),
                                Label(self.panel, text="SIMULATION", width=250, align=TextAlign.LEFT, font_color="#F3F6FA"),
                            ],
                            direction=LayoutDirection.HORIZONTAL,
                            margin=5,
                        ),
                        Layout(
                            self.panel,
                            widgets=[
                                Widget(width=20),
                                IconButton(
                                    self.panel,
                                    "play.png",
                                    width=20,
                                    height=20,
                                    toggle=True,
                                    on_toggle=lambda playing: engine.play() if playing else engine.pause(),
                                    normal_tint=(0.0, 0.5),
                                    hover_tint=(0.0, 1.0),
                                    pressed_tint=(194.0, 1.5),  # theme.highlight_color play state
                                ),
                                Label(
                                    self.panel,
                                    text=lambda: (f"{engine.get_time():6.2f}s  {engine.step_rate_hz:5.1f} Hz   {engine.sim_speed_ratio:4.2f}×"),
                                    width=200,
                                    align=TextAlign.RIGHT,
                                ),
                            ],
                            direction=LayoutDirection.HORIZONTAL,
                        ),
                        Widget(height=5),
                    ],
                    direction=LayoutDirection.VERTICAL,
                ),
                Widget(height=5),
                Group(
                    self.panel,
                    widgets=[
                        Layout(
                            self.panel,
                            widgets=[
                                Widget(width=10),
                                Label(self.panel, text="CORALS", width=230, align=TextAlign.LEFT, font_color="#F3F6FA"),
                            ],
                            direction=LayoutDirection.HORIZONTAL,
                            margin=5,
                        ),
                        IconButton(
                            self.panel,
                            "add.png",
                            width=20,
                            height=20,
                            toggle=False,
                            on_click=lambda: logger.debug("ADD CORAL"),
                            normal_tint=(0.0, 0.5),
                            hover_tint=(0.0, 1.0),
                            pressed_tint=(0.0, 1.5),  # theme.highlight_color play state
                        ),
                    ],
                    direction=LayoutDirection.HORIZONTAL,
                ),
            ],
            margin=15,
        )

        self.renderer.request_draw(self.draw)

    @property
    def is_open(self) -> bool:
        """Flag indicating the window is still open."""
        return not self.canvas.get_closed()

    def draw(self) -> None:
        """Render one frame of the simulation and overlay UI."""
        # with self.stats:
        self.reef.draw(self.engine.state)
        self.panel.draw(self.engine.state)
        # self.stats.render()
        self.renderer.flush()
