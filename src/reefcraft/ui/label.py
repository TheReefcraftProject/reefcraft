# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Label control for displaying static or dynamic text with alignment.

This module provides the Label class that creates text display controls
for the Reefcraft UI. The Label supports both static text and dynamic
text that updates automatically through callable functions.

The Label provides:
- Static text display with customizable alignment
- Dynamic text updates through callable functions
- Multiple text alignment options (left, center, right)
- Theme integration for consistent styling
- Automatic text positioning and layout management
- Screen-space rendering for consistent appearance

Labels are commonly used for:
- Section headers and titles
- Status information and metrics
- Descriptive text for UI elements
- Dynamic content that updates during simulation
"""

from collections.abc import Callable
from enum import Enum

import pygfx as gfx

from reefcraft.ui.control import Control
from reefcraft.ui.theme import Theme
from reefcraft.ui.ui_context import UIContext
from reefcraft.utils.logger import logger


class TextAlign(Enum):
    """Alignment options for text labels.

    Defines how text is positioned within the label's boundaries.
    Each alignment option provides different visual positioning
    suitable for different UI layout needs.

    Attributes:
        LEFT: Text is aligned to the left edge of the label
        CENTER: Text is centered within the label boundaries
        RIGHT: Text is aligned to the right edge of the label
    """

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Label(Control):
    """A non-interactive UI label control with text alignment and optional dynamic updates.

    The Label class provides a simple text display control that can show
    either static text or dynamically updated text through callable functions.
    It automatically handles text positioning, alignment, and visual updates.

    Key features:
    - Static or dynamic text content
    - Configurable text alignment (left, center, right)
    - Theme-based styling and colors
    - Automatic text positioning and updates
    - Screen-space rendering for consistent appearance

    Dynamic text labels automatically update their content before each
    render cycle, making them ideal for displaying real-time information
    like simulation metrics, status updates, or time displays.

    Attributes:
        context: UI context for rendering and event handling
        align: Text alignment within the label boundaries
        text_source: Source of text content (string or callable)
        text_string: Current displayed text string
        _text_material: Material for text rendering
        _text: pygfx Text object for display
    """

    def __init__(
        self,
        context: UIContext,
        *,
        left: int = 0,
        top: int = 0,
        width: int = 100,
        height: int = 24,
        text: str | Callable[[], str],
        align: TextAlign = TextAlign.CENTER,
        theme: Theme | None = None,
        font_size: int | None = None,
        font_color: str | None = None,
    ) -> None:
        """Create a label with static or callable text and alignment.

        Initializes a label with the specified text content and alignment.
        Sets up the text rendering with appropriate materials and positioning.
        If dynamic text is provided, sets up automatic update handling.

        Args:
            context: UI context for rendering and event handling
            left: Left position in pixels from layout origin
            top: Top position in pixels from layout origin
            width: Width of the label in pixels
            height: Height of the label in pixels
            text: Text content (string) or callable function returning text
            align: Text alignment within the label boundaries
            theme: Optional theme object (uses default if None)
            font_size: Optional font size in pixels (uses theme default if None)
            font_color: Optional font color (uses theme default if None)
        """
        super().__init__(context, left=left, top=top, width=width, height=height, theme=theme)

        self.context = context
        self.align = align
        self.text_source: str | Callable[[], str] = text
        self.text_string: str = self._evaluate_text()

        # Create text material and text object
        self._text_material = gfx.TextMaterial(color=font_color or self.theme.text_color)
        self._text = gfx.Text(
            self.text_string,
            material=self._text_material,
            screen_space=True,
            font_size=font_size or self.theme.font_size,
        )

        # Add text to the scene and update visuals
        self.context.add(self._text)
        self._update_visuals()

        # Set up dynamic text updates if callable source is provided
        if callable(self.text_source):
            renderer = getattr(self.context, "renderer", None)
            if renderer is not None and hasattr(renderer, "add_event_handler"):
                renderer.add_event_handler(self._update_text_pre_render, "before_render")
                logger.info("-> Added event handler for callable text update")

    def _evaluate_text(self) -> str:
        """Evaluate the current text string from static or callable source.

        Determines the current text content by either returning the static
        string directly or calling the callable function to get the latest value.

        Returns:
            The current text string to display
        """
        return self.text_source() if callable(self.text_source) else self.text_source

    def _update_text_pre_render(self, _event: object | None = None) -> None:
        """Check and update text if the source has changed.

        This method is called before each render cycle when using
        dynamic text. It checks if the text content has changed and
        updates the display accordingly.

        Args:
            _event: Render event (unused)
        """
        new_text = self._evaluate_text()
        if new_text != self.text_string:
            self.text_string = new_text
            self._text.set_text(new_text)
            self._update_visuals()

    def _update_visuals(self) -> None:
        """Update label alignment and position in screen space.

        Positions the text within the label boundaries according to
        the specified alignment. The text is positioned in screen
        space coordinates for consistent appearance across different
        viewport sizes and zoom levels.
        """
        # Determine text anchor and x-position based on alignment
        match self.align:
            case TextAlign.LEFT:
                anchor = "middle-left"
                x = self.left
            case TextAlign.RIGHT:
                anchor = "middle-right"
                x = self.left + self.width
            case _:  # CENTER (default)
                anchor = "middle-center"
                x = self.left + self.width / 2

        # Calculate y-position (centered vertically)
        y = self.top + self.height / 2

        # Update text positioning and anchor
        self._text.anchor = anchor
        self._text.local.position = self.context.screen_to_world(x, y, z=-1)
