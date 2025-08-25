# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Cross-platform window styling utilities for customizing application appearance.

This module provides platform-specific functions for customizing the appearance
of application windows, including dark mode titlebar styling and custom icon
setting. The implementation is tailored for each platform to provide the best
possible user experience.

The window styling system provides:
- Dark mode titlebar support on Windows 10/11
- Custom application icon setting
- Cross-platform compatibility with graceful fallbacks
- Windows API integration for native styling
- Automatic Windows version detection for optimal compatibility

The module automatically detects the platform and provides appropriate
implementations, with full functionality on Windows and graceful stubs
on other platforms where native support may be limited.
"""

import sys
from pathlib import Path

from reefcraft.utils.logger import logger

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    def apply_dark_titlebar_and_icon(window_title: str, icon_path: str | Path) -> None:
        """Apply dark mode titlebar and custom icon to a Windows application window.

        This function customizes the appearance of a Windows application window
        by enabling dark mode titlebar styling and setting a custom application
        icon. It uses Windows API calls to achieve native integration with the
        Windows desktop environment.

        Key features:
        - Automatic Windows version detection for optimal compatibility
        - Dark mode titlebar for Windows 10 build 19041+ and Windows 11
        - Custom icon setting for both small and large icon sizes
        - Comprehensive error handling and logging
        - Native Windows API integration

        Args:
            window_title: The exact title of the window to customize
            icon_path: Path to the icon file (.ico format recommended)

        Note:
            The window must already exist and be visible for this function
            to work properly. The icon file should be in .ico format for
            best compatibility with Windows.

        Example:
            >>> from pathlib import Path
            >>> icon_file = Path("resources/icons/app.ico")
            >>> apply_dark_titlebar_and_icon("My Application", icon_file)

        Windows API Details:
            - Uses FindWindowW to locate the window by title
            - Uses DwmSetWindowAttribute for dark mode titlebar
            - Uses LoadImageW and SendMessageW for icon setting
        """
        icon_path = Path(icon_path)

        # Find the window handle by title
        hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
        logger.info(f"HWND for '{window_title}': {hwnd}")

        if not hwnd:
            logger.debug("Unable to find window handle for dark mode styling")
            return

        # Apply dark mode titlebar using DWM (Desktop Window Manager)
        _apply_dark_titlebar(hwnd)

        # Set custom application icon
        _set_window_icon(hwnd, icon_path)

    def _apply_dark_titlebar(hwnd: int) -> None:
        """Apply dark mode styling to the window titlebar.

        Uses the Windows Desktop Window Manager (DWM) API to enable
        dark mode titlebar styling. The specific attribute used depends
        on the Windows build number for maximum compatibility.

        Args:
            hwnd: Window handle obtained from FindWindowW

        Windows Version Support:
            - Windows 10 build 19041+: Uses DWMWA_USE_IMMERSIVE_DARK_MODE (20)
            - Earlier versions: Uses legacy attribute (19)
        """
        # Determine the correct attribute based on Windows build
        build = sys.getwindowsversion().build
        dwm_attribute = 20 if build >= 19041 else 19  # DWMWA_USE_IMMERSIVE_DARK_MODE

        # Enable dark mode titlebar
        dark_mode_flag = ctypes.c_int(1)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            ctypes.c_uint(dwm_attribute),
            ctypes.byref(dark_mode_flag),
            ctypes.sizeof(dark_mode_flag),
        )

        if result == 0:  # S_OK
            logger.debug("Dark mode titlebar applied successfully")
        else:
            logger.warning(f"Failed to apply dark mode titlebar, error code: {result}")

    def _set_window_icon(hwnd: int, icon_path: Path) -> None:
        """Set the custom application icon for the window.

        Loads an icon file and applies it to both the small (16x16) and
        large (32x32) icon slots for the window. This ensures the icon
        appears correctly in the titlebar, taskbar, and Alt+Tab switcher.

        Args:
            hwnd: Window handle obtained from FindWindowW
            icon_path: Path to the icon file (.ico format recommended)

        Icon Requirements:
            - .ico format is recommended for best compatibility
            - Should contain multiple sizes (16x16, 32x32, 48x48)
            - File must exist and be accessible
        """
        if not icon_path.exists():
            logger.error(f"Icon file does not exist: {icon_path}")
            return

        # Load the icon file using Windows API
        # LR_LOADFROMFILE (0x00000010) flag loads from file path
        hIcon = ctypes.windll.user32.LoadImageW(
            None,  # hInstance (NULL for file loading)
            str(icon_path.resolve()),  # Absolute path to icon file
            1,  # IMAGE_ICON
            0,  # Desired width (0 = default)
            0,  # Desired height (0 = default)
            0x00000010,  # LR_LOADFROMFILE flag
        )

        if hIcon:
            # Set both small (16x16) and large (32x32) icons
            # WM_SETICON (0x80) with ICON_SMALL (0) and ICON_BIG (1)
            ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, hIcon)  # Small icon
            ctypes.windll.user32.SendMessageW(hwnd, 0x80, 1, hIcon)  # Large icon
            logger.info("Window icon set successfully")
        else:
            error_code = ctypes.windll.kernel32.GetLastError()
            logger.error(f"Failed to load icon file: {icon_path}, error code: {error_code}")

else:
    # Non-Windows platforms: Provide stub implementation
    def apply_dark_titlebar_and_icon(window_title: str, icon_path: str | Path) -> None:
        """Stub implementation for non-Windows platforms.

        On non-Windows platforms, this function serves as a no-op stub
        to maintain cross-platform compatibility. Platform-specific
        window styling may be implemented in the future for macOS and Linux.

        Args:
            window_title: The window title (unused on non-Windows platforms)
            icon_path: Path to icon file (unused on non-Windows platforms)

        Note:
            This is a stub implementation. Native window styling support
            for macOS and Linux may be added in future versions.
        """
        logger.debug(f"Window styling not implemented for platform: {sys.platform}")
        # Future: Add platform-specific implementations for macOS/Linux
        pass
