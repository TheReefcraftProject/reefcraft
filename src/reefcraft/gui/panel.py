"""UI Panel overlay using Dear PyGui."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from collections.abc import Callable

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
        self.header: int | str | None = None
        self.open = True

    def build(self, parent: int | str) -> None:
        """Create widgets for this section."""
        self.header = dpg.add_collapsing_header(label=self.title, default_open=self.open, parent=parent)
        with dpg.group(parent=self.header):
            self.builder()

    def update(self) -> None:
        """Refresh internal open state."""
        if self.header is not None:
            self.open = bool(dpg.get_item_state(self.header).get("open"))


class Panel:
    """Fixed side panel that holds collapsible sections."""

    def __init__(
        self, width: int = 300, margin: int = 10, *, side: str = "right"
    ) -> None:
        """Initialize the panel with width, margin, and pinned side."""
        self.width = width
        self.margin = margin
        if side not in ("left", "right"):
            raise ValueError("side must be 'left' or 'right'")
        self.side = side
        self.sections: list[Section] = []
        self.window_id = dpg.add_window(
            label="",
            no_title_bar=True,
            no_move=True,
            no_resize=True,
            no_scrollbar=True,
        )

    def register(self, section: Section) -> None:
        """Add a section to the panel."""
        section.build(self.window_id)
        self.sections.append(section)

    def draw(self) -> None:
        """Update the panel layout."""
        win_w, win_h = dpg.get_viewport_width(), dpg.get_viewport_height()
        x = self.margin if self.side == "left" else win_w - self.margin - self.width
        y = self.margin
        h = win_h - 2 * self.margin
        dpg.configure_item(self.window_id, pos=(x, y), width=self.width, height=h)
        for section in self.sections:
            section.update()
