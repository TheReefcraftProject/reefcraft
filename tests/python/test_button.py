import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from reefcraft.ui.button import Button, ButtonState


class DummyTarget:
    def __init__(self) -> None:
        self.captured = False

    def set_pointer_capture(self, pid: int, renderer: object) -> None:
        self.captured = True

    def has_pointer_capture(self, pid: int) -> bool:
        return self.captured

    def release_pointer_capture(self, pid: int) -> None:
        self.captured = False


class DummyEvent:
    def __init__(self) -> None:
        self.pointer_id = 1
        self.target = DummyTarget()


class DummyScene:
    def add(self, obj: object) -> None:
        pass


class DummyPanel:
    def __init__(self) -> None:
        self.scene = DummyScene()
        self.renderer = object()


def test_button_state_changes() -> None:
    panel = DummyPanel()
    btn = Button(panel, left=0, top=0, width=10, height=10, label="ok")
    event = DummyEvent()
    assert btn.state is ButtonState.NORMAL

    btn._on_enter(event)
    assert btn.state is ButtonState.HOVER

    btn._on_down(event)
    assert btn.state is ButtonState.PRESSED

    btn._on_up(event)
    assert btn.state is ButtonState.HOVER


def test_button_disabled() -> None:
    panel = DummyPanel()
    btn = Button(panel, left=0, top=0, width=10, height=10, enabled=False)
    event = DummyEvent()
    assert btn.state is ButtonState.DISABLED

    btn._on_enter(event)
    assert btn.state is ButtonState.DISABLED


class ClickButton(Button):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.clicked = False

    def on_click(self) -> None:
        self.clicked = True


def test_button_on_click() -> None:
    panel = DummyPanel()
    btn = ClickButton(panel, left=0, top=0, width=10, height=10)
    event = DummyEvent()
    btn._on_down(event)
    btn._on_up(event)
    assert btn.clicked
