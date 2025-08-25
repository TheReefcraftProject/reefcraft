# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Theme system for consistent UI styling across the Reefcraft application.

This module provides the Theme class that defines the visual appearance
and styling for all UI controls in the Reefcraft application. The theme
system ensures consistent colors, fonts, and visual elements across
the entire user interface.

The Theme provides:
- Color scheme for different UI states (normal, hover, disabled)
- Typography settings for text rendering
- Border and outline styling
- Group and section visual organization
- Consistent visual hierarchy

The theme uses a dark color scheme optimized for:
- Scientific visualization and simulation display
- Long-term viewing comfort
- High contrast for readability
- Professional appearance
"""

from dataclasses import dataclass


@dataclass
class Theme:
    """Theme configuration for consistent UI styling.

    The Theme class defines all visual styling parameters used
    throughout the Reefcraft UI system. It provides a centralized
    way to manage colors, fonts, borders, and other visual
    properties for consistent user experience.

    Key features:
    - Comprehensive color scheme for all UI states
    - Typography configuration for text elements
    - Border and outline styling options
    - Group and section visual organization
    - Dark theme optimized for scientific visualization

    The color scheme is designed for:
    - High contrast and readability
    - Professional scientific appearance
    - Long-term viewing comfort
    - Consistent visual hierarchy

    Attributes:
        color: Primary background color for UI controls
        disabled_color: Background color for disabled controls
        hover_color: Background color for hover state
        highlight_color: Accent color for highlights and selections
        border_color: Color for control borders
        border_thickness: Thickness of borders in pixels
        text_color: Primary text color
        disabled_text_color: Text color for disabled controls
        font_size: Base font size in pixels
        font_name: Font family name (None for system default)
        window_color: Main window background color
        outline_color: Color for section outlines and dividers
        group_header_font_size: Font size for group headers
        group_header_font_color: Text color for group headers
        group_color: Background color for group containers
    """

    # Primary UI colors
    color: str = "#0F0F3D"  # Dark blue-gray for controls
    disabled_color: str = "#0F0F3D"  # Same as normal for disabled
    hover_color: str = "#1D1D6E"  # Lighter blue-gray for hover
    highlight_color: str = "#45CDF7"  # Bright cyan for highlights

    # Border and outline styling
    border_color: str = "#000000"  # Black borders
    border_thickness: float = 1.0  # Border thickness in pixels

    # Typography colors
    text_color: str = "#ffffff"  # White text for contrast
    disabled_text_color: str = "#808080"  # Gray text for disabled

    # Font configuration
    font_size: int = 12  # Base font size in pixels
    font_name: str | None = None  # Font family (None = system default)

    # Window and container colors
    window_color: str = "#08080A"  # Very dark background
    outline_color: str = "#2C4F59"  # Dark teal for outlines

    # Group and section styling
    group_header_font_size: int = 14  # Larger font for headers
    group_header_font_color: str = "#ffffff"  # White text for headers
    group_color: str = "#101013"  # Dark background for groups
