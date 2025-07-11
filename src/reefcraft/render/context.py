"""Onscreen rendering context using pygfx."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygfx as gfx
from wgpu.gui.auto import WgpuCanvas

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from .scene import Scene


class RenderContext:
    """Manage an onscreen pygfx renderer."""

    def __init__(self, size: tuple[int, int] = (1024, 768)) -> None:
        """Create the rendering context."""
        self.size = size
        self.canvas = WgpuCanvas(size=size, title="Reefcraft")
        self.renderer = gfx.renderers.WgpuRenderer(self.canvas, pixel_ratio=1)
        self.camera = gfx.PerspectiveCamera(70, 16 / 9)
        self.camera.local.z = 400
        self.scene: gfx.Scene | None = None

    def set_scene(self, scene: Scene) -> None:
        """Attach a scene to render."""
        self.scene = scene

    def resize(self, width: int, height: int) -> None:
        """Resize internal buffers."""
        if (width, height) != self.size:
            self.size = (width, height)
            self.canvas.set_logical_size(width, height)
            self.camera.aspect = width / height

    def render(self) -> None:
        """Render the current scene."""
        if self.scene is None:
            return
        self.scene.update()
        self.renderer.render(self.scene.scene, self.camera)
