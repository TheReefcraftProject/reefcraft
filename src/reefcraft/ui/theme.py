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
    highlight_color: str = "#45CDF7"
    border_color: str = "#000000"
    border_thickness: float = 1.0
    text_color: str = "#ffffff"
    disabled_text_color: str = "#808080"
    font_size: int = 12
    font_name: str | None = None
    window_color: str = "#08080A"
    outline_color: str = "#2C4F59"
    group_header_font_size: int = 14
    group_header_font_color: str = "#ffffff"
    group_color: str = "#101013"
