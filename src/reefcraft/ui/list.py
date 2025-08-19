# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""List control for arranging child controls vertically or horizontally with optional background and frame.

This module provides the List class that creates layout containers for organizing
UI controls in the Reefcraft application. The List can arrange child controls
either vertically or horizontally with configurable spacing, margins, and alignment.

The List provides:
- Flexible layout direction (vertical or horizontal)
- Configurable spacing between child controls
- Margin control around the entire layout
- Cross-axis alignment options (start, center, end)
- Optional background and frame rendering
- Automatic layout updates when child controls change
- Change tracking and callback registration

Lists are commonly used for:
- Organizing related UI controls into sections
- Creating form layouts and control groups
- Building navigation menus and toolbars
- Arranging simulation controls and displays
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

import numpy as np
import pygfx as gfx

from reefcraft.ui.control import Control
from reefcraft.ui.theme import Theme

if TYPE_CHECKING:
    from reefcraft.ui.ui_context import UIContext


class LayoutDirection(Enum):
    """Layout direction: vertical (top-down) or horizontal (left-right).

    Defines how child controls are arranged within the List container.
    Each direction provides different layout behavior suitable for
    different UI organization needs.

    Attributes:
        VERTICAL: Controls are arranged from top to bottom
        HORIZONTAL: Controls are arranged from left to right
    """

    VERTICAL = auto()
    HORIZONTAL = auto()


class Alignment(Enum):
    """Control alignment within the cross-axis of the layout.

    Defines how child controls are positioned along the axis
    perpendicular to the layout direction. This allows for
    precise control over control positioning within the container.

    Attributes:
        START: Controls are aligned to the start of the cross-axis
        CENTER: Controls are centered along the cross-axis
        END: Controls are aligned to the end of the cross-axis
    """

    START = auto()
    CENTER = auto()
    END = auto()


class List(Control):
    """A layout container that arranges child controls with optional background and frame.

    The List class provides a flexible layout system for organizing
    UI controls in either vertical or horizontal arrangements. It
    automatically handles positioning, sizing, and layout updates
    when child controls change.

    Key features:
    - Configurable layout direction (vertical/horizontal)
    - Automatic child control positioning and sizing
    - Configurable spacing and margins
    - Cross-axis alignment control
    - Optional background and frame rendering
    - Change tracking and automatic relayout

    The List automatically sizes itself to contain all child controls
    and provides a clean interface for building complex UI layouts.
    Child controls are positioned sequentially along the primary axis
    with optional alignment along the cross-axis.

    Attributes:
        direction: Layout direction (vertical or horizontal)
        spacing: Space between child controls in pixels
        margin: Outer margin around the entire layout in pixels
        alignment: Cross-axis alignment of child controls
        background: Whether to show background and frame
        header: Optional header text for the list
        theme: Theme object for styling
        controls: List of child controls managed by this list
        _bg_mesh: Background mesh for visual styling
        _frame_mesh: Frame mesh for visual styling
        _layout_in_progress: Flag to prevent recursive layout calls
    """

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
        """Create a List Control that lays out the contained controls vertically or horizontally.

        Initializes a List container with the specified layout parameters.
        Sets up background and frame meshes, registers initial controls,
        and performs the initial layout calculation.

        Args:
            context: UI context for rendering and event handling
            controls: Optional list of initial child controls
            direction: Layout direction (vertical or horizontal)
            spacing: Space between child controls in pixels
            margin: Outer margin around the entire layout in pixels
            alignment: Cross-axis alignment of child controls
            background: Whether to show background and frame
            header: Optional header text for the list
            theme: Optional theme object (uses default if None)
        """
        super().__init__(context)

        # Store layout configuration
        self.direction = direction
        self.spacing = spacing
        self.margin = margin
        self.alignment = alignment
        self.background = background
        self.header = header
        self.theme = theme or Theme()

        # Create background and frame meshes
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

        # Set initial visibility based on background setting
        if self.background:
            self._bg_mesh.visible = True
            self._frame_mesh.visible = True
        else:
            self._bg_mesh.visible = False
            self._frame_mesh.visible = False

        # Initialize control management
        self._layout_in_progress = False
        self.controls: list[Control] = []

        # Add initial controls if provided
        if controls:
            for control in controls:
                self.add_control(control)

    def add_control(self, control: Control) -> None:
        """Append a control to the list and register for change tracking.

        Adds a new child control to the list and sets up change
        tracking so the layout automatically updates when the
        control's properties change.

        Args:
            control: The control to add to the list
        """
        self.controls.append(control)
        control.on_change(self._layout)
        self._layout()

    # Backwards-compat for tests expecting a 'widgets' attribute
    @property
    def widgets(self) -> list[Control]:
        """Alias for the list of child controls (legacy name: widgets).

        Returns:
            List of child controls managed by this list
        """
        return self.controls

    def set_spacing(self, spacing: int) -> None:
        """Set the space between controls and relayout.

        Updates the spacing between child controls and triggers
        a layout recalculation to reflect the new spacing.

        Args:
            spacing: New spacing value in pixels
        """
        self.spacing = spacing
        self._layout()

    def set_margin(self, margin: int) -> None:
        """Set the outer margin around the layout and relayout.

        Updates the outer margin around the entire layout and
        triggers a layout recalculation to reflect the new margin.

        Args:
            margin: New margin value in pixels
        """
        self.margin = margin
        self._layout()

    def set_alignment(self, alignment: Alignment) -> None:
        """Set control alignment along the cross-axis and relayout.

        Updates the cross-axis alignment of child controls and
        triggers a layout recalculation to reflect the new alignment.

        Args:
            alignment: New alignment setting
        """
        self.alignment = alignment
        self._layout()

    def relayout(self) -> None:
        """Public trigger for layout recomputation.

        Forces a complete layout recalculation. This is useful
        when external changes require the layout to be updated
        but the change tracking system hasn't detected them.
        """
        self._layout()

    def _layout(self) -> None:
        """Internal layout logic: positions widgets and sizes layout accordingly.

        Calculates the optimal size and position for the List container
        based on its child controls. Positions each child control
        sequentially along the primary axis and applies cross-axis
        alignment as specified.

        The layout algorithm:
        1. Calculates total size needed for all controls
        2. Positions controls sequentially with specified spacing
        3. Applies cross-axis alignment (start, center, end)
        4. Updates container dimensions to fit all controls
        5. Updates background and frame meshes
        """
        # Prevent recursive layout calls
        if self._layout_in_progress:
            return

        self._layout_in_progress = True

        try:
            offset = 0
            max_cross = 0

            # First pass: calculate total size needed
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

            # Remove extra spacing after last control
            if self.controls:
                offset -= self.spacing

            # Update container dimensions
            if self.direction == LayoutDirection.VERTICAL:
                self.height = offset + self.margin * 2
                self.width = max_cross + self.margin * 2
            else:
                self.width = offset + self.margin * 2
                self.height = max_cross + self.margin * 2

            # Second pass: apply cross-axis alignment
            for widget in self.controls:
                if self.direction == LayoutDirection.VERTICAL:
                    if self.alignment == Alignment.CENTER:
                        widget.left = self.left + self.margin + (self.width - 2 * self.margin - widget.width) // 2
                    elif self.alignment == Alignment.END:
                        widget.left = self.left + self.width - self.margin - widget.width
                    else:  # Alignment.START
                        widget.left = self.left + self.margin
                else:
                    if self.alignment == Alignment.CENTER:
                        widget.top = self.top + self.margin + (self.height - 2 * self.margin - widget.height) // 2
                    elif self.alignment == Alignment.END:
                        widget.top = self.top + self.height - self.margin - widget.height
                    else:  # Alignment.START
                        widget.top = self.top + self.margin

        finally:
            self._layout_in_progress = False

    def _update_visuals(self) -> None:
        """Update the background meshes as needed and show and hide as desired.

        Updates the visual appearance of the List container including
        background and frame meshes. Triggers a layout recalculation
        and updates mesh positions and geometries to match the current
        container dimensions.
        """
        # Perform layout calculation
        self._layout()

        # Update visibility based on background setting
        if self.background:
            self._bg_mesh.visible = True
            self._frame_mesh.visible = True
        else:
            self._bg_mesh.visible = False
            self._frame_mesh.visible = False

        # Calculate center position for meshes
        w, h = self.width, self.height
        cx = self.left + w / 2
        cy = self.top + h / 2
        pos = self.context.screen_to_world(cx, cy, z=-50)

        # Update background mesh
        self._bg_mesh.geometry = gfx.plane_geometry(w, h)
        self._bg_mesh.local.position = pos

        # Update frame mesh
        self._frame_mesh.geometry = create_line_rectangle(w, h)
        self._frame_mesh.local.position = pos


def create_line_rectangle(width: int, height: int) -> gfx.Geometry:
    """Utility for creating a rectangular line geometry for the frame.

    Creates a line-based rectangle geometry suitable for drawing
    frames around UI elements. The rectangle is centered at the origin
    and uses the specified dimensions.

    Args:
        width: Width of the rectangle in pixels
        height: Height of the rectangle in pixels

    Returns:
        A pygfx Geometry object representing the rectangle outline
    """
    points = np.array(
        [
            [-width / 2, -height / 2, 0],
            [+width / 2, -height / 2, 0],
            [+width / 2, +height / 2, 0],
            [-width / 2, +height / 2, 0],
            [-width / 2, -height / 2, 0],  # Close the rectangle
        ],
        dtype=np.float32,
    )
    return gfx.Geometry(positions=points)


# Backwards-compat alias for tests using `Layout`
Layout = List
