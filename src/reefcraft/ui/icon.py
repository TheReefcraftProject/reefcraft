# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Icon control for displaying image-based icons in the UI.

This module provides the Icon class that creates simple image-based
icon controls for the Reefcraft UI. Icons are loaded from the resources/icons
directory and displayed as textured meshes with customizable dimensions.

The Icon provides:
- Image-based icon display from icon files
- Customizable icon dimensions independent of control size
- Automatic icon positioning and centering
- Theme integration through the base Control class
- Support for various image formats (PNG, JPG, etc.)

Icons are commonly used for:
- Visual indicators and status symbols
- Navigation elements and buttons
- Decorative UI elements
- Branding and application identity
"""

import imageio.v3 as iio
import numpy as np
import pygfx as gfx

from reefcraft.ui.control import Control
from reefcraft.ui.ui_context import UIContext
from reefcraft.utils.paths import icons_dir


class Icon(Control):
    """A simple non-interactive control that displays an icon.

    The Icon class provides a lightweight way to display image-based
    icons in the UI. Icons are loaded from the resources/icons directory
    and rendered as textured meshes that can be positioned and sized
    independently of their source image dimensions.

    Key features:
    - Image-based icon rendering
    - Customizable display dimensions
    - Automatic centering within control boundaries
    - Efficient texture loading and caching
    - Integration with the UI layout system

    Icons are automatically centered within their control boundaries
    and can be sized independently of their source image dimensions,
    making them flexible for various UI layout needs.

    Attributes:
        context: UI context for rendering and event handling
        icon_name: Filename of the icon in resources/icons directory
        icon_width: Display width of the icon in pixels
        icon_height: Display height of the icon in pixels
        _icon_mesh: pygfx mesh object displaying the icon
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
        icon_width: int | None = None,
        icon_height: int | None = None,
    ) -> None:
        """Display an icon from resources/icons, optionally with a specific icon size.

        Initializes an icon control with the specified icon file and dimensions.
        The icon is loaded from the resources/icons directory and displayed
        as a textured mesh centered within the control boundaries.

        Args:
            context: UI context for rendering and event handling
            icon: Filename of the icon in the resources/icons directory
            left: Left position in pixels from layout origin
            top: Top position in pixels from layout origin
            width: Width of the control in pixels
            height: Height of the control in pixels
            icon_width: Optional custom width for the icon (uses control width if None)
            icon_height: Optional custom height for the icon (uses control height if None)
        """
        super().__init__(context=context, top=top, left=left, width=width, height=height)

        self.context = context
        self.icon_name = icon
        self.icon_width = icon_width or width
        self.icon_height = icon_height or height

        # Load and create the icon mesh
        self._icon_mesh = self._load_icon(icon)

        # Add icon to the scene and update visuals
        self.context.add(self._icon_mesh)
        self._update_visuals()

    def _load_icon(self, name: str) -> gfx.Mesh:
        """Load an icon image and return a textured mesh.

        Loads the specified icon file from the resources/icons directory,
        converts it to a texture, and creates a mesh with the appropriate
        material for display.

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
        mat = gfx.MeshBasicMaterial(map=tex)
        return gfx.Mesh(gfx.plane_geometry(1, 1), mat)

    def _update_visuals(self) -> None:
        """Position and size the icon mesh centered within the control.

        Updates the icon's geometry and position to reflect the current
        control dimensions and positioning. The icon is automatically
        centered within the control boundaries for consistent appearance.
        """
        # Update icon geometry to match desired dimensions
        self._icon_mesh.geometry = gfx.plane_geometry(self.icon_width, self.icon_height)

        # Position icon centered within control boundaries
        self._icon_mesh.local.position = self.context.screen_to_world(
            self.left + (self.width - self.icon_width) / 2 + self.icon_width / 2,
            self.top + (self.height - self.icon_height) / 2 + self.icon_height / 2,
            -1,
        )
