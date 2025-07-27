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
        # ``offset`` tracks the position along the main axis.  It starts at the
        # layout's margin which represents a single outer padding at the
        # beginning of the axis.
        offset = self.margin
        max_cross = 0

        for widget in self.widgets:
            if self.direction == LayoutDirection.VERTICAL:
                widget.top = offset + self.top
                offset += widget.height + self.spacing
                max_cross = max(max_cross, widget.width)
            else:
                widget.left = offset + self.left
                offset += widget.width + self.spacing
                max_cross = max(max_cross, widget.height)

        # After looping ``offset`` contains an extra ``spacing`` that should not
        # be included after the final widget.  The size of the layout along the
        # main axis therefore subtracts the trailing spacing.  Only the initial
        # margin is included so the layout height/width matches expectations from
        # the tests.
        main_size = offset - self.spacing if self.widgets else 0

        if self.direction == LayoutDirection.VERTICAL:
            self.height = main_size
            self.width = max_cross
        else:
            self.width = main_size
            self.height = max_cross

        for widget in self.widgets:
            if self.direction == LayoutDirection.VERTICAL:
                if self.alignment == Alignment.CENTER:
                    widget.left = self.left + (self.width - widget.width) // 2
                elif self.alignment == Alignment.END:
                    widget.left = self.left + (self.width - widget.width)
                else:
                    widget.left = self.left
            else:
                if self.alignment == Alignment.CENTER:
                    widget.top = self.top + (self.height - widget.height) // 2
                elif self.alignment == Alignment.END:
                    widget.top = self.top + (self.height - widget.height)
                else:
                    widget.top = self.top

    def _update_visuals(self) -> None:
        """Update child widget positions when this layout moves."""
        self._layout()
