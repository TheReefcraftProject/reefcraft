# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Holds global context for UI rendering (renderer, scene, camera, etc)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygfx as gfx

if TYPE_CHECKING:
    from rendercanvas.auto import RenderCanvas


class UIContext:
    """Global rendering context shared by all UI controls."""

    def __init__(self, canvas: RenderCanvas, width: int = 1920, height: int = 1080) -> None:
        """Initialize renderer and related objects for UI rendering."""
        self.canvas = canvas
        self.renderer = gfx.WgpuRenderer(canvas)
        self.scene = gfx.Scene()
        self.camera = gfx.OrthographicCamera(width=width, height=height)
        self.viewport = gfx.Viewport(self.renderer)

    def add(self, *objs: gfx.WorldObject) -> None:
        """Add one or more gfx objects to the UI scene."""
        for obj in objs:
            self.scene.add(obj)

    def remove(self, *objs: gfx.WorldObject) -> None:
        """Remove one or more gfx objects from the UI scene."""
        for obj in objs:
            if obj in self.scene.children:
                self.scene.children.remove(obj)

    def draw(self) -> None:
        """Draw UI scene to viewport."""
        self.viewport.render(self.scene, self.camera)

    @property
    def width(self) -> int:
        """Logical width of the canvas in pixels."""
        return self.canvas.get_logical_size()[0]

    @property
    def height(self) -> int:
        """Logical height of the canvas in pixels."""
        return self.canvas.get_logical_size()[1]

    def screen_to_world(self, x: float, y: float, z: float = 0.0) -> tuple[float, float, float]:
        """Convert screen-space (pixel) coordinates to world coordinates using ortho projection."""
        # Center-based world space conversion
        world_x = x - self.width / 2
        world_y = self.height / 2 - y
        world_z = z
        return (world_x, world_y, world_z)
