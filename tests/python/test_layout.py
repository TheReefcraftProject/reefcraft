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


def test_nested_layout_geometry() -> None:
    # Build widget hierarchy
    layout = Layout(
        [
            Layout(
                [
                    Widget(width=20, height=20),  # "P"
                    Widget(width=20, height=20),  # "X"
                ],
                direction=LayoutDirection.HORIZONTAL,
            ),
            Layout(
                [
                    Widget(width=250, height=20),
                    Widget(width=250, height=20),
                    Widget(width=250, height=20),
                    Widget(width=250, height=20),
                    Widget(width=250, height=20),
                ],
                direction=LayoutDirection.VERTICAL,
            ),
        ],
        direction=LayoutDirection.VERTICAL,
    )

    # Trigger layout calculations
    # layout.update_geometry(left=0, top=0)

    # Access inner layouts
    row = layout.widgets[0]  # Horizontal row with 2 widgets
    column = layout.widgets[1]  # Vertical column with 5 widgets

    # Horizontal layout starts at (0, 0), lays out left to right
    w0, w1 = row.widgets
    assert w0.left == 0
    assert w0.top == 0
    assert w1.left == 20
    assert w1.top == 0

    # Vertical layout starts at (0, 20), stacks downward
    v0, v1, v2, v3, v4 = column.widgets
    assert v0.left == 0
    assert v0.top == 20
    assert v1.top == 40
    assert v2.top == 60
    assert v3.top == 80
    assert v4.top == 100
    assert all(w.left == 0 for w in [v0, v1, v2, v3, v4])
