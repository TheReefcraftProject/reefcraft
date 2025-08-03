# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines a palette window to draw ui elements on."""

import pygfx as gfx

from reefcraft.sim.engine import Engine
from reefcraft.sim.state import SimState
from reefcraft.ui.control import Control
from reefcraft.ui.icon import Icon
from reefcraft.ui.layout import Layout, LayoutDirection
from reefcraft.ui.views.coral_section import CoralSection
from reefcraft.ui.views.engine_section import EngineSection


class Palette:
    """A left-docked panel: covers left 300px of canvas height."""

    def __init__(self, renderer: gfx.WgpuRenderer, engine: Engine, width: int = 300, height: int = 1080) -> None:
        """Initialize the panel and its correstponding 3D scene and ortho cameras."""
        self.renderer = renderer
        self.viewport = gfx.Viewport(renderer)

        geom = gfx.plane_geometry(width=width, height=height, width_segments=1, height_segments=1)
        mat = gfx.MeshBasicMaterial(color="#08080A")
        mesh = gfx.Mesh(geom, mat)
        mesh.local.position = (-((1920 / 2) - (300 / 2)), 0, -100)

        # Block the picking for the background of the palette
        if mesh.material is not None:
            mesh.material.pick_write = True
        mesh.add_event_handler(self._on_mouse_down, "pointer_down")
        mesh.add_event_handler(self._on_mouse_up, "pointer_up")

        self.scene = gfx.Scene()
        self.camera = gfx.OrthographicCamera(width=1920, height=1080)
        self.scene.add(mesh)

        _ = Layout(
            self.scene,
            controls=[
                Layout(
                    self.scene,
                    controls=[
                        Icon(
                            self.scene,
                            "logo.png",
                            width=64,
                            height=64,
                        ),
                    ],
                    direction=LayoutDirection.HORIZONTAL,
                ),
                Control(height=5),
                EngineSection(self.scene, engine),
                Control(height=5),
                CoralSection(self.scene, engine),
            ],
            margin=15,
        )

    def _on_mouse_down(self, event: gfx.PointerEvent) -> None:
        """When the mouse is clicked in background of the panel, capture the mouse and block others."""
        event.target.set_pointer_capture(event.pointer_id, self.renderer)

    def _on_mouse_up(self, event: gfx.PointerEvent) -> None:
        """Release the mouse on mouse up."""
        event.target.release_pointer_capture(event.pointer_id)

    def draw(self, state: SimState) -> None:
        """Draw a solid rectangle on the left side of the UI scene."""
        self.viewport.render(self.scene, self.camera)  # , flush=False)
