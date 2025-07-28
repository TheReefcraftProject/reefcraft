# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

from collections.abc import Callable

import imageio.v3 as iio
import numpy as np
import pygfx as gfx

from reefcraft.ui.panel import Panel
from reefcraft.ui.widget import Widget
from reefcraft.utils.logger import logger
from reefcraft.utils.paths import icons_dir


def tint_image(image: np.ndarray, tint: float) -> np.ndarray:
    """Apply a brightness tint (0.0 to 1.0+) to a grayscale RGBA image."""
    tinted = image.copy()
    tinted[..., :3] = np.clip(tinted[..., :3] * tint, 0, 255)
    return tinted.astype(np.uint8)


class IconButton(Widget):
    """An icon-only button with automatic hover/pressed/toggle tinting."""

    def __init__(
        self,
        panel: Panel,
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
    ) -> None:
        super().__init__(top, left, width, height)
        self.panel: Panel = panel
        self.icon_name: str = icon
        self.enabled: bool = enabled
        self.toggle: bool = toggle
        self._state: bool = initial
        self._on_click_callback = on_click
        self._on_toggle_callback = on_toggle
        self._dragging = False
        self._is_pressed = False
        self._icon_scale = icon_scale

        # Load and generate tinted states
        img = iio.imread(icons_dir() / icon)

        self._img_normal = gfx.MeshBasicMaterial(map=gfx.Texture(tint_image(img, 0.5), dim=2), pick_write=True)
        self._img_hover = gfx.MeshBasicMaterial(map=gfx.Texture(tint_image(img, 0.9), dim=2), pick_write=True)
        self._img_pressed = gfx.MeshBasicMaterial(map=gfx.Texture(tint_image(img, 1.3), dim=2), pick_write=True)
        self._geometry = gfx.plane_geometry(int(width * icon_scale), int(height * icon_scale))
        self._sprite = gfx.Mesh(self._geometry, self._img_normal)

        self.panel.scene.add(self._sprite)

        # Event bindings
        _ = self._sprite.add_event_handler(self._on_mouse_enter, "pointer_enter")  # type: ignore
        _ = self._sprite.add_event_handler(self._on_mouse_leave, "pointer_leave")  # type: ignore
        _ = self._sprite.add_event_handler(self._on_mouse_down, "pointer_down")  # type: ignore
        _ = self._sprite.add_event_handler(self._on_mouse_up, "pointer_up")  # type: ignore

        self._update_visuals()

    def _on_mouse_enter(self, _event: gfx.PointerEvent) -> None:
        if self.enabled and not self._dragging:
            logger.debug("MOUSE ENTER ICON BUTTON")
            self._is_pressed = False
            self._update_visuals()

    def _on_mouse_leave(self, _event: gfx.PointerEvent) -> None:
        if self.enabled and not self._dragging:
            self._is_pressed = False
            self._update_visuals()

    def _on_mouse_down(self, event: gfx.PointerEvent) -> None:
        if not self.enabled:
            return
        self._dragging = True
        self._is_pressed = True
        event.target.set_pointer_capture(event.pointer_id, self.panel.renderer)
        self._update_visuals()

    def _on_mouse_up(self, event: gfx.PointerEvent) -> None:
        if not self.enabled:
            return
        if self._dragging:
            self._dragging = False
            self._is_pressed = False
            event.target.release_pointer_capture(event.pointer_id)

            if self.toggle:
                self._state = not self._state
                if self._on_toggle_callback:
                    self._on_toggle_callback(self._state)

            if self._on_click_callback:
                self._on_click_callback()

            self._update_visuals()

    def _update_visuals(self) -> None:
        tex = self._img_normal
        if not self.enabled:
            tex = self._img_normal
        elif self.toggle and self._state or self._is_pressed:
            tex = self._img_pressed
        elif not self._dragging:
            tex = self._img_hover

        self._sprite.material = tex
        self._sprite.local.position = self._screen_to_world(
            self.left + self.width / 2,
            self.top + self.height / 2,
            -1,
        )
