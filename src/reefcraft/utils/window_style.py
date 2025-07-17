# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Helpers for customizing window appearance on different platforms."""

import sys

from reefcraft.reefcraft_logging import logger

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    from pathlib import Path

    def apply_dark_titlebar_and_icon(window_title: str, icon_path: str | Path) -> None:
        """Force the window to honor darkmode and set the icon."""
        icon_path = Path(icon_path)

        hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
        logger.debug("HWND for '{}': {}", window_title, hwnd)
        if not hwnd:
            logger.debug("Unable to find HWND for dark mode")
            return

        # Apply dark title bar
        build = sys.getwindowsversion().build
        attr = 20 if build >= 19041 else 19
        flag = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            ctypes.c_uint(attr),
            ctypes.byref(flag),
            ctypes.sizeof(flag),
        )
        logger.debug("Dark title bar applied")

        # Attempt to set window icon
        if icon_path.exists():
            logger.debug("Icon path exists: {}", icon_path.resolve())
            hIcon = ctypes.windll.user32.LoadImageW(None, str(icon_path.resolve()), 1, 0, 0, 0x00000010)
            logger.debug("hIcon loaded: {}", hIcon)
            if hIcon:
                ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, hIcon)  # ICON_SMALL
                ctypes.windll.user32.SendMessageW(hwnd, 0x80, 1, hIcon)  # ICON_BIG
                logger.debug("Window icon set successfully")
            else:
                logger.error("Failed to load icon with LoadImageW")
        else:
            logger.error("Icon path does not exist: {}", icon_path)
else:

    def apply_dark_titlebar_and_icon(window_title: str, icon_path: str) -> None:
        """Stub out for non-Windows platforms."""
        pass
