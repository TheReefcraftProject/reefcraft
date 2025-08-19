# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Base class for all UI elements with geometry and change notification.

This module provides the Control class, which serves as the foundation for
all user interface elements in the Reefcraft application. The Control class
provides common functionality for positioning, sizing, theming, and change
notification that all UI components inherit.

The Control class provides:
- Position and size management with change notification
- Theme integration for consistent styling
- Visibility control (show/hide)
- Change callback registration for layout updates
- Integration with the UI context and rendering system

All UI components (buttons, labels, lists, etc.) inherit from this base
class to ensure consistent behavior and common functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygfx as gfx

from reefcraft.ui.theme import Theme

if TYPE_CHECKING:
    from collections.abc import Callable

    from reefcraft.ui.ui_context import UIContext


class Control:
    """Base class for all UI elements with position, size, theme, and parent access.

    The Control class provides the fundamental building block for all UI
    components in the Reefcraft application. It manages positioning, sizing,
    theming, and change notification that child classes can extend and customize.

    Key features:
    - Position and size properties with automatic change notification
    - Theme integration for consistent visual styling
    - Visibility control for showing/hiding controls
    - Change callback system for layout updates
    - Integration with the pygfx rendering system

    Child classes should override `_update_visuals()` to implement
    their specific visual representation and respond to property changes.

    Attributes:
        context: UI context for rendering and event handling
        _left: Internal left position in pixels
        _top: Internal top position in pixels
        _width: Internal width in pixels
        _height: Internal height in pixels
        root: pygfx Group containing all visual elements
        theme: Theme object for styling and colors
        _on_change_callbacks: List of callbacks for change notifications
    """

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
        """Initialize control with position, size, theme, and shared context.

        Creates a new control with the specified dimensions and position.
        Sets up the pygfx root group, applies the theme, and registers
        the control with the UI context for rendering.

        Args:
            context: UI context for rendering and event handling
            left: Left position in pixels from layout origin
            top: Top position in pixels from layout origin
            width: Width of the control in pixels
            height: Height of the control in pixels
            theme: Optional theme object (uses default if None)
        """
        self.context = context
        self._left = left
        self._top = top
        self._width = width
        self._height = height

        # Create root group for all visual elements
        self.root = gfx.Group()
        self.context.add(self.root)

        # Apply theme (use default if none provided)
        self.theme = theme or Theme()

        # Initialize change notification system
        self._on_change_callbacks: list[Callable[[], None]] = []

    @property
    def left(self) -> int:
        """Left edge in pixels from layout origin.

        Returns:
            The left position of the control in pixels
        """
        return self._left

    @left.setter
    def left(self, value: int) -> None:
        """Set the left position and trigger change notification.

        Args:
            value: New left position in pixels
        """
        self._left = value
        self._trigger_change()

    @property
    def top(self) -> int:
        """Top edge in pixels from layout origin.

        Returns:
            The top position of the control in pixels
        """
        return self._top

    @top.setter
    def top(self, value: int) -> None:
        """Set the top position and trigger change notification.

        Args:
            value: New top position in pixels
        """
        self._top = value
        self._trigger_change()

    @property
    def width(self) -> int:
        """Width in pixels.

        Returns:
            The width of the control in pixels
        """
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        """Set the width and trigger change notification.

        Args:
            value: New width in pixels
        """
        self._width = value
        self._trigger_change()

    @property
    def height(self) -> int:
        """Height in pixels.

        Returns:
            The height of the control in pixels
        """
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        """Set the height and trigger change notification.

        Args:
            value: New height in pixels
        """
        self._height = value
        self._trigger_change()

    def show(self) -> None:
        """Make the control visible.

        Sets the control's visibility to True and triggers a redraw
        of the UI context to reflect the change immediately.
        """
        self.root.visible = True
        self.context.draw()

    def hide(self) -> None:
        """Hide the control from view.

        Sets the control's visibility to False and triggers a redraw
        of the UI context to reflect the change immediately.
        """
        self.root.visible = False
        self.context.draw()

    def is_visible(self) -> bool:
        """Return whether the control is currently visible.

        Returns:
            True if the control is visible, False otherwise
        """
        return self.root.visible

    def _trigger_change(self) -> None:
        """Call all registered change listeners and update visuals.

        This method is called automatically whenever a position or size
        property changes. It notifies all registered change callbacks
        and then calls `_update_visuals()` to refresh the visual representation.
        """
        # Notify all registered change listeners
        for callback in self._on_change_callbacks:
            callback()

        # Update visual representation
        self._update_visuals()

    def _update_visuals(self) -> None:
        """Update visuals to reflect current position and size.

        This method should be overridden by child classes to implement
        their specific visual update logic. The base implementation
        does nothing, allowing child classes to define their own behavior.

        Called automatically whenever position or size properties change.
        """
        pass

    def on_change(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when control position or size changes.

        Registers a function that will be called automatically whenever
        the control's position or size properties are modified. This is
        useful for implementing layout systems that need to respond to
        control changes.

        Args:
            callback: Function to call when changes occur
        """
        self._on_change_callbacks.append(callback)
