# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Base class for a UI palette, managing scene and input capture."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygfx as gfx

if TYPE_CHECKING:
    from reefcraft.sim.state import SimState
    from reefcraft.ui.ui_context import UIContext


class Palette:
    """A left-docked UI palette with a dedicated scene and input handling."""

    def __init__(self, context: UIContext, width: int = 300, height: int = 1080) -> None:
        """Initialize the palette with its own scene and camera."""
        self.context = context
        self.width = width
        self.height = height

        self._init_background()

    def _init_background(self) -> None:
        """Add solid background mesh with pointer capture to block scene clicks."""
        geom = gfx.plane_geometry(width=self.width, height=self.height)
        mat = gfx.MeshBasicMaterial(color="#08080A", pick_write=True)
        mesh = gfx.Mesh(geom, mat)
        mesh.local.position = (-((self.context.width / 2) - (self.width / 2)), 0, -100)

        mesh.add_event_handler(self._on_mouse_down, "pointer_down")
        mesh.add_event_handler(self._on_mouse_up, "pointer_up")

        self.context.add(mesh)

    def _on_mouse_down(self, event: gfx.PointerEvent) -> None:
        """When clicked, capture mouse and block others."""
        event.target.set_pointer_capture(event.pointer_id, self.context.renderer)

    def _on_mouse_up(self, event: gfx.PointerEvent) -> None:
        """Release the mouse after click."""
        event.target.release_pointer_capture(event.pointer_id)

    def draw(self, state: SimState) -> None:
        """Render the palette contents."""
        self.context.draw()
