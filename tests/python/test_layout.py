import pytest

from reefcraft.ui.layout import Alignment, Layout, LayoutDirection, Widget


def test_single_widget_vertical() -> None:
    w = Widget(top=0, left=0, width=100, height=20)
    layout = Layout(direction=LayoutDirection.VERTICAL, widgets=[w], spacing=10, margin=5)
    assert w.top == 5
    assert layout.height == 25  # height of widget + margin
    assert layout.width == 100


def test_two_widgets_vertical() -> None:
    w1 = Widget(width=100, height=20)
    w2 = Widget(width=120, height=30)
    layout = Layout(direction=LayoutDirection.VERTICAL, widgets=[w1, w2], spacing=10, margin=5)
    assert w1.top == 5
    assert w2.top == 5 + 20 + 10
    assert layout.height == 5 + 20 + 10 + 30
    assert layout.width == 120


def test_alignment_center() -> None:
    w = Widget(top=0, left=0, width=50, height=20)
    layout = Layout(direction=LayoutDirection.VERTICAL, widgets=[w], spacing=10, margin=0, alignment=Alignment.CENTER)
    assert w.left == (layout.width - w.width) // 2


def test_alignment_end() -> None:
    w = Widget(top=0, left=0, width=50, height=20)
    layout = Layout(direction=LayoutDirection.VERTICAL, widgets=[w], spacing=10, margin=0, alignment=Alignment.END)
    assert w.left == layout.width - w.width
