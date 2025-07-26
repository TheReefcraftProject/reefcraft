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
        left: int = 0,
        top: int = 0,
        width: int = 100,
        height: int = 20,
        label: str = "",
        enabled: bool = True,
        on_click: Callable[[], None] | None = None,
    ) -> None:
        """Create a new button widget."""
        super().__init__(top, left, width, height)
        self.panel: Panel = panel
        self.label: str = label
        self.enabled: bool = enabled
        self._on_click_callback: Callable[[], None] | None = on_click

        self.state: ButtonState = ButtonState.NORMAL if enabled else ButtonState.DISABLED

        self.mat_normal: gfx.MeshBasicMaterial = gfx.MeshBasicMaterial(color=self.theme.color, pick_write=True)
        self.mat_disabled: gfx.MeshBasicMaterial = gfx.MeshBasicMaterial(color=self.theme.disabled_color, pick_write=True)
        self.mat_hover: gfx.MeshBasicMaterial = gfx.MeshBasicMaterial(color=self.theme.hover_color, pick_write=True)
        self.mat_pressed: gfx.MeshBasicMaterial = gfx.MeshBasicMaterial(color=self.theme.highlight_color, pick_write=True)

        self._bg_mesh: gfx.Mesh = gfx.Mesh(
            gfx.plane_geometry(width=width, height=height),
            self.mat_normal,
        )
        text_mat: gfx.TextMaterial = gfx.TextMaterial(color=self.theme.text_color)
        self._text: gfx.Text = gfx.Text(self.label, text_mat)

        self._dragging: bool = False

        _ = self.panel.scene.add(self._bg_mesh)
        _ = self.panel.scene.add(self._text)

        # Bind event handlers to the background mesh (which is clickable)
        _ = self._bg_mesh.add_event_handler(self._on_mouse_enter, "pointer_enter")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_leave, "pointer_leave")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_down, "pointer_down")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_up, "pointer_up")  # type: ignore

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

    def _on_mouse_enter(self, _event: gfx.PointerEvent) -> None:
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


class ToggleButton(Button):
    """A button that toggles between two labeled states, like Play/Pause."""

    def __init__(
        self,
        panel: Panel,
        label_on: str,
        label_off: str,
        *,
        initial: bool = False,
        on_toggle: Callable[[bool], None] | None = None,
        width: int = 100,
        height: int = 20,
    ) -> None:
        """Initialize a toggleable button with two visual states."""
        self._label_on = label_on
        self._label_off = label_off
        self._state = initial
        self._on_toggle = on_toggle

        # Use the correct label for the initial state
        super().__init__(
            panel,
            label=self._label_on if self._state else self._label_off,
            width=width,
            height=height,
            on_click=self._handle_click,
        )

        self._update_visuals()

    def _handle_click(self) -> None:
        """Handle button toggle logic when clicked."""
        self._state = not self._state
        self.set_label(self._label_on if self._state else self._label_off)
        self._update_visuals()
        if self._on_toggle:
            self._on_toggle(self._state)

    def _update_visuals(self) -> None:
        """Update the button's visual state based on toggle status."""
        # If toggled on and enabled, override the normal visual logic
        if self._state and self.enabled:
            self._bg_mesh.material = self.mat_pressed
        else:
            super()._update_visuals()

        self._is_pressed = self._state  # visually depressed when toggled "on" - future

    @property
    def is_toggled(self) -> bool:
        """Return the current toggle state."""
        return self._state
