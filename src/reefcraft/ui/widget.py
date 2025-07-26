# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines an widget parent class for all UI elements."""

from collections.abc import Callable

from reefcraft.ui.theme import Theme


class Widget:
    """Base class for all UI elements with geometry and change notification."""

    def __init__(
        self,
        left: int = 0,
        top: int = 0,
        width: int = 100,
        height: int = 20,
        theme: Theme | None = None,
    ) -> None:
        """Initialize a widget with position, size, and optional theme."""
        self._top = top
        self._left = left
        self._width = width
        self._height = height
        self.theme = theme or Theme()
        self._on_change_callbacks: list[Callable[[], None]] = []

    @property
    def top(self) -> int:
        """Top y-coordinate of the widget."""
        return self._top

    @top.setter
    def top(self, value: int) -> None:
        if value != self._top:
            self._top = value
            self._emit_change()

    @property
    def left(self) -> int:
        """Left x-coordinate of the widget."""
        return self._left

    @left.setter
    def left(self, value: int) -> None:
        if value != self._left:
            self._left = value
            self._emit_change()

    @property
    def width(self) -> int:
        """Width of the widget."""
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        if value != self._width:
            self._width = value
            self._emit_change()

    @property
    def height(self) -> int:
        """Height of the widget."""
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        if value != self._height:
            self._height = value
            self._emit_change()

    def on_change(self, callback: Callable[[], None]) -> None:
        """Register a callback triggered when widget geometry changes."""
        self._on_change_callbacks.append(callback)

    def _emit_change(self) -> None:
        """Invoke all registered change callbacks and update visuals."""
        self._update_visuals()
        for callback in self._on_change_callbacks:
            callback()

    def _update_visuals(self) -> None:
        """Update visuals when geometry or state changes. To be overridden by subclasses."""
        pass
