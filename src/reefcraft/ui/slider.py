# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Slider control for interactive value adjustment.

This module provides the Slider class that creates an interactive
slider control for the Reefcraft UI. The slider allows users to
adjust numerical values within a specified range through mouse
interaction.

The Slider provides:
- Interactive value adjustment with mouse drag
- Visual feedback showing current value and range
- Configurable minimum and maximum values
- Change callback system for value updates
- Theme integration for consistent styling
- Real-time visual updates during interaction

The slider automatically handles:
- Mouse event capture and release
- Value calculation from screen position
- Visual representation updates
- Change notification callbacks
"""

from collections.abc import Callable

import pygfx as gfx

from reefcraft.ui.control import Control
from reefcraft.ui.ui_context import UIContext


class Slider(Control):
    """Interactive slider control for numerical value adjustment.

    The Slider class creates a horizontal slider that allows users
    to adjust values within a specified range. The slider provides
    visual feedback showing the current value and filled portion,
    and supports mouse interaction for value adjustment.

    Key features:
    - Horizontal slider with configurable range
    - Visual feedback showing current value and progress
    - Mouse drag interaction for value adjustment
    - Real-time value updates and callbacks
    - Theme integration for consistent styling
    - Text overlay displaying current value

    The slider automatically manages:
    - Mouse event handling and pointer capture
    - Value calculation from screen coordinates
    - Visual updates for background, foreground, and text
    - Change callback execution

    Attributes:
        min: Minimum allowed value for the slider
        max: Maximum allowed value for the slider
        value: Current value of the slider
        _on_change_callback: Function called when value changes
        _dragging: Whether the slider is currently being dragged
        _bg_mesh: Background mesh showing the slider track
        _fg_mesh: Foreground mesh showing the filled portion
        _text: Text overlay displaying the current value
    """

    def __init__(
        self,
        context: UIContext,
        *,
        left: int = 0,
        top: int = 0,
        width: int = 100,
        height: int = 20,
        min_value: float = 0.0,
        max_value: float = 1.0,
        value: float | None = None,
        on_change: Callable[[float], None] | None = None,
    ) -> None:
        """Create a new slider control.

        Initializes a slider with the specified dimensions, value range,
        and initial value. The slider is ready for interaction immediately
        after creation.

        Args:
            context: UI context for rendering and event handling
            left: Left position in pixels from layout origin
            top: Top position in pixels from layout origin
            width: Width of the slider in pixels
            height: Height of the slider in pixels
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            value: Initial value (uses min_value if None)
            on_change: Optional callback function for value changes
        """
        super().__init__(context=context, top=top, left=left, width=width, height=height)
        self.context = context
        self.min = min_value
        self.max = max_value
        self.value = value if value is not None else min_value
        self._on_change_callback = on_change

        self._dragging = False

        # Create background mesh for the slider track
        self._bg_mesh = gfx.Mesh(
            gfx.plane_geometry(width=width, height=height),
            gfx.MeshBasicMaterial(color=self.theme.color),
        )
        if self._bg_mesh.material is not None:
            self._bg_mesh.material.pick_write = True

        # Create foreground mesh showing the filled portion
        self._fg_mesh = gfx.Mesh(
            gfx.plane_geometry(width=1, height=height),
            gfx.MeshBasicMaterial(color=self.theme.highlight_color),
        )

        # Create text overlay for displaying the current value
        text_mat = gfx.TextMaterial(color=self.theme.text_color)
        self._text = gfx.Text(str(self.value), text_mat)

        # Add all meshes to the context
        self.context.add(self._bg_mesh)
        self.context.add(self._fg_mesh)
        self.context.add(self._text)

        # Set up mouse event handlers
        self._bg_mesh.add_event_handler(self._on_mouse_down, "pointer_down")
        self._bg_mesh.add_event_handler(self._on_mouse_move, "pointer_move")
        self._bg_mesh.add_event_handler(self._on_mouse_up, "pointer_up")

        # Initialize visual state
        self._update_visuals()

    def set_value(self, value: float) -> None:
        """Set the slider value and trigger change callback.

        Updates the slider's value and calls the change callback
        if one is provided. The visual representation is automatically
        updated to reflect the new value.

        Args:
            value: New value for the slider
        """
        if value != self.value:
            self.value = value
            if self._on_change_callback:
                self._on_change_callback(self.value)
            self._update_visuals()

    @property
    def _percent(self) -> float:
        """Calculate the percentage of the slider that should be filled.

        Returns:
            Value between 0.0 and 1.0 representing the fill percentage
        """
        return (self.value - self.min) / (self.max - self.min)

    def _set_from_screen_x(self, x: float) -> None:
        """Set the slider value based on screen x-coordinate.

        Converts the screen x-coordinate to a value within the
        slider's range and updates the slider accordingly.

        Args:
            x: Screen x-coordinate in pixels
        """
        # Calculate normalized position (0.0 to 1.0)
        t = (x - self.left) / self.width
        t = max(0.0, min(1.0, t))

        # Convert to slider value
        self.set_value(self.min + t * (self.max - self.min))

    def _update_visuals(self) -> None:
        """Update the visual representation of the slider.

        Updates the background, foreground, and text elements
        to reflect the current slider state and value.
        """
        # Calculate fill percentage
        filled = max(0.0, min(1.0, self._percent))

        # Update background mesh
        self._bg_mesh.geometry = gfx.plane_geometry(width=self.width, height=self.height)
        self._bg_mesh.local.position = self.context.screen_to_world(self.left + self.width / 2, self.top + self.height / 2, -1)

        # Update foreground mesh (filled portion)
        self._fg_mesh.geometry = gfx.plane_geometry(width=int(self.width * filled), height=self.height)
        self._fg_mesh.local.position = self.context.screen_to_world(self.left + (self.width * filled) / 2, self.top + self.height / 2, 0)

        # Update text overlay
        self._text.set_text(f"{self.value:.2f}")
        self._text.local.position = self.context.screen_to_world(self.left + self.width / 2, self.top + self.height / 2, -2)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_mouse_down(self, event: gfx.PointerEvent) -> None:
        """Handle mouse down event for slider interaction.

        Captures the mouse pointer and initiates slider dragging.
        The slider value is immediately updated to the position
        under the mouse cursor.

        Args:
            event: PyGFX pointer event containing mouse information
        """
        self._dragging = True
        event.target.set_pointer_capture(event.pointer_id, self.context.renderer)
        self._set_from_screen_x(event.x)

    def _on_mouse_move(self, event: gfx.PointerEvent) -> None:
        """Handle mouse move event during slider dragging.

        Updates the slider value as the mouse moves while dragging.
        This provides real-time feedback during interaction.

        Args:
            event: PyGFX pointer event containing mouse information
        """
        if self._dragging:
            self._set_from_screen_x(event.x)

    def _on_mouse_up(self, event: gfx.PointerEvent) -> None:
        """Handle mouse up event to end slider interaction.

        Releases the mouse pointer capture and finalizes the
        slider value at the current mouse position.

        Args:
            event: PyGFX pointer event containing mouse information
        """
        if self._dragging:
            self._dragging = False
            event.target.release_pointer_capture(event.pointer_id)
            self._set_from_screen_x(event.x)
