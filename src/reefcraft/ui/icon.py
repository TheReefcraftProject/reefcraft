# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

import imageio.v3 as iio
import numpy as np
import pygfx as gfx

from reefcraft.ui.panel import Panel
from reefcraft.ui.widget import Widget
from reefcraft.utils.paths import icons_dir


class Icon(Widget):
    """A simple non-interactive widget that displays an icon."""

    def __init__(
        self,
        panel: Panel,
        icon: str,
        *,
        left: int = 0,
        top: int = 0,
        width: int = 32,
        height: int = 32,
    ) -> None:
        """Display an icon from resources/icons."""
        super().__init__(top, left, width, height)
        self.panel = panel
        self.icon_name = icon
        self._icon_mesh = self._load_icon(icon)

        self.panel.scene.add(self._icon_mesh)
        self._update_visuals()

    def _screen_to_world(self, x: float, y: float, z: float = 0.0) -> tuple[float, float, float]:
        return (x - 1920 / 2, 1080 / 2 - y, z)

    def _load_icon(self, name: str) -> gfx.Mesh:
        """Load an icon image and return a textured mesh."""
        path = icons_dir() / name
        img = iio.imread(path).astype(np.float32) / 255.0
        tex = gfx.Texture(img, dim=2)
        mat = gfx.MeshBasicMaterial(map=tex)
        return gfx.Mesh(gfx.plane_geometry(1, 1), mat)

    def _update_visuals(self) -> None:
        """Position and size the icon mesh."""
        size = min(self.width, self.height)
        self._icon_mesh.geometry = gfx.plane_geometry(size, size)
        self._icon_mesh.local.position = self._screen_to_world(
            self.left + self.width / 2,
            self.top + self.height / 2,
            -1,
        )
