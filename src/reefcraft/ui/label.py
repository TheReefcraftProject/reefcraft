# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Label widget for displaying static or dynamic text with alignment."""

from collections.abc import Callable
from enum import Enum

import pygfx as gfx

from reefcraft.ui.panel import Panel
from reefcraft.ui.theme import Theme
from reefcraft.ui.widget import Widget
from reefcraft.utils.logger import logger


class TextAlign(Enum):
    """Alignment options for text labels."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Label(Widget):
    """A non-interactive UI label widget with text alignment and optional dynamic updates."""

    def __init__(
        self,
        panel: Panel,
        *,
        text: str | Callable[[], str],
        left: int = 0,
        top: int = 0,
        width: int = 100,
        height: int = 20,
        align: TextAlign = TextAlign.CENTER,
        theme: Theme | None = None,
        font_size: int | None = None,
        font_color: str | None = None,
    ) -> None:
        """Create a label with static or callable text and alignment."""
        super().__init__(left=left, top=top, width=width, height=height, theme=theme)

        self.panel = panel
        self.align = align
        self.text_source: str | Callable[[], str] = text
        self.text_string: str = self._evaluate_text()

        self._text_material = gfx.TextMaterial(color=font_color or self.theme.text_color)
        self._text = gfx.Text(
            self.text_string,
            material=self._text_material,
            screen_space=True,
            font_size=font_size or self.theme.font_size,
        )

        self.panel.scene.add(self._text)
        self._update_visuals()

        if callable(self.text_source):
            self.panel.renderer.add_event_handler(self._update_text_pre_render, "before_render")
            logger.info("-> Added event handler for callable text update")

    def _evaluate_text(self) -> str:
        """Evaluate the current text string from static or callable source."""
        return self.text_source() if callable(self.text_source) else self.text_source

    def _update_text_pre_render(self, _event: object | None = None) -> None:
        """Check and update text if the source has changed."""
        new_text = self._evaluate_text()
        if new_text != self.text_string:
            self.text_string = new_text
            self._text.set_text(new_text)
            self._update_visuals()

    def _update_visuals(self) -> None:
        """Update label alignment and position in screen space."""
        match self.align:
            case TextAlign.LEFT:
                anchor = "middle-left"
                x = self.left
            case TextAlign.RIGHT:
                anchor = "middle-right"
                x = self.left + self.width
            case _:
                anchor = "middle-center"
                x = self.left + self.width / 2

        y = self.top + self.height / 2

        self._text.anchor = anchor
        self._text.local.position = self._screen_to_world(x, y, z=-1)
