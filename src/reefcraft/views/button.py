# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Button widget implementation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

import pygfx as gfx

from .ui import Panel, Widget


class ButtonState(Enum):
    """Enumeration of possible button states."""

    NORMAL = auto()
    HOVER = auto()
    PRESSED = auto()
    DISABLED = auto()


@dataclass
class ButtonTheme:
    """Visual theme parameters for :class:`Button`."""

    color: tuple
    hover_color: tuple
    pressed_color: tuple
    disabled_color: tuple
    border_color: tuple
    border_thickness: float
    text_color: tuple
    disabled_text_color: tuple
    font_size: float
    font_name: str | None = None
    corner_radius: float = 0.0


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
        theme: ButtonTheme | None = None,
    ) -> None:
        """Create a new button widget."""
        super().__init__(top, left, width, height)
        self.panel = panel
        self.label = label
        self.enabled = enabled
        self.state = ButtonState.NORMAL if enabled else ButtonState.DISABLED

        # Default theme values
        self.theme = theme or ButtonTheme(
            color=(0.2, 0.2, 0.2),
            hover_color=(0.25, 0.25, 0.25),
            pressed_color=(0.15, 0.15, 0.15),
            disabled_color=(0.1, 0.1, 0.1),
            border_color=(1, 1, 1),
            border_thickness=1.0,
            text_color=(1, 1, 1),
            disabled_text_color=(0.5, 0.5, 0.5),
            font_size=12,
        )

        self._bg_mesh = gfx.Mesh(
            gfx.plane_geometry(width=width, height=height),
            gfx.MeshBasicMaterial(color=self.theme.color),
        )
        if self._bg_mesh.material is not None:
            self._bg_mesh.material.pick_write = True
        text_mat = gfx.TextMaterial(color=self.theme.text_color)
        text_mat.size = self.theme.font_size
        if self.theme.font_name is not None:
            text_mat.font = self.theme.font_name
        self._text = gfx.Text(self.label, text_mat)

        self.panel.scene.add(self._bg_mesh)
        self.panel.scene.add(self._text)

        self._bg_mesh.add_event_handler(self._on_enter, "pointer_enter")
        self._bg_mesh.add_event_handler(self._on_leave, "pointer_leave")
        self._bg_mesh.add_event_handler(self._on_down, "pointer_down")
        self._bg_mesh.add_event_handler(self._on_up, "pointer_up")

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

    def set_theme(self, theme: ButtonTheme) -> None:
        """Replace the current theme and refresh visuals."""
        self.theme = theme
        self._update_visuals()

    def on_click(self) -> None:  # pragma: no cover - meant to be overridden
        """Called when the button is activated."""
        pass

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_enter(self, event: gfx.PointerEvent) -> None:
        if self.enabled and self.state is not ButtonState.PRESSED:
            self.state = ButtonState.HOVER
            self._update_visuals()

    def _on_leave(self, event: gfx.PointerEvent) -> None:
        if self.enabled and self.state is not ButtonState.PRESSED:
            self.state = ButtonState.NORMAL
            self._update_visuals()

    def _on_down(self, event: gfx.PointerEvent) -> None:
        if self.enabled:
            self.state = ButtonState.PRESSED
            event.target.set_pointer_capture(event.pointer_id, self.panel.renderer)
            self._update_visuals()

    def _on_up(self, event: gfx.PointerEvent) -> None:
        if not self.enabled:
            return
        captured = event.target.has_pointer_capture(event.pointer_id)
        event.target.release_pointer_capture(event.pointer_id)
        if self.state is ButtonState.PRESSED and captured:
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
            color = self.theme.disabled_color
            text_color = self.theme.disabled_text_color
        elif self.state is ButtonState.HOVER:
            color = self.theme.hover_color
            text_color = self.theme.text_color
        elif self.state is ButtonState.PRESSED:
            color = self.theme.pressed_color
            text_color = self.theme.text_color
        else:
            color = self.theme.color
            text_color = self.theme.text_color

        if self._bg_mesh.material is not None:
            self._bg_mesh.material.color = color
        self._bg_mesh.geometry = gfx.plane_geometry(width=self.width, height=self.height)
        self._bg_mesh.local.position = self._screen_to_world(self.left + self.width / 2, self.top + self.height / 2, 0)

        self._text.material.color = text_color
        self._text.material.size = self.theme.font_size
        self._text.material.font = self.theme.font_name
        self._text.local.position = self._screen_to_world(self.left + self.width / 2, self.top + self.height / 2, -1)
