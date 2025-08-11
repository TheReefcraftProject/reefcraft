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
        """Initialize renderer and related objects for UI rendering.

        If the provided canvas is not a valid render target (e.g., during unit
        testing), fall back to a lightweight headless mode that stubs out the
        renderer/scene while preserving the public API used by controls.
        """
        self.canvas = canvas

        try:
            self.renderer = gfx.WgpuRenderer(canvas)
            self.scene = gfx.Scene()
            self.camera = gfx.OrthographicCamera(width=width, height=height)
            self.viewport = gfx.Viewport(self.renderer)
        except Exception:  # pragma: no cover - exercised in tests
            # Headless fallback
            class _SimpleScene:
                def __init__(self) -> None:
                    self.children: list[object] = []

                def add(self, obj: object) -> None:
                    self.children.append(obj)

            self.renderer = None  # type: ignore[assignment]
            self.scene = _SimpleScene()  # type: ignore[assignment]
            self.camera = None  # type: ignore[assignment]
            self.viewport = None  # type: ignore[assignment]

    def add(self, *objs: gfx.WorldObject) -> None:
        """Add one or more gfx objects to the UI scene (no-op if headless)."""
        for obj in objs:
            if hasattr(self.scene, "add"):
                self.scene.add(obj)  # type: ignore[attr-defined]

    def remove(self, *objs: gfx.WorldObject) -> None:
        """Remove one or more gfx objects from the UI scene (no-op if headless)."""
        for obj in objs:
            children = getattr(self.scene, "children", None)
            if isinstance(children, list) and obj in children:
                children.remove(obj)

    def draw(self) -> None:
        """Draw UI scene to viewport if a renderer exists."""
        if self.viewport is not None and self.renderer is not None and self.camera is not None:
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
