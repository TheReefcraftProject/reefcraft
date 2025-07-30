# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Button widget implementation with optional icon support."""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

import imageio.v3 as iio
import numpy as np
import pygfx as gfx

from reefcraft.ui.widget import Widget
from reefcraft.utils.paths import icons_dir

if TYPE_CHECKING:
    from collections.abc import Callable

    from reefcraft.ui.panel import Panel


class ButtonState(Enum):
    """Enumeration of possible button states."""

    NORMAL = auto()
    HOVER = auto()
    PRESSED = auto()
    DISABLED = auto()


class Button(Widget):
    """Interactive UI button with optional icon."""

    def __init__(
        self,
        panel: Panel,
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
        """Create a new button widget."""
        super().__init__(top, left, width, height)
        self.panel: Panel = panel
        self.label: str = label
        self.enabled: bool = enabled
        self._on_click_callback: Callable[[], None] | None = on_click
        self.icon_name: str | None = icon
        self.icon_width: int | None = icon_width
        self.icon_height: int | None = icon_height

        self.state: ButtonState = ButtonState.NORMAL if enabled else ButtonState.DISABLED

        self.mat_normal = gfx.MeshBasicMaterial(color=self.theme.color, pick_write=True)
        self.mat_disabled = gfx.MeshBasicMaterial(color=self.theme.disabled_color, pick_write=True)
        self.mat_hover = gfx.MeshBasicMaterial(color=self.theme.hover_color, pick_write=True)
        self.mat_pressed = gfx.MeshBasicMaterial(color=self.theme.highlight_color, pick_write=True)

        self._bg_mesh = gfx.Mesh(gfx.plane_geometry(width=width, height=height), self.mat_normal)
        text_mat = gfx.TextMaterial(color=self.theme.text_color)
        self._text = gfx.Text(self.label, text_mat)

        self._icon_mesh: gfx.Mesh | None = self._load_icon(icon) if icon else None

        _ = self.panel.scene.add(self._bg_mesh)
        _ = self.panel.scene.add(self._text)
        if self._icon_mesh:
            _ = self.panel.scene.add(self._icon_mesh)

        self._dragging = False

        _ = self._bg_mesh.add_event_handler(self._on_mouse_enter, "pointer_enter")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_leave, "pointer_leave")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_down, "pointer_down")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_up, "pointer_up")  # type: ignore

        self._update_visuals()

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
        """Called when the button is activated."""
        if self._on_click_callback:
            self._on_click_callback()

    def _on_mouse_enter(self, _event: gfx.PointerEvent) -> None:
        if self.enabled and not self._dragging:
            self.state = ButtonState.HOVER
            self._update_visuals()

    def _on_mouse_leave(self, _event: gfx.PointerEvent) -> None:
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

    def _update_visuals(self) -> None:
        # Background material
        if self.state is ButtonState.DISABLED:
            self._bg_mesh.material = self.mat_disabled
        elif self.state is ButtonState.HOVER:
            self._bg_mesh.material = self.mat_hover
        elif self.state is ButtonState.PRESSED:
            self._bg_mesh.material = self.mat_pressed
        else:
            self._bg_mesh.material = self.mat_normal

        # Geometry and placement
        self._bg_mesh.geometry = gfx.plane_geometry(width=self.width, height=self.height)
        self._bg_mesh.local.position = self._screen_to_world(self.left + self.width / 2, self.top + self.height / 2, 0)

        # Text placement (centered)
        self._text.local.position = self._screen_to_world(self.left + self.width / 2, self.top + self.height / 2, -2)

        # Icon placement (centered)
        if self._icon_mesh:
            iw = self.icon_width or self.width
            ih = self.icon_height or self.height
            self._icon_mesh.geometry = gfx.plane_geometry(iw, ih)
            self._icon_mesh.local.position = self._screen_to_world(
                self.left + (self.width - iw) / 2 + iw / 2,
                self.top + (self.height - ih) / 2 + ih / 2,
                -1,
            )

    def _load_icon(self, name: str) -> gfx.Mesh:
        """Load an icon image from the resources/icons directory and return a mesh."""
        path = icons_dir() / name
        img = iio.imread(path).astype(np.float32) / 255.0
        tex = gfx.Texture(img, dim=2)
        mat = gfx.MeshBasicMaterial(map=tex, depth_test=False)
        return gfx.Mesh(gfx.plane_geometry(1, 1), mat)


class ToggleButton(Button):
    """A button that toggles between two labeled/icon states, like Play/Pause."""

    def __init__(
        self,
        panel: Panel,
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
        """Initialize a toggleable button with optional label/icon states."""
        self._label_on = label_on
        self._label_off = label_off
        self._icon_on = icon_on
        self._icon_off = icon_off
        self._state = initial
        self._on_toggle = on_toggle

        # Determine initial values
        init_label = self._label_on if self._state else self._label_off
        init_icon = self._icon_on if self._state else self._icon_off

        super().__init__(
            panel,
            label=init_label or "",
            icon=init_icon,
            icon_width=icon_width,
            icon_height=icon_height,
            width=width,
            height=height,
            on_click=self._handle_click,
        )

        self._update_visuals()

    def _handle_click(self) -> None:
        """Handle button toggle logic when clicked."""
        self._state = not self._state

        # Update label if defined
        if self._label_on or self._label_off:
            new_label = self._label_on if self._state else self._label_off
            self.set_label(new_label or "")

        # Swap icon if needed
        new_icon = self._icon_on if self._state else self._icon_off
        if new_icon and new_icon != self.icon_name:
            if self._icon_mesh:
                self.panel.scene.remove(self._icon_mesh)
            self.icon_name = new_icon
            self._icon_mesh = self._load_icon(new_icon)
            self.panel.scene.add(self._icon_mesh)

        self._update_visuals()

        if self._on_toggle:
            self._on_toggle(self._state)

    def _update_visuals(self) -> None:
        """Update the button's visual state based on toggle status."""
        super()._update_visuals()  # Update text, icon, layout

        if self._state and self.enabled:
            self._bg_mesh.material = self.mat_pressed

        self._is_pressed = self._state
