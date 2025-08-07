# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""List control for arranging child controls vertically or horizontally with optional background and frame."""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

import numpy as np
import pygfx as gfx

from reefcraft.ui.control import Control
from reefcraft.ui.theme import Theme
from reefcraft.utils.logger import logger

if TYPE_CHECKING:
    from reefcraft.ui.ui_context import UIContext


class LayoutDirection(Enum):
    """Layout direction: vertical (top-down) or horizontal (left-right)."""

    VERTICAL = auto()
    HORIZONTAL = auto()


class Alignment(Enum):
    """Control alignment within the cross-axis of the layout."""

    START = auto()
    CENTER = auto()
    END = auto()


class List(Control):
    """A layout container that arranges child controls with optional background and frame."""

    def __init__(
        self,
        context: UIContext,
        *,
        controls: list[Control] | None = None,
        direction: LayoutDirection = LayoutDirection.VERTICAL,
        spacing: int = 2,
        margin: int = 0,
        alignment: Alignment = Alignment.START,
        background: bool = False,
        header: str | None = None,
        theme: Theme | None = None,
    ) -> None:
        """Create a List Control that lays out the contained controls vertically or horizontally."""
        super().__init__(context)

        self.direction = direction
        self.spacing = spacing
        self.margin = margin
        self.alignment = alignment
        self.background = background
        self.header = header
        self.theme = theme or Theme()

        self._bg_mesh = gfx.Mesh(
            gfx.plane_geometry(1, 1),
            gfx.MeshBasicMaterial(color=self.theme.group_color),
        )
        self.context.add(self._bg_mesh)
        self._frame_mesh = gfx.Line(
            create_line_rectangle(1, 1),
            gfx.LineMaterial(color=self.theme.outline_color, thickness=1),
        )
        self.context.add(self._frame_mesh)
        if self.background:
            self._bg_mesh.visible = True
            self._frame_mesh.visible = True
        else:
            self._bg_mesh.visible = False
            self._frame_mesh.visible = False

        self._layout_in_progress = False
        self.controls: list[Control] = []

        if controls:
            for control in controls:
                self.add_control(control)

    def add_control(self, control: Control) -> None:
        """Append a control to the list and register for change tracking."""
        self.controls.append(control)
        control.on_change(self._layout)
        self._layout()

    def set_spacing(self, spacing: int) -> None:
        """Set the space between controls and relayout."""
        self.spacing = spacing
        self._layout()

    def set_margin(self, margin: int) -> None:
        """Set the outer margin around the layout and relayout."""
        self.margin = margin
        self._layout()

    def set_alignment(self, alignment: Alignment) -> None:
        """Set control alignment along the cross-axis and relayout."""
        self.alignment = alignment
        self._layout()

    def relayout(self) -> None:
        """Public trigger for layout recomputation."""
        self._layout()

    def _layout(self) -> None:
        """Internal layout logic: positions widgets and sizes layout accordingly."""
        if self._layout_in_progress:
            return

        self._layout_in_progress = True

        try:
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
                offset -= self.spacing

            if self.direction == LayoutDirection.VERTICAL:
                self.height = offset + self.margin * 2
                self.width = max_cross + self.margin * 2
            else:
                self.width = offset + self.margin * 2
                self.height = max_cross + self.margin * 2

            for widget in self.controls:
                if self.direction == LayoutDirection.VERTICAL:
                    if self.alignment == Alignment.CENTER:
                        widget.left = self.left + self.margin + (self.width - 2 * self.margin - widget.width) // 2
                    elif self.alignment == Alignment.END:
                        widget.left = self.left + self.width - self.margin - widget.width
                    else:
                        widget.left = self.left + self.margin
                else:
                    if self.alignment == Alignment.CENTER:
                        widget.top = self.top + self.margin + (self.height - 2 * self.margin - widget.height) // 2
                    elif self.alignment == Alignment.END:
                        widget.top = self.top + self.height - self.margin - widget.height
                    else:
                        widget.top = self.top + self.margin

        finally:
            self._layout_in_progress = False

    def _update_visuals(self) -> None:
        """Update the backgound meshes as needed and show and hide as desired."""
        self._layout()

        if self.background:
            self._bg_mesh.visible = True
            self._frame_mesh.visible = True
        else:
            self._bg_mesh.visible = False
            self._frame_mesh.visible = False

        w, h = self.width, self.height
        cx = self.left + w / 2
        cy = self.top + h / 2
        pos = self.context.screen_to_world(cx, cy, z=-50)

        self._bg_mesh.geometry = gfx.plane_geometry(w, h)
        self._bg_mesh.local.position = pos

        self._frame_mesh.geometry = create_line_rectangle(w, h)
        self._frame_mesh.local.position = pos


def create_line_rectangle(width: int, height: int) -> gfx.Geometry:
    """Utility for the frame around the background."""
    points = np.array(
        [
            [-width / 2, -height / 2, 0],
            [+width / 2, -height / 2, 0],
            [+width / 2, +height / 2, 0],
            [-width / 2, +height / 2, 0],
            [-width / 2, -height / 2, 0],
        ],
        dtype=np.float32,
    )
    return gfx.Geometry(positions=points)
