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
    # Build widget hierarchy with explicit spacing = 10
    layout = Layout(
        [
            Layout(
                [
                    Widget(width=20, height=20),  # "P"
                    Widget(width=20, height=20),  # "X"
                ],
                direction=LayoutDirection.HORIZONTAL,
                spacing=10,
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
                spacing=10,
            ),
        ],
        direction=LayoutDirection.VERTICAL,
        spacing=10,
    )

    # Access nested layouts
    row = layout.widgets[0]
    column = layout.widgets[1]

    # Horizontal layout with 2 widgets, spacing = 10
    w0, w1 = row.widgets
    assert w0.left == 0
    assert w0.top == 0
    assert w1.left == 30  # w0.width + spacing = 20 + 10
    assert w1.top == 0

    # Vertical layout starts at top = 30 (row height 20 + spacing 10)
    v0, v1, v2, v3, v4 = column.widgets
    assert v0.top == 30
    assert v1.top == 30 + 20 + 10  # 60
    assert v2.top == 30 + 20 * 2 + 10 * 2  # 90
    assert v3.top == 30 + 20 * 3 + 10 * 3  # 120
    assert v4.top == 30 + 20 * 4 + 10 * 4  # 150
    assert all(w.left == 0 for w in [v0, v1, v2, v3, v4])
