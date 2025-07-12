# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Helpers for customizing window appearance on different platforms."""

import sys

if sys.platform == "win32":
    def apply_dark_titlebar_and_icon(window_title: str, icon_path: str) -> None:  # pragma: no cover - platform specific
        """Placeholder for Windows window styling (no-op in tests)."""
        return
else:

    def apply_dark_titlebar_and_icon(window_title: str, icon_path: str) -> None:  # pragma: no cover - platform specific
        """Stub out for non-Windows platforms."""
        return
