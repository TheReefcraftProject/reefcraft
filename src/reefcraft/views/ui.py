# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout as a side panel."""

import pygfx as gfx
from reefcraft.reefcraft_logging import logger


class Widget:
    """A base cass for all widget types."""

    def __init__(self, top: int, left: int, width: int, height: int) -> None:
        """Create the slider and add it to the given ``panel`` scene."""
        self.top = top
        self.left = left
        self.width = width
        self.height = height


class ListLayout:
    """A simple retained-mode slider widget."""

    def __init__(self) -> None:
        """Create the slider and add it to the given ``panel`` scene."""
        self.widgets: list[Widget] = []
        self.line_spacing = 10

    def add_widget(self, widget: Widget) -> None:
        """Append another widget to the list."""
        self.widgets.append(widget)

    @property
    def height(self) -> int:
        """Sum the heights of all the widgets plus the line spacing."""
        return 100


class Slider(Widget):
    """A simple retained-mode slider widget."""

    def __init__(
        self,
        panel: "Panel",
        *,
        left: int,
        top: int,
        width: int,
        height: int,
        min_value: float = 0.0,
        max_value: float = 1.0,
        value: float | None = None,
        background_color: str = "#1E182B",
        foreground_color: str = "#4343EC",
        text_color: str = "#D8D8D8",
    ) -> None:
        """Create the slider and add it to the given ``panel`` scene."""
        super().__init__(top, left, width, height)
        self.panel = panel
        self.min = min_value
        self.max = max_value
        self.value = value if value is not None else min_value
        self.background_color = background_color
        self.foreground_color = foreground_color
        self.text_color = text_color

        self._dragging = False

        # Background mesh
        self._bg_mesh = gfx.Mesh(
            gfx.plane_geometry(width=width, height=height),
            gfx.MeshBasicMaterial(color=background_color),
        )
        if self._bg_mesh.material is not None:
            self._bg_mesh.material.pick_write = True

        # Foreground mesh showing the filled portion
        self._fg_mesh = gfx.Mesh(
            gfx.plane_geometry(width=1, height=height),
            gfx.MeshBasicMaterial(color=foreground_color),
        )

        # Text overlay (transparent background)
        text_mat = gfx.TextMaterial(color=text_color)
        self._text = gfx.Text(str(self.value), text_mat)

        self.panel.scene.add(self._bg_mesh)
        self.panel.scene.add(self._fg_mesh)
        self.panel.scene.add(self._text)

        self._bg_mesh.add_event_handler(self._on_mouse_down, "pointer_down")
        self._bg_mesh.add_event_handler(self._on_mouse_move, "pointer_move")
        self._bg_mesh.add_event_handler(self._on_mouse_up, "pointer_up")

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
        self.value = self.min + t * (self.max - self.min)
        self._update_visuals()

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


class Section:
    """A sub-section of the UI to show/hide."""

    def __init__(self) -> None:
        """Initialize the section TBD."""
        logger.debug("Section initialized - not yet implemented")


class Panel:
    """A left-docked panel: covers left 300px of canvas height."""

    def __init__(self, renderer: gfx.WgpuRenderer, width: int = 300, height: int = 1080) -> None:
        """Initialize the panel and its correstponding 3D scene and ortho cameras."""
        self.renderer = renderer
        self.viewport = gfx.Viewport(renderer)

        geom = gfx.plane_geometry(width=width, height=height, width_segments=1, height_segments=1)
        mat = gfx.MeshBasicMaterial(color="#08080A")
        mesh = gfx.Mesh(geom, mat)
        mesh.local.position = (-((1920 / 2) - (300 / 2)), 0, -100)

        # Block the picking for the background of the panel
        if mesh.material is not None:
            mesh.material.pick_write = True
        mesh.add_event_handler(self._on_mouse_down, "pointer_down")
        mesh.add_event_handler(self._on_mouse_up, "pointer_up")

        self.scene = gfx.Scene()
        self.camera = gfx.OrthographicCamera(width=1920, height=1080)
        self.scene.add(mesh)

        Slider(self, left=20, top=20, width=250, height=20, min_value=0, max_value=100, value=10)
        Slider(self, left=20, top=50, width=250, height=20, min_value=0, max_value=100, value=70)
        Slider(self, left=20, top=80, width=250, height=20, min_value=0, max_value=100, value=15)

    def _on_mouse_down(self, event: gfx.PointerEvent) -> None:
        """When the mouse is clicked in background of the panel, capture the mouse and block others."""
        event.target.set_pointer_capture(event.pointer_id, self.renderer)
        pass

    def _on_mouse_up(self, event: gfx.PointerEvent) -> None:
        """Release the mouse on mouse up."""
        event.target.release_pointer_capture(event.pointer_id)
        pass

    def update(self, time: float) -> None:
        """Update the UI."""
        pass

    def draw(self) -> None:
        """Draw a solid rectangle on the left side of the UI scene."""
        self.viewport.render(self.scene, self.camera)  # , flush=False)
