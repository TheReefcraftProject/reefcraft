# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Button widget implementation."""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

import pygfx as gfx

if TYPE_CHECKING:
    from collections.abc import Callable

    from reefcraft.ui.panel import Panel
from reefcraft.ui.widget import Widget


class ButtonState(Enum):
    """Enumeration of possible button states."""

    NORMAL = auto()
    HOVER = auto()
    PRESSED = auto()
    DISABLED = auto()


class Button(Widget):
    """Interactive UI button."""

    def __init__(
        self,
        panel: Panel,
        *,
        left: int,
        top: int,
        width: int,
        height: int,
        label: str = "",
        enabled: bool = True,
        on_click: Callable[[], None] | None = None,
    ) -> None:
        """Create a new button widget."""
        super().__init__(top, left, width, height)
        self.panel = panel
        self.label = label
        self.enabled = enabled
        self._on_click_callback = on_click

        self.state = ButtonState.NORMAL if enabled else ButtonState.DISABLED

        self.mat_normal = gfx.MeshBasicMaterial(color=self.theme.color, pick_write=True)
        self.mat_disabled = gfx.MeshBasicMaterial(color=self.theme.disabled_color, pick_write=True)
        self.mat_hover = gfx.MeshBasicMaterial(color=self.theme.hover_color, pick_write=True)
        self.mat_pressed = gfx.MeshBasicMaterial(color=self.theme.highlight_color, pick_write=True)

        self._bg_mesh = gfx.Mesh(
            gfx.plane_geometry(width=width, height=height),
            self.mat_normal,
        )
        text_mat = gfx.TextMaterial(color=self.theme.text_color)
        self._text = gfx.Text(self.label, text_mat)

        self._dragging = False

        self.panel.scene.add(self._bg_mesh)
        self.panel.scene.add(self._text)

        # Bind event handlers to the background mesh (which is clickable)
        self._bg_mesh.add_event_handler(self._on_mouse_enter, "pointer_enter")
        self._bg_mesh.add_event_handler(self._on_mouse_leave, "pointer_leave")
        self._bg_mesh.add_event_handler(self._on_mouse_down, "pointer_down")
        self._bg_mesh.add_event_handler(self._on_mouse_up, "pointer_up")

        self._update_visuals()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_label(self, text: str) -> None:
        """Update the button label."""
        self.label = text
        self._text.set_text(text)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the button."""
        self.enabled = enabled
        self.state = ButtonState.NORMAL if enabled else ButtonState.DISABLED
        self._update_visuals()

    def on_click(self) -> None:
        """Called when the button is activated. Can be overridden or passed in as a callback."""
        if self._on_click_callback:
            self._on_click_callback()

    # ------------------------------------------------------------------
    # Event handlers (Slider-style logic)
    # ------------------------------------------------------------------

    def _on_mouse_enter(self, event: gfx.PointerEvent) -> None:
        if self.enabled and not self._dragging:
            self.state = ButtonState.HOVER
            self._update_visuals()

    def _on_mouse_leave(self, event: gfx.PointerEvent) -> None:
        if self.enabled and not self._dragging:
            self.state = ButtonState.NORMAL
            self._update_visuals()

    def _on_mouse_down(self, event: gfx.PointerEvent) -> None:
        if not self.enabled:
            return
        self._dragging = True
        self.state = ButtonState.PRESSED
        event.target.set_pointer_capture(event.pointer_id, self.panel.renderer)
        self._update_visuals()

    def _on_mouse_up(self, event: gfx.PointerEvent) -> None:
        if not self.enabled:
            return
        if self._dragging:
            self._dragging = False
            event.target.release_pointer_capture(event.pointer_id)
            if self.state == ButtonState.PRESSED:
                self.on_click()
            self.state = ButtonState.HOVER
            self._update_visuals()

    # ------------------------------------------------------------------
    # Visual updates
    # ------------------------------------------------------------------
    def _screen_to_world(self, x: float, y: float, z: float = 0.0) -> tuple[float, float, float]:
        return (x - 1920 / 2, 1080 / 2 - y, z)

    def _update_visuals(self) -> None:
        if self.state is ButtonState.DISABLED:
            self._bg_mesh.material = self.mat_disabled
        elif self.state is ButtonState.HOVER:
            self._bg_mesh.material = self.mat_hover
        elif self.state is ButtonState.PRESSED:
            self._bg_mesh.material = self.mat_pressed
        else:
            self._bg_mesh.material = self.mat_normal

        self._bg_mesh.geometry = gfx.plane_geometry(width=self.width, height=self.height)
        self._bg_mesh.local.position = self._screen_to_world(self.left + self.width / 2, self.top + self.height / 2, 0)
        self._text.local.position = self._screen_to_world(self.left + self.width / 2, self.top + self.height / 2, -1)
