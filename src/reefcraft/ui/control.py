# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Base class for all UI elements with geometry and change notification."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygfx as gfx

from reefcraft.ui.theme import Theme

if TYPE_CHECKING:
    from collections.abc import Callable

    from reefcraft.ui.ui_context import UIContext


class Control:
    """Base class for all UI elements with position, size, theme, and parent access."""

    def __init__(
        self,
        context: UIContext,
        *,
        left: int = 0,
        top: int = 0,
        width: int = 100,
        height: int = 20,
        theme: Theme | None = None,
    ) -> None:
        """Initialize control with position, size, theme, and shared context."""
        self.context = context
        self._left = left
        self._top = top
        self._width = width
        self._height = height
        self.root = gfx.Group()
        self.context.add(self.root)
        self.theme = theme or Theme()
        self._on_change_callbacks: list[Callable[[], None]] = []

    @property
    def left(self) -> int:
        """Left edge in pixels from layout origin."""
        return self._left

    @left.setter
    def left(self, value: int) -> None:
        self._left = value
        self._trigger_change()

    @property
    def top(self) -> int:
        """Top edge in pixels from layout origin."""
        return self._top

    @top.setter
    def top(self, value: int) -> None:
        self._top = value
        self._trigger_change()

    @property
    def width(self) -> int:
        """Width in pixels."""
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        self._width = value
        self._trigger_change()

    @property
    def height(self) -> int:
        """Height in pixels."""
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        self._height = value
        self._trigger_change()

    def show(self) -> None:
        """Make the control visible."""
        self.root.visible = True
        self.context.draw()

    def hide(self) -> None:
        """Hide the control from view."""
        self.root.visible = False
        self.context.draw()

    def is_visible(self) -> bool:
        """Return whether the control is currently visible."""
        return self.root.visible

    def _trigger_change(self) -> None:
        """Call all registered change listeners and update visuals."""
        for callback in self._on_change_callbacks:
            callback()
        self._update_visuals()

    def _update_visuals(self) -> None:
        """Update visuals to reflect current position and size. To be overridden."""
        pass

    def on_change(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when control position or size changes."""
        self._on_change_callbacks.append(callback)
