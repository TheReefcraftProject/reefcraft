import pytest

from reefcraft.ui.list import Alignment, Layout, LayoutDirection
from reefcraft.ui.control import Control
from reefcraft.ui.ui_context import UIContext


class DummyCanvas:
    def __init__(self, size=(800, 600)) -> None:
        self._size = size

    def get_logical_size(self):  # noqa: D401 - simple dummy
        return self._size


def test_single_widget_vertical() -> None:
    ctx = UIContext(canvas=DummyCanvas())
    w = Control(context=ctx, top=0, left=0, width=100, height=20)
    layout = Layout(context=ctx, direction=LayoutDirection.VERTICAL, controls=[w], spacing=10, margin=5)
    assert w.top == 5
    assert layout.height == 30  # 20 height + 5 top + 5 bottom


def test_two_widgets_vertical() -> None:
    ctx = UIContext(canvas=DummyCanvas())
    w1 = Control(context=ctx, width=100, height=20)
    w2 = Control(context=ctx, width=120, height=30)
    layout = Layout(context=ctx, direction=LayoutDirection.VERTICAL, controls=[w1, w2], spacing=10, margin=5)
    assert w1.top == 5
    assert w2.top == 5 + 20 + 10
    assert layout.height == 5 + 20 + 10 + 30 + 5  # top + w1 + spacing + w2 + bottom


def test_alignment_center() -> None:
    ctx = UIContext(canvas=DummyCanvas())
    w = Control(context=ctx, top=0, left=0, width=50, height=20)
    layout = Layout(context=ctx, direction=LayoutDirection.VERTICAL, controls=[w], spacing=10, margin=0, alignment=Alignment.CENTER)
    assert w.left == (layout.width - w.width) // 2


def test_alignment_end() -> None:
    ctx = UIContext(canvas=DummyCanvas())
    w = Control(context=ctx, top=0, left=0, width=50, height=20)
    layout = Layout(context=ctx, direction=LayoutDirection.VERTICAL, controls=[w], spacing=10, margin=0, alignment=Alignment.END)
    assert w.left == layout.width - w.width


def test_nested_layout_geometry() -> None:
    ctx = UIContext(canvas=DummyCanvas())
    # Build widget hierarchy with explicit spacing = 10
    layout = Layout(
        context=ctx,
        controls=[
            Layout(
                context=ctx,
                controls=[
                    Control(context=ctx, width=20, height=20),  # "P"
                    Control(context=ctx, width=20, height=20),  # "X"
                ],
                direction=LayoutDirection.HORIZONTAL,
                spacing=10,
            ),
            Layout(
                context=ctx,
                controls=[
                    Control(context=ctx, width=250, height=20),
                    Control(context=ctx, width=250, height=20),
                    Control(context=ctx, width=250, height=20),
                    Control(context=ctx, width=250, height=20),
                    Control(context=ctx, width=250, height=20),
                ],
                direction=LayoutDirection.VERTICAL,
                spacing=10,
            ),
        ],
        direction=LayoutDirection.VERTICAL,
        spacing=10,
    )

    # Access nested layouts
    row = layout.controls[0]
    column = layout.controls[1]

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


def test_nested_layout_margins() -> None:
    ctx = UIContext(canvas=DummyCanvas())
    # Outer layout with margin=10
    outer_layout = Layout(
        context=ctx,
        controls=[
            Layout(
                context=ctx,
                controls=[Control(context=ctx, width=20, height=20)],
                direction=LayoutDirection.HORIZONTAL,
                margin=5,  # Inner margin
            ),
        ],
        direction=LayoutDirection.VERTICAL,
        margin=10,
    )

    # Access inner layout and widget
    inner_layout = outer_layout.controls[0]
    inner_widget = inner_layout.widgets[0]

    # Outer layout starts at (0, 0) but margin shifts inner layout by (10, 10)
    assert inner_layout.left == 10
    assert inner_layout.top == 10

    # Inner layout has margin of 5, so widget is offset by (5, 5) from inner layout
    assert inner_widget.left == 10 + 5  # = 15
    assert inner_widget.top == 10 + 5  # = 15


def test_horizontal_layout_bounds() -> None:
    ctx = UIContext(canvas=DummyCanvas())
    layout = Layout(
        context=ctx,
        direction=LayoutDirection.HORIZONTAL,
        spacing=2,
        margin=2,
    )
    layout.add_control(Control(context=ctx, width=20, height=20))
    layout.add_control(Control(context=ctx, width=100, height=20))
    layout.add_control(Control(context=ctx, width=50, height=20))

    # Total width = left margin + widths + spacing between + right margin
    expected_width = 2 + 20 + 2 + 100 + 2 + 50 + 2
    assert layout.width == expected_width, f"Expected {expected_width}, got {layout.width}"
