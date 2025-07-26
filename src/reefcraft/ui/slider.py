# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout as a side panel."""

from collections.abc import Callable

import pygfx as gfx

from reefcraft.ui.panel import Panel
from reefcraft.ui.widget import Widget


class Slider(Widget):
    """A simple retained-mode slider widget."""

    def __init__(
        self,
        panel: Panel,
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
        """Create the slider and add it to the given ``panel`` scene."""
        super().__init__(top, left, width, height)
        self.panel = panel
        self.min = min_value
        self.max = max_value
        self.value = value if value is not None else min_value
        self._on_change_callback = on_change

        self._dragging = False

        # Background mesh
        self._bg_mesh = gfx.Mesh(
            gfx.plane_geometry(width=width, height=height),
            gfx.MeshBasicMaterial(color=self.theme.color),
        )
        if self._bg_mesh.material is not None:
            self._bg_mesh.material.pick_write = True

        # Foreground mesh showing the filled portion
        self._fg_mesh = gfx.Mesh(
            gfx.plane_geometry(width=1, height=height),
            gfx.MeshBasicMaterial(color=self.theme.highlight_color),
        )

        # Text overlay (transparent background)
        text_mat = gfx.TextMaterial(color=self.theme.text_color)
        self._text = gfx.Text(str(self.value), text_mat)

        self.panel.scene.add(self._bg_mesh)
        self.panel.scene.add(self._fg_mesh)
        self.panel.scene.add(self._text)

        self._bg_mesh.add_event_handler(self._on_mouse_down, "pointer_down")
        self._bg_mesh.add_event_handler(self._on_mouse_move, "pointer_move")
        self._bg_mesh.add_event_handler(self._on_mouse_up, "pointer_up")

        self._update_visuals()

    def set_value(self, value: float) -> None:
        """Changes the value and calls the callback to the data source."""
        if value != self.value:
            self.value = value
            if self._on_change_callback:
                self._on_change_callback(self.value)
            self._update_visuals()

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _screen_to_world(self, x: float, y: float, z: float = 0) -> tuple[float, float, float]:
        """Convert screen-space coordinates to panel's world space."""
        return (
            x - 1920 / 2,
            1080 / 2 - y,
            z,
        )

    @property
    def _percent(self) -> float:
        return (self.value - self.min) / (self.max - self.min)

    def _set_from_screen_x(self, x: float) -> None:
        t = (x - self.left) / self.width
        t = max(0.0, min(1.0, t))
        self.set_value(self.min + t * (self.max - self.min))

    def _update_visuals(self) -> None:
        filled = max(0.0, min(1.0, self._percent))
        # Background
        self._bg_mesh.geometry = gfx.plane_geometry(width=self.width, height=self.height)
        self._bg_mesh.local.position = self._screen_to_world(self.left + self.width / 2, self.top + self.height / 2, -1)

        # Foreground
        self._fg_mesh.geometry = gfx.plane_geometry(width=int(self.width * filled), height=self.height)
        self._fg_mesh.local.position = self._screen_to_world(self.left + (self.width * filled) / 2, self.top + self.height / 2, 0)

        # Text overlay
        self._text.set_text(f"{self.value:.2f}")
        self._text.local.position = self._screen_to_world(self.left + self.width / 2, self.top + self.height / 2, -2)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_mouse_down(self, event: gfx.PointerEvent) -> None:
        """Capture the mouse for slider control."""
        self._dragging = True
        event.target.set_pointer_capture(event.pointer_id, self.panel.renderer)
        self._set_from_screen_x(event.x)

    def _on_mouse_move(self, event: gfx.PointerEvent) -> None:
        """Update the dragging on the slider."""
        if self._dragging:
            self._set_from_screen_x(event.x)

    def _on_mouse_up(self, event: gfx.PointerEvent) -> None:
        """Release the mouse on mouse up."""
        if self._dragging:
            self._dragging = False
            event.target.release_pointer_capture(event.pointer_id)
            self._set_from_screen_x(event.x)
