# -----------------------------------------------------------------------------
# Copyright (c) 2025
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

import ctypes
import sys
from ctypes import wintypes

import dearpygui.dearpygui as gui


def enable_windows_dark_titlebar(window_title: str) -> None:
    """
    On Windows 10/11, enable the dark title bar for a Dear PyGui window
    whose title matches `window_title`.
    """
    if sys.platform != "win32":
        return

    def _apply() -> None:
        # Look up the window handle (HWND) by window title
        hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
        if not hwnd:
            return  # Window not yet ready; will retry next frame

        # Choose correct attribute index based on Windows build version
        build_number = sys.getwindowsversion().build
        dark_mode_attr = 20 if build_number >= 19041 else 19

        # Enable dark title bar
        enable_flag = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(wintypes.HWND(hwnd), ctypes.c_uint(dark_mode_attr), ctypes.byref(enable_flag), ctypes.sizeof(enable_flag))

    # Schedule _apply on the next GUI frame (after the OS window exists)
    next_frame_index = gui.get_frame_count() + 1
    gui.set_frame_callback(next_frame_index, _apply)
