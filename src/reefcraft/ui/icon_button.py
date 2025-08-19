# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Icon button control with visual feedback and toggle support.

This module provides the IconButton class that creates interactive
icon-based buttons for the Reefcraft UI. The buttons support both
click and toggle modes with visual feedback through texture tinting.

The IconButton provides:
- Icon-based button display with customizable tinting
- Visual feedback for hover, pressed, and disabled states
- Toggle mode support with state callbacks
- Efficient texture tinting using NumPy operations
- Theme integration and consistent styling
- Mouse event handling and pointer capture

Icon buttons are commonly used for:
- Toolbar controls and actions
- Status toggles and switches
- Navigation elements
- Compact UI controls where space is limited
"""

from collections.abc import Callable

import imageio.v3 as iio
import numpy as np
import pygfx as gfx

from reefcraft.ui.control import Control
from reefcraft.ui.theme import Theme
from reefcraft.ui.ui_context import UIContext
from reefcraft.utils.paths import icons_dir


class IconButton(Control):
    """An icon-only button that visually responds by tinting its texture.

    The IconButton class provides an interactive button control that
    displays an icon with visual feedback through texture tinting.
    It supports both click and toggle modes with appropriate callbacks.

    Key features:
    - Icon-based visual representation
    - Multiple visual states (normal, hover, pressed, disabled)
    - Toggle mode with state tracking
    - Efficient texture tinting for visual feedback
    - Mouse event handling and pointer capture
    - Theme integration for consistent styling

    The button uses a transparent background mesh for interaction
    detection while displaying the tinted icon sprite on top.
    Visual feedback is provided through different tinting applied
    to the same base icon texture.

    Attributes:
        context: UI context for rendering and event handling
        icon_name: Filename of the icon in resources/icons directory
        enabled: Whether the button can be interacted with
        toggle: Whether the button operates in toggle mode
        _state: Current toggle state (True = on, False = off)
        _hovering: Whether the mouse is hovering over the button
        _dragging: Whether the button is currently being dragged
        _on_click_callback: Function called when button is clicked
        _on_toggle_callback: Function called when toggle state changes
        icon_scale: Scale factor for the icon display
        _sprite: Icon sprite mesh with tinted textures
        _bg_mesh: Transparent background mesh for interaction
    """

    def __init__(
        self,
        context: UIContext,
        icon: str,
        *,
        left: int = 0,
        top: int = 0,
        width: int = 32,
        height: int = 32,
        enabled: bool = True,
        toggle: bool = False,
        initial: bool = False,
        on_click: Callable[[], None] | None = None,
        on_toggle: Callable[[bool], None] | None = None,
        icon_scale: float = 1.0,
        normal_tint: tuple[float, float] = (0.0, 0.5),  # hue shift, brightness
        hover_tint: tuple[float, float] = (0.0, 0.9),
        pressed_tint: tuple[float, float] = (0.0, 1.3),
        theme: Theme | None = None,
    ) -> None:
        """Create an icon button.

        Initializes an icon button with the specified icon and behavior.
        Creates tinted versions of the icon for different visual states
        and sets up event handling for mouse interactions.

        Args:
            context: UI context for rendering and event handling
            icon: Filename of the icon in the resources/icons directory
            left: Left position in pixels from layout origin
            top: Top position in pixels from layout origin
            width: Width of the button in pixels
            height: Height of the button in pixels
            enabled: Whether the button can be interacted with
            toggle: Whether the button operates in toggle mode
            initial: Initial toggle state (only used if toggle=True)
            on_click: Optional callback function called when button is clicked
            on_toggle: Optional callback function called when toggle state changes
            icon_scale: Scale factor for the icon display (1.0 = full size)
            normal_tint: (hue_shift, brightness) for normal state
            hover_tint: (hue_shift, brightness) for hover state
            pressed_tint: (hue_shift, brightness) for pressed state
            theme: Optional theme object (uses default if None)
        """
        super().__init__(context=context, top=top, left=left, width=width, height=height)

        self.context = context
        self.icon_name = icon
        self.enabled = enabled
        self.toggle = toggle
        self._state = initial
        self._hovering = False
        self._dragging = False
        self._on_click_callback = on_click
        self._on_toggle_callback = on_toggle

        # Load and prepare tinted textures for different states
        img = iio.imread(icons_dir() / icon)
        self._img_normal = gfx.MeshBasicMaterial(map=gfx.Texture(tint_image(img, *normal_tint), dim=2), depth_test=False, pick_write=False)
        self._img_hover = gfx.MeshBasicMaterial(map=gfx.Texture(tint_image(img, *hover_tint), dim=2), depth_test=False, pick_write=False)
        self._img_pressed = gfx.MeshBasicMaterial(map=gfx.Texture(tint_image(img, *pressed_tint), dim=2), depth_test=False, pick_write=False)

        # Create icon sprite and geometry
        self._geometry = gfx.plane_geometry(int(width * icon_scale), int(height * icon_scale))
        self._sprite = gfx.Mesh(self._geometry, self._img_normal)

        # Create transparent pickable background for interaction
        self._bg_material = gfx.MeshBasicMaterial(color=self.theme.group_color, pick_write=True)
        self._bg_mesh = gfx.Mesh(self._geometry, self._bg_material)

        # Add visual elements to the scene
        self.context.add(self._sprite)
        self.context.add(self._bg_mesh)

        # Register event handlers on the background mesh
        _ = self._bg_mesh.add_event_handler(self._on_mouse_enter, "pointer_enter")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_leave, "pointer_leave")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_down, "pointer_down")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_up, "pointer_up")  # type: ignore

        # Initialize visual state
        self._update_visuals()

    def _on_mouse_enter(self, _event: gfx.PointerEvent) -> None:
        """Handle mouse enter events.

        Changes the button state to hovering when the mouse enters
        the button area, providing visual feedback to the user.

        Args:
            _event: Mouse enter event (unused)
        """
        if self.enabled:
            self._hovering = True
            self._update_visuals()

    def _on_mouse_leave(self, _event: gfx.PointerEvent) -> None:
        """Handle mouse leave events.

        Changes the button state back to normal when the mouse
        leaves the button area.

        Args:
            _event: Mouse leave event (unused)
        """
        if self.enabled:
            self._hovering = False
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
        event.target.set_pointer_capture(event.pointer_id, self.context.renderer)
        self._update_visuals()

    def _on_mouse_up(self, event: gfx.PointerEvent) -> None:
        """Handle mouse up events.

        Releases the mouse pointer capture and triggers the appropriate
        action (click or toggle) based on the button configuration.

        Args:
            event: Mouse up event containing pointer information
        """
        if not self.enabled:
            return
        if self._dragging:
            self._dragging = False
            event.target.release_pointer_capture(event.pointer_id)

            # Handle toggle mode state change
            if self.toggle:
                self._state = not self._state
                if self._on_toggle_callback:
                    self._on_toggle_callback(self._state)

            # Execute click callback
            if self._on_click_callback:
                self._on_click_callback()

            # Update visual appearance
            self._update_visuals()

    def _update_visuals(self) -> None:
        """Apply the correct icon texture tint based on current state.

        Updates the icon sprite material based on the button's current
        state (enabled, hovering, pressed, toggle state) and positions
        both the sprite and background mesh correctly.
        """
        # Select appropriate material based on current state
        if not self.enabled:
            mat = self._img_normal
        elif self.toggle and self._state or self._dragging:
            mat = self._img_pressed
        elif self._hovering:
            mat = self._img_hover
        else:
            mat = self._img_normal

        # Apply selected material to sprite
        self._sprite.material = mat

        # Calculate center position for both sprite and background
        cx = self.left + self.width / 2
        cy = self.top + self.height / 2
        pos = self.context.screen_to_world(cx, cy, 1)

        # Update positions of both visual elements
        self._sprite.local.position = pos
        self._bg_mesh.local.position = pos


def tint_image(img: np.ndarray, hue_shift: float = 0.0, brightness: float = 1.0) -> np.ndarray:
    """Fast hue and brightness tinting using NumPy (supports white icons via saturation injection).

    Applies hue shift and brightness adjustments to an image using HSV color space
    conversion. This function is optimized for performance and handles edge cases
    like white/gray icons by injecting saturation when hue shifts are applied.

    Args:
        img: Input image as numpy array (RGB or RGBA)
        hue_shift: Hue shift in degrees (0-360, 0 = no change)
        brightness: Brightness multiplier (1.0 = no change, >1.0 = brighter, <1.0 = darker)

    Returns:
        Tinted image as numpy array with same shape and dtype as input

    Note:
        The function converts RGB to HSV, applies the tinting, then converts
        back to RGB. It handles edge cases like division by zero and provides
        robust saturation injection for white/gray icons when hue shifting.
    """
    # Normalize image to 0-1 range
    img = img.astype(np.float32) / 255.0
    rgb = img[..., :3]
    alpha = img[..., 3:] if img.shape[-1] == 4 else np.ones((*img.shape[:2], 1))

    # Extract RGB channels
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = np.max(rgb, axis=-1)
    minc = np.min(rgb, axis=-1)
    v = maxc

    # Calculate saturation (avoid division by zero)
    s = np.zeros_like(maxc)
    np.divide(maxc - minc, maxc, out=s, where=maxc > 0)

    # Calculate hue using RGB differences
    rc = (maxc - r) / (maxc - minc + 1e-8)
    gc = (maxc - g) / (maxc - minc + 1e-8)
    bc = (maxc - b) / (maxc - minc + 1e-8)

    # Determine hue based on which channel is maximum
    h = np.zeros_like(maxc)
    h[(maxc == r) & (maxc != minc)] = (bc - gc)[(maxc == r) & (maxc != minc)]
    h[(maxc == g) & (maxc != minc)] = 2.0 + (rc - bc)[(maxc == g) & (maxc != minc)]
    h[(maxc == b) & (maxc != minc)] = 4.0 + (gc - rc)[(maxc == b) & (maxc != minc)]
    h = (h / 6.0) % 1.0

    # Apply hue shift and brightness adjustments
    h = (h + hue_shift / 360.0) % 1.0
    v = np.clip(v * brightness, 0, 1)

    # Inject saturation for white/gray icons when hue shifting
    if hue_shift != 0.0:
        s = np.where((s < 0.05) & (v > 0.2), 1.0, s)

    # Convert HSV back to RGB
    i = (h * 6.0).astype(int)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)

    # Build RGB output based on hue sextant
    i = i % 6
    rgb_out = np.zeros_like(rgb)
    idx = i == 0
    rgb_out[idx] = np.stack([v, t, p], axis=-1)[idx]
    idx = i == 1
    rgb_out[idx] = np.stack([q, v, p], axis=-1)[idx]
    idx = i == 2
    rgb_out[idx] = np.stack([p, v, t], axis=-1)[idx]
    idx = i == 3
    rgb_out[idx] = np.stack([p, q, v], axis=-1)[idx]
    idx = i == 4
    rgb_out[idx] = np.stack([t, p, v], axis=-1)[idx]
    idx = i == 5
    rgb_out[idx] = np.stack([v, p, q], axis=-1)[idx]

    # Combine RGB with alpha and convert back to 0-255 range
    result = np.concatenate([rgb_out, alpha], axis=-1)
    return (result * 255).astype(np.uint8)
