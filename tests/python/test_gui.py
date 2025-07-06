import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

if "dearpygui.dearpygui" not in sys.modules:
    pkg = types.ModuleType("dearpygui")
    dpg_mod = types.ModuleType("dearpygui.dearpygui")
    pkg.dearpygui = dpg_mod
    sys.modules["dearpygui"] = pkg
    sys.modules["dearpygui.dearpygui"] = dpg_mod

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from reefcraft.gui.panel import Panel, Section
from reefcraft.gui.window import Window
from reefcraft.sim.engine import Engine


def test_section_builder_called_when_open() -> None:
    called = []

    def builder() -> None:
        called.append(True)

    with patch("reefcraft.gui.panel.dpg") as mdpg:
        mdpg.add_collapsing_header.return_value = "hdr"
        mdpg.group.return_value.__enter__.return_value = None
        mdpg.get_item_state.return_value = {"open": True}
        sec = Section("Test", builder)
        sec.build("parent")
        assert called == [True]

        sec.update()
        assert sec.open is True

        mdpg.get_item_state.return_value = {"open": False}
        sec.update()
        assert sec.open is False


def test_panel_draw_updates_position() -> None:
    with patch("reefcraft.gui.panel.dpg") as mdpg:
        mdpg.get_viewport_width.return_value = 800
        mdpg.get_viewport_height.return_value = 600
        mdpg.add_window.return_value = "panel_win"
        mdpg.configure_item = MagicMock()
        mdpg.add_collapsing_header.return_value = "hdr"
        mdpg.group.return_value.__enter__.return_value = None
        mdpg.get_item_state.return_value = {"open": True}

        panel = Panel(width=300, margin=10)

        called = []

        def builder() -> None:
            called.append(True)

        panel.register(Section("Test", builder))

        assert called == [True]

        panel.draw()

        mdpg.configure_item.assert_called_with(
            "panel_win", pos=(800 - 10 - 300, 10), width=300, height=600 - 20
        )


def test_window_update_renders_panel() -> None:
    engine = Engine()

    with patch("reefcraft.gui.window.dpg") as mdpg, patch(
        "reefcraft.gui.panel.dpg", mdpg
    ), patch("reefcraft.utils.window_style.apply_dark_titlebar_and_icon"):
        mdpg.create_context.return_value = None
        mdpg.create_viewport.return_value = None
        mdpg.setup_dearpygui.return_value = None
        mdpg.show_viewport.return_value = None
        mdpg.render_dearpygui_frame.return_value = None
        mdpg.get_viewport_width.return_value = 1280
        mdpg.get_viewport_height.return_value = 1080
        mdpg.is_dearpygui_running.return_value = True

        mdpg.add_window.side_effect = ["panel_win", "canvas_window"]
        mdpg.set_primary_window.return_value = None
        mdpg.add_collapsing_header.return_value = "hdr"
        mdpg.group.return_value.__enter__.return_value = None
        mdpg.get_item_state.return_value = {"open": True}
        mdpg.configure_item.return_value = None
        mdpg.generate_uuid.return_value = "uuid"
        mdpg.add_dynamic_texture.return_value = None
        mdpg.add_image.return_value = "canvas_image"

        win = Window(engine, Path())
        assert len(win.panel.sections) == 2

        win.panel.draw = MagicMock()
        win.update()
        win.panel.draw.assert_called_once()
        mdpg.configure_item.assert_any_call(
            "canvas_window", pos=(0, 0), width=1280, height=1080
        )
        mdpg.configure_item.assert_any_call(
            "canvas_image", width=1280, height=1080
        )
        mdpg.render_dearpygui_frame.assert_called_once()

