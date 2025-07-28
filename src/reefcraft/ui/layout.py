# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Manage auto-layout options for groups of widgets."""

from enum import Enum, auto

from reefcraft.ui.widget import Widget


class LayoutDirection(Enum):
    """Layout direction: vertical (top-down) or horizontal (left-right)."""

    VERTICAL = auto()
    HORIZONTAL = auto()


class Alignment(Enum):
    """Widget alignment within the cross-axis of the layout."""

    START = auto()
    CENTER = auto()
    END = auto()


class Layout(Widget):
    """A layout widget that arranges child widgets vertically or horizontally."""

    def __init__(
        self,
        widgets: list[Widget] | None = None,
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
        self.direction = direction
        self.spacing = spacing
        self.margin = margin
        self.alignment = alignment
        self.widgets: list[Widget] = []
        if widgets:
            for widget in widgets:
                self.add_widget(widget)

    def add_widget(self, widget: Widget) -> None:
        """Append a widget to the layout and register for change tracking."""
        self.widgets.append(widget)
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
        offset = self.margin
        max_cross = 0

        for widget in self.widgets:
            if self.direction == LayoutDirection.VERTICAL:
                widget.top = offset + self.top  # don't add margin again
                offset += widget.height + self.spacing
                max_cross = max(max_cross, widget.width)
            else:
                widget.left = offset + self.left  # don't add margin again
                offset += widget.width + self.spacing
                max_cross = max(max_cross, widget.height)

        # Remove trailing spacing
        main_size = offset - self.spacing if self.widgets else 0

        if self.direction == LayoutDirection.VERTICAL:
            self.height = main_size
            self.width = max_cross + 2 * self.margin
        else:
            self.width = main_size
            self.height = max_cross + 2 * self.margin

        # Cross-axis alignment
        for widget in self.widgets:
            if self.direction == LayoutDirection.VERTICAL:
                if self.alignment == Alignment.CENTER:
                    widget.left = self.left + self.margin + (self.width - 2 * self.margin - widget.width) // 2
                elif self.alignment == Alignment.END:
                    widget.left = self.left + self.margin + (self.width - 2 * self.margin - widget.width)
                else:
                    widget.left = self.left + self.margin
            else:
                if self.alignment == Alignment.CENTER:
                    widget.top = self.top + self.margin + (self.height - 2 * self.margin - widget.height) // 2
                elif self.alignment == Alignment.END:
                    widget.top = self.top + self.margin + (self.height - 2 * self.margin - widget.height)
                else:
                    widget.top = self.top + self.margin

    def _update_visuals(self) -> None:
        """Update child widget positions when this layout moves."""
        self._layout()
