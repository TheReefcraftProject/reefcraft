# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Handles application settings and configuration values."""


def load_settings() -> dict:
    """Return default configuration values for the application."""
    return {
        "theme": "dark",
        "default_growth_rate": 1.0,
    }
