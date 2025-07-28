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
from reefcraft.ui.theme import Theme
from reefcraft.ui.widget import Widget
from reefcraft.utils.logger import logger
from reefcraft.utils.paths import icons_dir


class IconButton(Widget):
    """An icon-only button that visually responds by tinting its texture."""

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
        normal_tint: tuple[float, float] = (0.0, 0.5),  # hue shift, brightness
        hover_tint: tuple[float, float] = (0.0, 0.9),
        pressed_tint: tuple[float, float] = (0.0, 1.3),
        theme: Theme | None = None,
    ) -> None:
        """Create a icon button."""
        super().__init__(top, left, width, height)
        self.panel = panel
        self.icon_name = icon
        self.enabled = enabled
        self.toggle = toggle
        self._state = initial
        self._hovering = False
        self._dragging = False
        self._on_click_callback = on_click
        self._on_toggle_callback = on_toggle

        # Load and prepare tinted textures
        img = iio.imread(icons_dir() / icon)
        self._img_normal = gfx.MeshBasicMaterial(map=gfx.Texture(tint_image(img, *normal_tint), dim=2), depth_test=False, pick_write=False)
        self._img_hover = gfx.MeshBasicMaterial(map=gfx.Texture(tint_image(img, *hover_tint), dim=2), depth_test=False, pick_write=False)
        self._img_pressed = gfx.MeshBasicMaterial(map=gfx.Texture(tint_image(img, *pressed_tint), dim=2), depth_test=False, pick_write=False)

        self._geometry = gfx.plane_geometry(int(width * icon_scale), int(height * icon_scale))
        self._sprite = gfx.Mesh(self._geometry, self._img_normal)

        # Transparent pickable background for interaction
        self._bg_material = gfx.MeshBasicMaterial(color=self.theme.group_color, pick_write=True)
        self._bg_mesh = gfx.Mesh(self._geometry, self._bg_material)

        self.panel.scene.add(self._sprite)
        self.panel.scene.add(self._bg_mesh)

        # Register event handlers  on the background mesh
        _ = self._bg_mesh.add_event_handler(self._on_mouse_enter, "pointer_enter")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_leave, "pointer_leave")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_down, "pointer_down")  # type: ignore
        _ = self._bg_mesh.add_event_handler(self._on_mouse_up, "pointer_up")  # type: ignore

        self._update_visuals()

    def _on_mouse_enter(self, _event: gfx.PointerEvent) -> None:
        if self.enabled:
            self._hovering = True
            self._update_visuals()

    def _on_mouse_leave(self, _event: gfx.PointerEvent) -> None:
        if self.enabled:
            self._hovering = False
            self._update_visuals()

    def _on_mouse_down(self, event: gfx.PointerEvent) -> None:
        if not self.enabled:
            return
        self._dragging = True
        event.target.set_pointer_capture(event.pointer_id, self.panel.renderer)
        self._update_visuals()

    def _on_mouse_up(self, event: gfx.PointerEvent) -> None:
        if not self.enabled:
            return
        if self._dragging:
            self._dragging = False
            event.target.release_pointer_capture(event.pointer_id)

            if self.toggle:
                self._state = not self._state
                if self._on_toggle_callback:
                    self._on_toggle_callback(self._state)

            if self._on_click_callback:
                self._on_click_callback()

            self._update_visuals()

    def _update_visuals(self) -> None:
        """Apply the correct icon texture tint based on state."""
        if not self.enabled:
            mat = self._img_normal
        elif self.toggle and self._state or self._dragging:
            mat = self._img_pressed
        elif self._hovering:
            mat = self._img_hover
        else:
            mat = self._img_normal

        self._sprite.material = mat

        cx = self.left + self.width / 2
        cy = self.top + self.height / 2
        pos = self._screen_to_world(cx, cy, 1)

        self._sprite.local.position = pos
        self._bg_mesh.local.position = pos


def tint_image(img: np.ndarray, hue_shift: float = 0.0, brightness: float = 1.0) -> np.ndarray:
    """Fast hue and brightness tinting using NumPy (supports white icons via saturation injection)."""
    img = img.astype(np.float32) / 255.0
    rgb = img[..., :3]
    alpha = img[..., 3:] if img.shape[-1] == 4 else np.ones((*img.shape[:2], 1))

    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = np.max(rgb, axis=-1)
    minc = np.min(rgb, axis=-1)
    v = maxc
    s = np.where(maxc == 0, 0, (maxc - minc) / maxc)

    # Hue calculation
    rc = (maxc - r) / (maxc - minc + 1e-8)
    gc = (maxc - g) / (maxc - minc + 1e-8)
    bc = (maxc - b) / (maxc - minc + 1e-8)

    h = np.zeros_like(maxc)
    h[(maxc == r) & (maxc != minc)] = (bc - gc)[(maxc == r) & (maxc != minc)]
    h[(maxc == g) & (maxc != minc)] = 2.0 + (rc - bc)[(maxc == g) & (maxc != minc)]
    h[(maxc == b) & (maxc != minc)] = 4.0 + (gc - rc)[(maxc == b) & (maxc != minc)]
    h = (h / 6.0) % 1.0

    # Apply hue shift and brightness
    h = (h + hue_shift / 360.0) % 1.0
    v = np.clip(v * brightness, 0, 1)

    # Inject saturation to allow color tinting of white/gray only when hue shift is applied
    if hue_shift != 0.0:
        s = np.where((s < 0.05) & (v > 0.2), 1.0, s)

    # HSV to RGB
    i = (h * 6.0).astype(int)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)

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

    result = np.concatenate([rgb_out, alpha], axis=-1)
    return (result * 255).astype(np.uint8)
