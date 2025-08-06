# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

import imageio.v3 as iio
import numpy as np
import pygfx as gfx

from reefcraft.ui.control import Control
from reefcraft.ui.ui_context import UIContext
from reefcraft.utils.paths import icons_dir


class Icon(Control):
    """A simple non-interactive control that displays an icon."""

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
        """Display an icon from resources/icons, optionally with a specific icon size."""
        super().__init__(context=context, top=top, left=left, width=width, height=height)
        self.context = context
        self.icon_name = icon
        self.icon_width = icon_width or width
        self.icon_height = icon_height or height
        self._icon_mesh = self._load_icon(icon)

        self.context.add(self._icon_mesh)
        self._update_visuals()

    def _load_icon(self, name: str) -> gfx.Mesh:
        """Load an icon image and return a textured mesh."""
        path = icons_dir() / name
        img = iio.imread(path).astype(np.float32) / 255.0
        tex = gfx.Texture(img, dim=2)
        mat = gfx.MeshBasicMaterial(map=tex)
        return gfx.Mesh(gfx.plane_geometry(1, 1), mat)

    def _update_visuals(self) -> None:
        """Position and size the icon mesh centered within the control."""
        self._icon_mesh.geometry = gfx.plane_geometry(self.icon_width, self.icon_height)
        self._icon_mesh.local.position = self.context.screen_to_world(
            self.left + (self.width - self.icon_width) / 2 + self.icon_width / 2,
            self.top + (self.height - self.icon_height) / 2 + self.icon_height / 2,
            -1,
        )
