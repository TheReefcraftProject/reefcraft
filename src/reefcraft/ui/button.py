# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Button control implementation with optional icon support.

This module provides the Button and ToggleButton classes that create interactive
UI buttons for the Reefcraft application. The buttons support both text labels
and icons, with visual feedback for different states (normal, hover, pressed, disabled).

The Button class provides:
- Basic button functionality with click callbacks
- Optional icon support with customizable dimensions
- Visual state management (normal, hover, pressed, disabled)
- Mouse event handling and pointer capture
- Theme-based styling and colors

The ToggleButton class extends Button with:
- Toggle functionality between two states
- Dynamic label and icon switching
- State change callbacks
- Visual feedback for active/inactive states

Both button types integrate with the UI context and theme system to provide
consistent styling and behavior across the application.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto
from typing import TYPE_CHECKING

import imageio.v3 as iio
import numpy as np
import pygfx as gfx

from reefcraft.ui.control import Control
from reefcraft.ui.ui_context import UIContext
from reefcraft.utils.paths import icons_dir

if TYPE_CHECKING:
    from collections.abc import Callable

    from reefcraft.ui.ui_context import UIContext


class ButtonState(Enum):
    """Enumeration of possible button states.

    Defines the visual and behavioral states a button can be in,
    each with corresponding visual styling and interaction behavior.

    Attributes:
        NORMAL: Default button state, ready for interaction
        HOVER: Mouse is hovering over the button
        PRESSED: Button is currently being pressed
        DISABLED: Button is disabled and cannot be interacted with
    """

    NORMAL = auto()
    HOVER = auto()
    PRESSED = auto()
    DISABLED = auto()


class Button(Control):
    """Interactive UI button with optional icon support.

    The Button class provides a complete interactive button implementation
    with support for text labels, icons, and multiple visual states. It
    handles mouse events, provides visual feedback, and supports custom
    click callbacks.

    The button automatically manages:
    - Visual state changes based on mouse interaction
    - Icon and text positioning and sizing
    - Theme-based color schemes for different states
    - Mouse pointer capture during press operations

    Attributes:
        context: UI context for rendering and event handling
        label: Text displayed on the button
        enabled: Whether the button can be interacted with
        _on_click_callback: Function called when button is clicked
        icon_name: Optional icon filename to display
        icon_width: Custom width for the icon (uses button width if None)
        icon_height: Custom height for the icon (uses button height if None)
        state: Current visual state of the button
        _dragging: Whether the button is currently being dragged
    """

    def __init__(
        self,
        context: UIContext,
        *,
        left: int = 0,
        top: int = 0,
        width: int = 100,
        height: int = 20,
        label: str = "",
        icon: str | None = None,
        icon_width: int | None = None,
        icon_height: int | None = None,
        enabled: bool = True,
        on_click: Callable[[], None] | None = None,
    ) -> None:
        """Create a new button control.

        Initializes a button with the specified dimensions, label, and icon.
        Sets up event handlers for mouse interactions and creates the visual
        elements (background, text, icon) with appropriate materials.

        Args:
            context: UI context for rendering and event handling
            left: Left position of the button in screen coordinates
            top: Top position of the button in screen coordinates
            width: Width of the button in pixels
            height: Height of the button in pixels
            label: Text label to display on the button
            icon: Optional icon filename from the resources/icons directory
            icon_width: Custom width for the icon (uses button width if None)
            icon_height: Custom height for the icon (uses button height if None)
            enabled: Whether the button can be interacted with
            on_click: Optional callback function called when button is clicked
        """
        super().__init__(context=context, top=top, left=left, width=width, height=height)
        self.context: UIContext = context
        self.label: str = label
        self.enabled: bool = enabled
        self._on_click_callback: Callable[[], None] | None = on_click
        self.icon_name: str | None = icon
        self.icon_width: int | None = icon_width
        self.icon_height: int | None = icon_height

        # Set initial state based on enabled status
        self.state: ButtonState = ButtonState.NORMAL if enabled else ButtonState.DISABLED

        # Create materials for different button states
        self.mat_normal = gfx.MeshBasicMaterial(color=self.theme.color, pick_write=True)
        self.mat_disabled = gfx.MeshBasicMaterial(color=self.theme.disabled_color, pick_write=True)
        self.mat_hover = gfx.MeshBasicMaterial(color=self.theme.hover_color, pick_write=True)
        self.mat_pressed = gfx.MeshBasicMaterial(color=self.theme.highlight_color, pick_write=True)

        # Create visual elements
        self._bg_mesh = gfx.Mesh(gfx.plane_geometry(width=width, height=height), self.mat_normal)
        text_mat = gfx.TextMaterial(color=self.theme.text_color)
        self._text = gfx.Text(self.label, text_mat)

        # Load icon if specified
        self._icon_mesh: gfx.Mesh | None = self._load_icon(icon) if icon else None

        # Add elements to the scene
        self.root.add(self._bg_mesh)
        self.root.add(self._text)
        if self._icon_mesh:
            self.root.add(self._icon_mesh)

        # Initialize interaction state
        self._dragging = False

        # Set up event handlers
        _ = self._bg_mesh.add_event_handler(self._on_mouse_enter, "pointer_enter")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_leave, "pointer_leave")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_down, "pointer_down")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_up, "pointer_up")  # type: ignore

        # Initialize visual state
        self._update_visuals()

    def set_label(self, text: str) -> None:
        """Update the button label.

        Changes the text displayed on the button and updates the
        visual representation immediately.

        Args:
            text: New text to display on the button
        """
        self.label = text
        self._text.set_text(text)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the button.

        Changes the button's enabled state and updates the visual
        appearance accordingly. Disabled buttons cannot be interacted with.

        Args:
            enabled: Whether the button should be enabled
        """
        self.enabled = enabled
        self.state = ButtonState.NORMAL if enabled else ButtonState.DISABLED
        self._update_visuals()

    def on_click(self) -> None:
        """Called when the button is activated.

        Executes the click callback function if one was provided
        during initialization. This method is called automatically
        when the button is pressed and released.
        """
        if self._on_click_callback:
            self._on_click_callback()

    def _on_mouse_enter(self, _event: gfx.PointerEvent) -> None:
        """Handle mouse enter events.

        Changes the button state to hover when the mouse enters
        the button area, providing visual feedback to the user.

        Args:
            _event: Mouse enter event (unused)
        """
        if self.enabled and not self._dragging:
            self.state = ButtonState.HOVER
            self._update_visuals()

    def _on_mouse_leave(self, _event: gfx.PointerEvent) -> None:
        """Handle mouse leave events.

        Changes the button state back to normal when the mouse
        leaves the button area.

        Args:
            _event: Mouse leave event (unused)
        """
        if self.enabled and not self._dragging:
            self.state = ButtonState.NORMAL
            self._update_visuals()

    def _on_mouse_down(self, event: gfx.PointerEvent) -> None:
        """Handle mouse down events.

        Changes the button state to pressed and captures the
        mouse pointer to track the press operation.

        Args:
            event: Mouse down event containing pointer information
        """
        if not self.enabled:
            return
        self._dragging = True
        self.state = ButtonState.PRESSED
        event.target.set_pointer_capture(event.pointer_id, self.context.renderer)
        self._update_visuals()

    def _on_mouse_up(self, event: gfx.PointerEvent) -> None:
        """Handle mouse up events.

        Releases the mouse pointer capture and triggers the click
        action if the button was pressed. Changes state to hover
        if the mouse is still over the button.

        Args:
            event: Mouse up event containing pointer information
        """
        if not self.enabled:
            return
        if self._dragging:
            self._dragging = False
            event.target.release_pointer_capture(event.pointer_id)
            if self.state == ButtonState.PRESSED:
                self.on_click()
            self.state = ButtonState.HOVER
            self._update_visuals()

    def _update_visuals(self) -> None:
        """Update the button's visual appearance based on current state.

        Updates the background material, positions all visual elements,
        and ensures the button reflects its current state and dimensions.
        This method is called whenever the button state or properties change.
        """
        # Update background material based on state
        if self.state is ButtonState.DISABLED:
            self._bg_mesh.material = self.mat_disabled
        elif self.state is ButtonState.HOVER:
            self._bg_mesh.material = self.mat_hover
        elif self.state is ButtonState.PRESSED:
            self._bg_mesh.material = self.mat_pressed
        else:
            self._bg_mesh.material = self.mat_normal

        # Update background geometry and position
        self._bg_mesh.geometry = gfx.plane_geometry(width=self.width, height=self.height)
        self._bg_mesh.local.position = self.context.screen_to_world(self.left + self.width / 2, self.top + self.height / 2, 0)

        # Update text position (centered)
        self._text.local.position = self.context.screen_to_world(self.left + self.width / 2, self.top + self.height / 2, -2)

        # Update icon position and geometry (centered)
        if self._icon_mesh:
            iw = self.icon_width or self.width
            ih = self.icon_height or self.height
            self._icon_mesh.geometry = gfx.plane_geometry(iw, ih)
            self._icon_mesh.local.position = self.context.screen_to_world(
                self.left + (self.width - iw) / 2 + iw / 2,
                self.top + (self.height - ih) / 2 + ih / 2,
                -1,
            )

    def _load_icon(self, name: str) -> gfx.Mesh:
        """Load an icon image from the resources/icons directory and return a mesh.

        Loads the specified icon file, converts it to a texture, and creates
        a mesh with the appropriate material for display.

        Args:
            name: Filename of the icon in the resources/icons directory

        Returns:
            A mesh object displaying the loaded icon image

        Note:
            Icons are loaded as RGBA images and converted to normalized
            float values (0.0-1.0) for proper texture rendering.
        """
        path = icons_dir() / name
        img = iio.imread(path).astype(np.float32) / 255.0
        tex = gfx.Texture(img, dim=2)
        mat = gfx.MeshBasicMaterial(map=tex, depth_test=False)
        return gfx.Mesh(gfx.plane_geometry(1, 1), mat)


class ToggleButton(Button):
    """A button that toggles between two labeled/icon states, like Play/Pause.

    The ToggleButton extends the basic Button functionality to support
    two distinct states with different labels and icons. It automatically
    switches between states when clicked and provides callbacks for
    state changes.

    Common use cases include:
    - Play/Pause buttons
    - On/Off toggles
    - Show/Hide controls
    - Enable/Disable switches

    Attributes:
        _label_on: Label text for the "on" state
        _label_off: Label text for the "off" state
        _icon_on: Icon filename for the "on" state
        _icon_off: Icon filename for the "off" state
        _state: Current toggle state (True = on, False = off)
        _on_toggle: Callback function called when state changes
        _is_pressed: Visual indication of pressed state
    """

    def __init__(
        self,
        context: UIContext,
        label_on: str | None = None,
        label_off: str | None = None,
        *,
        icon_on: str | None = None,
        icon_off: str | None = None,
        icon_width: int | None = None,
        icon_height: int | None = None,
        initial: bool = False,
        on_toggle: Callable[[bool], None] | None = None,
        width: int = 100,
        height: int = 20,
    ) -> None:
        """Initialize a toggleable button with optional label/icon states.

        Creates a toggle button with two possible states, each with its
        own label and icon. The button starts in the specified initial
        state and switches between states when clicked.

        Args:
            context: UI context for rendering and event handling
            label_on: Label text for the "on" state
            label_off: Label text for the "off" state
            icon_on: Icon filename for the "on" state
            icon_off: Icon filename for the "off" state
            icon_width: Custom width for icons (uses button width if None)
            icon_height: Custom height for icons (uses button height if None)
            initial: Initial toggle state (True = on, False = off)
            on_toggle: Optional callback function called when state changes
            width: Width of the button in pixels
            height: Height of the button in pixels
        """
        self._label_on = label_on
        self._label_off = label_off
        self._icon_on = icon_on
        self._icon_off = icon_off
        self._state = initial
        self._on_toggle = on_toggle

        # Determine initial values based on starting state
        init_label = self._label_on if self._state else self._label_off
        init_icon = self._icon_on if self._state else self._icon_off

        # Initialize the base button with initial state
        super().__init__(
            context=context,
            label=init_label or "",
            icon=init_icon,
            icon_width=icon_width,
            icon_height=icon_height,
            width=width,
            height=height,
            on_click=self._handle_click,
        )

        # Update visual state to reflect initial toggle state
        self._update_visuals()

    def _handle_click(self) -> None:
        """Handle button toggle logic when clicked.

        Switches the button between on/off states, updates the label
        and icon accordingly, and calls the toggle callback if provided.
        The visual appearance is updated to reflect the new state.
        """
        # Toggle the state
        self._state = not self._state

        # Update label if labels are defined
        if self._label_on or self._label_off:
            new_label = self._label_on if self._state else self._label_off
            self.set_label(new_label or "")

        # Swap icon if icons are defined and different
        new_icon = self._icon_on if self._state else self._icon_off
        if new_icon and new_icon != self.icon_name:
            # Remove old icon and add new one
            if self._icon_mesh:
                self.root.remove(self._icon_mesh)
            self.icon_name = new_icon
            self._icon_mesh = self._load_icon(new_icon)
            self.root.add(self._icon_mesh)

        # Update visual appearance
        self._update_visuals()

        # Call toggle callback if provided
        if self._on_toggle:
            self._on_toggle(self._state)

    def _update_visuals(self) -> None:
        """Update the button's visual state based on toggle status.

        Calls the parent's visual update method and then applies
        additional styling specific to the toggle button's state.
        Active (on) state buttons use the pressed material color
        to provide visual feedback about their current state.
        """
        # Update basic visuals (text, icon, layout)
        super()._update_visuals()

        # Apply pressed material for active state
        if self._state and self.enabled:
            self._bg_mesh.material = self.mat_pressed

        # Track pressed state for visual consistency
        self._is_pressed = self._state
