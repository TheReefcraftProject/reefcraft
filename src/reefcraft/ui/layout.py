# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Manage auto-layout options for groups of widgets."""

from reefcraft.ui.widget import Widget


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
