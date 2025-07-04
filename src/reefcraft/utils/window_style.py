# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

import sys

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    from pathlib import Path
    from typing import Union

    # import dearpygui.dearpygui as gui

    def apply_dark_titlebar_and_icon(window_title: str, icon_path: str | Path) -> None:
        icon_path = Path(icon_path)

        hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
        print(f"[DEBUG] HWND for '{window_title}':", hwnd)
        # if not hwnd:
        # gui.set_frame_callback(gui.get_frame_count() + 1, _apply)
        # return

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
        print("[DEBUG] Dark title bar applied")

        # Attempt to set window icon
        if icon_path.exists():
            print(f"[DEBUG] Icon path exists: {icon_path.resolve()}")
            hIcon = ctypes.windll.user32.LoadImageW(None, str(icon_path.resolve()), 1, 0, 0, 0x00000010)
            print("[DEBUG] hIcon loaded:", hIcon)
            if hIcon:
                ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, hIcon)  # ICON_SMALL
                ctypes.windll.user32.SendMessageW(hwnd, 0x80, 1, hIcon)  # ICON_BIG
                print("[DEBUG] Window icon set successfully")
            else:
                print("[ERROR] Failed to load icon with LoadImageW")
        else:
            print("[ERROR] Icon path does not exist:", icon_path)
else:

    def apply_dark_titlebar_and_icon(window_title: str, icon_path: str) -> None:
        pass
