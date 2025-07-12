"""Simple side panel implemented with pyimgui."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from collections.abc import Callable

import imgui


class Section:
    """A collapsible section in the panel."""

    def __init__(self, title: str, builder: Callable[[], None]) -> None:
        """Create a new section."""
        self.title = title
        self.builder = builder
        self.open = True

    def draw(self) -> None:
        """Draw the section if open."""
        opened, _ = imgui.collapsing_header(self.title, visible=True)
        if opened:
            self.builder()
        self.open = opened


class Panel:
    """Fixed side panel that holds collapsible :class:`Section` objects."""

    def __init__(self, width: int = 300, margin: int = 10, *, side: str = "right") -> None:
        """Initialize the panel geometry and placement."""
        if side not in ("left", "right"):
            raise ValueError("side must be 'left' or 'right'")
        self.width = width
        self.margin = margin
        self.side = side
        self.sections: list[Section] = []

    def register(self, section: Section) -> None:
        """Register a new section with the panel."""
        self.sections.append(section)

    def draw(self, win_w: int, win_h: int) -> None:
        """Render the panel and contained sections."""
        x = self.margin if self.side == "left" else win_w - self.margin - self.width
        y = self.margin
        h = win_h - 2 * self.margin
        imgui.set_next_window_position(x, y)
        imgui.set_next_window_size(self.width, h)
        imgui.begin(
            "panel",
            False,
            flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE,
        )
        for section in self.sections:
            section.draw()
        imgui.end()
