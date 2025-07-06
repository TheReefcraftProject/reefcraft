import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from reefcraft.gui.panel import Panel, Section
from reefcraft.gui.window import Window
from reefcraft.sim.engine import Engine


def test_section_builder_called_when_open() -> None:
    called = []

    def builder() -> None:
        called.append(True)

    with patch("reefcraft.gui.panel.dpg") as mdpg:
        mdpg.collapsing_header.return_value = "hdr"
        mdpg.is_item_open.return_value = True
        sec = Section("Test", builder)
        sec.draw()
        assert sec.open is True
        assert called == [True]

        mdpg.is_item_open.return_value = False
        sec.draw()
        assert sec.open is False
        assert called == [True]


def test_panel_draw_calls_sections() -> None:
    with patch("reefcraft.gui.panel.dpg") as mdpg:
        mdpg.get_viewport_width.return_value = 800
        mdpg.get_viewport_height.return_value = 600

        mdpg.window_calls = []
        from contextlib import contextmanager

        @contextmanager
        def dummy_window(**kwargs):
            mdpg.window_calls.append(kwargs)
            yield
        mdpg.window.side_effect = dummy_window
        mdpg.collapsing_header.return_value = "hdr"
        mdpg.is_item_open.return_value = True

        panel = Panel(width=300, margin=10)

        class DummySection:
            def __init__(self) -> None:
                self.calls = 0

            def draw(self) -> None:
                self.calls += 1

        sec = DummySection()
        panel.register(sec)
        panel.draw()

        assert sec.calls == 1
        assert len(mdpg.window_calls) == 1
        kw = mdpg.window_calls[0]
        x, y = kw["pos"]
        assert x == 800 - 10 - 300
        assert y == 10
        assert kw["width"] == 300
        assert kw["height"] == 600 - 20


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

        from contextlib import contextmanager

        @contextmanager
        def dummy_window(**kwargs):
            yield
        mdpg.window.side_effect = dummy_window
        mdpg.collapsing_header.return_value = "hdr"
        mdpg.is_item_open.return_value = True

        win = Window(engine, Path())
        assert len(win.panel.sections) == 2

        win.panel = MagicMock()
        win.update()
        win.panel.draw.assert_called_once()
        mdpg.render_dearpygui_frame.assert_called_once()

