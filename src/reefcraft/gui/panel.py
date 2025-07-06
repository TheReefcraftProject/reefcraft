"""UI Panel overlay using Taichi GGUI."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported for type hints
    from collections.abc import Callable

    import taichi as ti


class Section:
    """A collapsible section inside a :class:`Panel`."""

    def __init__(self, title: str, builder: Callable[[ti.ui.Gui], None]) -> None:
        """Create a new section.

        Args:
            title: Header label for the section.
            builder: Callback used to populate the section's widgets.
        """
        self.title = title
        self.builder = builder
        self.open = True

    def draw(self, gui: ti.ui.Gui) -> None:
        """Render this section using ``gui``."""
        self.open = gui.checkbox(self.title, self.open)
        if self.open:
            self.builder(gui)


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

    def draw(self, window: ti.ui.Window, gui: ti.ui.Gui) -> None:
        """Render the panel and its sections."""
        win_w, win_h = window.get_window_shape()
        x = (win_w - self.margin - self.width) / win_w
        y = self.margin / win_h
        w = self.width / win_w
        h = (win_h - 2 * self.margin) / win_h
        with gui.sub_window("Panel", x, y, w, h):
            for section in self.sections:
                section.draw(gui)
