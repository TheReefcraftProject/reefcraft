# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Popup menu control: an icon button that opens a transient menu overlay."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from reefcraft.ui.control import Control
from reefcraft.ui.icon_button import IconButton
from reefcraft.ui.theme import Theme


class PopupMenuControl(Control):
    """A compact control that shows a popup menu when clicked.

    - Renders a small icon button (e.g., plus icon)
    - On click, shows an overlay menu with a vertical list of items
    - Tracks hover highlight and calls `on_select(label)` on pointer up
    - Hides automatically after selection or when toggled again
    """

    def __init__(
        self,
        context,
        *,
        icon: str = "add.png",
        width: int = 24,
        height: int = 24,
        items: Iterable[str] | None = None,
        on_select: Callable[[str], None] | None = None,
        theme: Theme | None = None,
        show_frame: bool = True,
    ) -> None:
        super().__init__(context=context, width=width, height=height, left=0, top=0, theme=theme)
        self._items: list[str] = list(items or [])
        self._on_select = on_select
        self._expanded: bool = False
        self._item_height: int = 22
        self._menu_width: int = 160
        self._margin: int = 4
        self._show_frame: bool = show_frame

        # The launcher button
        self._button = IconButton(
            context=context,
            icon=icon,
            width=width,
            height=height,
            toggle=False,
            on_click=self._on_button_click,
            normal_tint=(0.0, 0.5),
            hover_tint=(0.0, 1.0),
            pressed_tint=(0.0, 1.5),
        )

        # Create menu item buttons (initially hidden)
        self._menu_buttons: list[Control] = []
        for item in self._items:
            # Create a simple button-like control for each menu item
            menu_item = self._create_menu_item(item)
            menu_item.hide()  # Start hidden
            self._menu_buttons.append(menu_item)

    def _create_menu_item(self, label: str) -> Control:
        """Create a menu item control."""
        from reefcraft.ui.button import Button
        
        # Create a button for each menu item
        btn = Button(
            context=self.context,
            label=label,
            width=self._menu_width,
            height=self._item_height,
            on_click=lambda l=label: self._on_item_click(l),
        )
        return btn

    # Layout update ---------------------------------------------------------
    def _update_visuals(self) -> None:  # noqa: D401
        # Position the launcher at this control's position
        self._button.left = self.left
        self._button.top = self.top

        # Position menu items
        if self._expanded:
            left_px = self.left + self.width + 6  # 6px gap to the right
            top_px = self.top
            
            for i, menu_item in enumerate(self._menu_buttons):
                menu_item.left = left_px
                menu_item.top = top_px + i * (self._item_height + 2)
                menu_item._update_visuals()

    # Popup management ------------------------------------------------------
    def set_items(self, items: Iterable[str]) -> None:
        self._items = list(items or [])
        if self._expanded:
            self._hide_menu()

    def _on_button_click(self) -> None:
        """Handle button click - toggle menu state."""
        if self._expanded:
            self._hide_menu()
        else:
            self._show_menu()

    def _show_menu(self) -> None:
        """Show the popup menu."""
        if not self._items or self._expanded:
            return

        self._expanded = True
        
        # Show all menu items
        for menu_item in self._menu_buttons:
            menu_item.show()
        
        self._update_visuals()

    def _hide_menu(self) -> None:
        """Hide the popup menu."""
        if not self._expanded:
            return

        self._expanded = False
        
        # Hide all menu items
        for menu_item in self._menu_buttons:
            menu_item.hide()
        
        self._update_visuals()

    def _on_item_click(self, value: str) -> None:
        """Handle menu item selection."""
        if self._on_select:
            self._on_select(value)
        self._hide_menu()


