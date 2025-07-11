"""Offscreen rendering context using pygfx."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pygfx as gfx
from pygfx.renderers.wgpu import enable_wgpu_features
from wgpu.gui.offscreen import WgpuCanvas

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from .scene import Scene


class RenderContext:
    """Manage an offscreen pygfx renderer."""

    def __init__(self, size: tuple[int, int] = (1024, 768)) -> None:
        """Create the rendering context."""
        self.size = size
        self.canvas = WgpuCanvas(size=size)
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

    def render(self) -> np.ndarray:
        """Render the current scene and return an RGBA image array."""
        if self.scene is None:
            return np.zeros((self.size[1], self.size[0], 4), dtype=np.float32)
        self.scene.update()
        self.renderer.render(self.scene.scene, self.camera)
        image = self.renderer.snapshot()
        return image.astype(np.float32) / 255.0
