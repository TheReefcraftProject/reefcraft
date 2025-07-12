"""Wrapper around :class:`RenderContext` managing draw callbacks."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from reefcraft.render.context import RenderContext
    from reefcraft.render.scene import Scene


class Canvas:
    """Onscreen canvas that delegates rendering to :class:`RenderContext`."""

    def __init__(self, context: RenderContext, scene: Scene) -> None:
        """Create a new onscreen canvas."""
        self.context = context
        self.scene = scene
        self.context.set_scene(scene)

    def draw(self) -> None:
        """Render the scene."""
        self.context.render()
