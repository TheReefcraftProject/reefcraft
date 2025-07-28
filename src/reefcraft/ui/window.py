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
from reefcraft.sim.state import SimState
from reefcraft.ui.button import Button, ToggleButton
from reefcraft.ui.icon import Icon
from reefcraft.ui.icon_button import IconButton
from reefcraft.ui.label import Label, TextAlign
from reefcraft.ui.layout import Group, Layout, LayoutDirection
from reefcraft.ui.panel import Panel
from reefcraft.ui.reef import Reef
from reefcraft.ui.slider import Slider
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
                Group(
                    self.panel,
                    widgets=[
                        Label(self.panel, text="ENGINE", width=270, align=TextAlign.LEFT),
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
                                    pressed_tint=(120.0, 1.5),  # green play state
                                ),
                                Label(self.panel, text=lambda: f"{engine.get_time():.2f}", width=100, align=TextAlign.RIGHT),
                                Label(self.panel, text="seconds", width=50, align=TextAlign.RIGHT),
                            ],
                            direction=LayoutDirection.HORIZONTAL,
                            margin=5,
                        ),
                    ],
                    direction=LayoutDirection.VERTICAL,
                    margin=5,
                ),
            ],
            margin=10,
            spacing=10,
        )

    @property
    def is_open(self) -> bool:
        """Flag indicating the window is still open."""
        return not self.canvas.get_closed()

    def register_app_step(self, step: Callable) -> None:
        """Async schedule the update and draw cycles as a single 'step'."""
        self.renderer.request_draw(step)

    def draw(self, state: SimState) -> None:
        """Render one frame of the simulation and overlay UI."""
        # with self.stats:
        self.reef.draw(state)
        self.panel.draw(state)
        # self.stats.render()
        self.renderer.flush()
