# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Manage auto-layout options for groups of widgets."""

from enum import Enum, auto

import numpy as np
import pygfx as gfx

from reefcraft.ui.control import Control
from reefcraft.ui.theme import Theme
from reefcraft.utils.logger import logger


class LayoutDirection(Enum):
    """Layout direction: vertical (top-down) or horizontal (left-right)."""

    VERTICAL = auto()
    HORIZONTAL = auto()


class Alignment(Enum):
    """Widget alignment within the cross-axis of the layout."""

    START = auto()
    CENTER = auto()
    END = auto()


class Layout(Control):
    """A layout widget that arranges child widgets vertically or horizontally."""

    def __init__(
        self,
        scene: gfx.Scene | None = None,
        *,
        controls: list[Control] | None = None,
        direction: LayoutDirection = LayoutDirection.VERTICAL,
        spacing: int = 2,
        margin: int = 0,
        alignment: Alignment = Alignment.START,
    ) -> None:
        """Create a new layout widget.

        Args:
            direction: LayoutDirection.VERTICAL or HORIZONTAL.
            widgets: Optional initial list of widgets.
            spacing: Space between items.
            margin: Outer margin around layout.
            alignment: Cross-axis alignment of child widgets.
        """
        super().__init__(top=0, left=0, width=0, height=0)

        self.scene = scene
        self.direction = direction
        self.spacing = spacing
        self.margin = margin
        self.alignment = alignment
        self.controls: list[Control] = []
        if controls:
            for widget in controls:
                self.add_widget(widget)

    def add_widget(self, widget: Control) -> None:
        """Append a widget to the layout and register for change tracking."""
        self.controls.append(widget)
        widget.on_change(self._layout)
        self._layout()

    def set_spacing(self, spacing: int) -> None:
        """Set the space between widgets and relayout."""
        self.spacing = spacing
        self._layout()

    def set_margin(self, margin: int) -> None:
        """Set the outer margin around the layout and relayout."""
        self.margin = margin
        self._layout()

    def set_alignment(self, alignment: Alignment) -> None:
        """Set widget alignment along the cross-axis and relayout."""
        self.alignment = alignment
        self._layout()

    def relayout(self) -> None:
        """Public trigger for layout recomputation."""
        self._layout()

    def _layout(self) -> None:
        """Internal layout logic: positions widgets and sizes layout accordingly."""
        offset = 0
        max_cross = 0

        for widget in self.controls:
            if self.direction == LayoutDirection.VERTICAL:
                widget.top = self.top + self.margin + offset
                offset += widget.height
                max_cross = max(max_cross, widget.width)
            else:
                widget.left = self.left + self.margin + offset
                offset += widget.width
                max_cross = max(max_cross, widget.height)

            offset += self.spacing

        if self.controls:
            offset -= self.spacing  # remove last spacing

        if self.direction == LayoutDirection.VERTICAL:
            self.height = offset + self.margin * 2
            self.width = max_cross + self.margin * 2
        else:
            self.width = offset + self.margin * 2
            self.height = max_cross + self.margin * 2

        # Align widgets along cross-axis
        for widget in self.controls:
            if self.direction == LayoutDirection.VERTICAL:
                if self.alignment == Alignment.CENTER:
                    widget.left = self.left + self.margin + (self.width - 2 * self.margin - widget.width) // 2
                elif self.alignment == Alignment.END:
                    widget.left = self.left + self.width - self.margin - widget.width
                else:  # START
                    widget.left = self.left + self.margin
            else:
                if self.alignment == Alignment.CENTER:
                    widget.top = self.top + self.margin + (self.height - 2 * self.margin - widget.height) // 2
                elif self.alignment == Alignment.END:
                    widget.top = self.top + self.height - self.margin - widget.height
                else:  # START
                    widget.top = self.top + self.margin

    def _update_visuals(self) -> None:
        """Update child widget positions when this layout moves."""
        self._layout()


def create_line_rectangle(width: int, height: int) -> gfx.Geometry:
    """Return a rectangle outline geometry for gfx.Line."""
    points = np.array(
        [
            [-width / 2, -height / 2, 0],
            [+width / 2, -height / 2, 0],
            [+width / 2, +height / 2, 0],
            [-width / 2, +height / 2, 0],
            [-width / 2, -height / 2, 0],  # close the loop
        ],
        dtype=np.float32,
    )
    return gfx.Geometry(positions=points)


class Group(Layout):
    """A drawable layout container with background, frame, and optional header."""

    def __init__(
        self,
        scene: gfx.Scene,
        *,
        controls: list[Control] | None = None,
        direction: LayoutDirection = LayoutDirection.VERTICAL,
        spacing: int = 2,
        margin: int = 0,
        alignment: Alignment = Alignment.START,
        draw: bool = True,
        header: str | None = None,
        theme: Theme | None = None,
    ) -> None:
        super().__init__(
            scene=scene,
            controls=controls,
            direction=direction,
            spacing=spacing,
            margin=margin,
            alignment=alignment,
        )

        self.draw = draw
        self.header = header
        self.theme = theme or Theme()

        # Initialize background and frame placeholders
        self._bg_mesh = gfx.Mesh(
            gfx.plane_geometry(1, 1),
            gfx.MeshBasicMaterial(color=self.theme.group_color),
        )
        self._frame_mesh = gfx.Line(
            create_line_rectangle(1, 1),
            gfx.LineMaterial(color=self.theme.outline_color, thickness=1),
        )

        scene.add(self._bg_mesh)
        scene.add(self._frame_mesh)

    def _update_visuals(self) -> None:
        super()._update_visuals()

        if not getattr(self, "draw", False):
            return  # <--- Early exit if draw is disabled

        self._bg_mesh.visible = False
        self._frame_mesh.visible = False

        self._bg_mesh.visible = True
        self._frame_mesh.visible = True

        w, h = self.width, self.height
        cx = self.left + w / 2
        cy = self.top + h / 2
        pos = self._screen_to_world(cx, cy, z=-50)

        # Update background
        self._bg_mesh.geometry = gfx.plane_geometry(w, h)
        self._bg_mesh.local.position = pos

        # Update frame
        self._frame_mesh.geometry = create_line_rectangle(w, h)
        self._frame_mesh.local.position = pos
