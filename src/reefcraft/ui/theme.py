# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""A table of theme data to be used by the UI."""

from dataclasses import dataclass


@dataclass
class Theme:
    """A simple data class to hold the theme, filled with defaults."""

    color: str = "#0F0F3D"
    disabled_color: str = "#0F0F3D"
    hover_color: str = "#1D1D6E"
    highlight_color: str = "#4343EC"
    border_color: str = "#000000"
    border_thickness: float = 1.0
    text_color: str = "#ffffff"
    disabled_text_color: str = "#808080"
    font_size: float = 12.0
    font_name: str | None = None
