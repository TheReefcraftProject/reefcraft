"""UI Panel overlay using Dear PyGui."""

from __future__ import annotations

from typing import Callable

import dearpygui.dearpygui as dpg


class Section:
    """A collapsible section inside a :class:`Panel`."""

    def __init__(self, title: str, builder: Callable[[], None]) -> None:
        """Create a new section.

        Args:
            title: Header label for the section.
            builder: Callback used to populate the section's widgets.
        """
        self.title = title
        self.builder = builder
        self.open = True

    def draw(self) -> None:
        """Render this section using Dear PyGui."""
        header = dpg.collapsing_header(label=self.title, default_open=self.open)
        self.open = dpg.is_item_open(header)
        if self.open:
            self.builder()


class Panel:
    """Fixed side panel that holds collapsible sections."""

    def __init__(self, width: int = 300, margin: int = 10) -> None:
        """Initialize the panel with width and margin."""
        self.width = width
        self.margin = margin
        self.sections: list[Section] = []

    def register(self, section: Section) -> None:
        """Add a section to the panel."""
        self.sections.append(section)

    def draw(self) -> None:
        """Render the panel and its sections."""
        win_w, win_h = dpg.get_viewport_width(), dpg.get_viewport_height()
        x = win_w - self.margin - self.width
        y = self.margin
        w = self.width
        h = win_h - 2 * self.margin
        with dpg.window(label="Panel", pos=(x, y), width=w, height=h, no_resize=True, no_move=True):
            for section in self.sections:
                section.draw()
