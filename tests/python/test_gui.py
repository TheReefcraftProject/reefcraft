import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

if "taichi" not in sys.modules:
    def fake_field(*args: object, shape: tuple[int, ...] | None = None, **kwargs: object) -> object:
        class Dummy:
            def __init__(self, shape: tuple[int, ...] | None) -> None:
                self.shape = shape

        return Dummy(shape)

    def ndrange(*sizes: int) -> list[tuple[int, int, int]]:
        result = []
        for i in range(sizes[0]):
            for j in range(sizes[1]):
                for k in range(sizes[2]):
                    result.append((i, j, k))
        return result

    ui_stub = types.SimpleNamespace(Window=object, Gui=object, Scene=object, make_camera=lambda: object())

    def vector(values: object | None = None) -> object | None:
        return values

    vector.field = fake_field

    ti_stub = types.SimpleNamespace(
        ui=ui_stub,
        vulkan="vulkan",
        init=lambda arch=None: None,
        kernel=lambda f: f,
        Vector=vector,
        field=fake_field,
        f32=0.0,
        ijk=0,
        ndrange=ndrange,
        root=types.SimpleNamespace(pointer=lambda *a, **k: types.SimpleNamespace(dense=lambda *a, **k: types.SimpleNamespace(place=lambda *a, **k: None))),
    )
    sys.modules["taichi"] = ti_stub

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from reefcraft.gui.panel import Panel, Section
from reefcraft.gui.window import Window
from reefcraft.sim.engine import Engine
from reefcraft.sim.volume import Volume

Volume._fill_test_pattern = lambda self: None


def test_section_builder_called_when_open() -> None:
    called = []

    def builder(gui: object) -> None:
        called.append(True)

    class DummyGui:
        def __init__(self, checked: bool) -> None:
            self.checked = checked

        def checkbox(self, title: str, state: bool) -> bool:  # noqa: D401 - simple stub
            return self.checked

    gui = DummyGui(True)
    sec = Section("Test", builder)
    sec.draw(gui)
    assert sec.open is True
    assert called == [True]

    gui.checked = False
    sec.draw(gui)
    assert sec.open is False
    assert called == [True]


def test_panel_draw_calls_sections() -> None:
    class DummyWindow:
        def get_window_shape(self) -> tuple[int, int]:
            return (800, 600)

    class DummyGui:
        def __init__(self) -> None:
            self.sub_windows: list[tuple[str, float, float, float, float]] = []

        def __call__(self) -> "DummyGui":  # type: ignore[override]
            return self

        def checkbox(self, title: str, value: bool) -> bool:
            return value

        from contextlib import AbstractContextManager, contextmanager

        @contextmanager
        def sub_window(self, title: str, x: float, y: float, w: float, h: float) -> AbstractContextManager["DummyGui"]:
            self.sub_windows.append((title, x, y, w, h))
            yield self

    gui = DummyGui()
    window = DummyWindow()
    panel = Panel(width=300, margin=10)

    class DummySection:
        def __init__(self) -> None:
            self.calls = 0

        def draw(self, g: DummyGui) -> None:
            self.calls += 1

    sec = DummySection()
    panel.register(sec)
    panel.draw(window, gui)

    assert sec.calls == 1
    assert len(gui.sub_windows) == 1
    _, x, y, w, h = gui.sub_windows[0]
    assert x == (800 - 10 - 300) / 800
    assert y == 10 / 600
    assert w == 300 / 800
    assert h == (600 - 20) / 600


def test_window_update_renders_panel() -> None:
    engine = Engine()

    with patch("reefcraft.gui.window.ti") as mti, patch(
        "reefcraft.utils.window_style.apply_dark_titlebar_and_icon"
    ):
        dummy_window = MagicMock()
        dummy_canvas = MagicMock()
        dummy_gui = MagicMock()
        mti.vulkan = "vulkan"
        mti.init.return_value = None
        mti.ui.Window.return_value = dummy_window
        dummy_window.get_canvas.return_value = dummy_canvas
        dummy_window.get_gui.return_value = dummy_gui

        win = Window(engine, Path())
        assert len(win.panel.sections) == 2

        win.panel = MagicMock()
        win.update()
        dummy_canvas.set_background_color.assert_called_once_with((0.0, 0.0, 0.0))
        win.panel.draw.assert_called_once_with(dummy_window, dummy_gui)
        dummy_window.show.assert_called_once()

