# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Non-interactive text label widget with alignment support."""

from enum import Enum

import pygfx as gfx

from reefcraft.ui.panel import Panel
from reefcraft.ui.widget import Widget


class TextAlign(Enum):
    """Text alignment options for Label widget."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Label(Widget):
    """Non-interactive text label with optional alignment."""

    def __init__(
        self,
        panel: Panel,
        *,
        text: str,
        left: int = 0,
        top: int = 0,
        width: int = 100,
        height: int = 20,
        align: TextAlign = TextAlign.CENTER,
    ) -> None:
        """Create a new text label widget."""
        super().__init__(top, left, width, height)
        self.panel = panel
        self.text = text
        self.align = align

        self._text_material = gfx.TextMaterial(color=self.theme.text_color)
        self._text = gfx.Text(
            text,
            material=self._text_material,
            screen_space=True,
            font_size=self.theme.font_size,
        )

        self.panel.scene.add(self._text)
        self._update_visuals()

    def set_text(self, text: str) -> None:
        """Update the label text."""
        self.text = text
        self._text.set_text(text)
        self._update_visuals()

    def set_align(self, align: TextAlign) -> None:
        """Update text alignment."""
        self.align = align
        self._update_visuals()

    def _update_visuals(self) -> None:
        """Update text position and alignment based on properties."""
        anchor_str = {
            TextAlign.LEFT: "middle-right",
            TextAlign.CENTER: "middle-center",
            TextAlign.RIGHT: "middle-left",
        }[self.align]

        self._text.anchor = anchor_str
        self._text.local.position = self._screen_to_world(
            self.left + self.width / 2,
            self.top + self.height / 2,
            -1,
        )
