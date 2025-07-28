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
    ) -> None:
        """Create a simple label."""
        super().__init__(left=left, top=top, width=width, height=height, theme=theme)

        self.panel = panel
        self.align = align
        self.text_source: str | Callable[[], str] = text
        self.text_string: str = self._evaluate_text()

        self._text_material = gfx.TextMaterial(color=self.theme.text_color)
        self._text = gfx.Text(
            self.text_string,
            material=self._text_material,
            screen_space=True,
            font_size=self.theme.font_size,
        )

        self.panel.scene.add(self._text)
        self._update_visuals()

        # Only register callback if text is dynamic
        if callable(self.text_source):
            self.panel.renderer.add_event_handler(self._update_text_pre_render, "before_render")
            logger.info("-> Added event handler for callable text update")

    def _evaluate_text(self) -> str:
        return self.text_source() if callable(self.text_source) else self.text_source

    def _update_text_pre_render(self, _event: object | None = None) -> None:
        new_text = self._evaluate_text()
        if new_text != self.text_string:
            self.text_string = new_text
            self._text.set_text(new_text)
            self._update_visuals()

    def _update_visuals(self) -> None:
        # Set the anchor for alignment
        match self.align:
            case TextAlign.LEFT:
                anchor = "middle-right"
            case TextAlign.RIGHT:
                anchor = "middle-left"
            case _:
                anchor = "middle-center"

        self._text.anchor = anchor
        self._text.local.position = self._screen_to_world(
            self.left + self.width / 2,
            self.top + self.height / 2,
            -1,
        )
