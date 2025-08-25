# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Popup menu control: an icon button that opens a transient menu overlay.

This module provides the PopupMenuControl class that creates a compact control
with an icon button that, when clicked, displays a popup menu with selectable
items. The popup menu automatically positions itself relative to the button
and handles item selection callbacks.

The PopupMenuControl provides:
- A compact icon button as the menu trigger
- A popup overlay menu with vertical item layout
- Automatic positioning and sizing of menu items
- Item selection callbacks with automatic menu hiding
- Theme integration and consistent styling
- Mouse event handling and visual feedback
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from reefcraft.ui.control import Control
from reefcraft.ui.icon_button import IconButton

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from reefcraft.ui.theme import Theme
    from reefcraft.ui.ui_context import UIContext


class PopupMenuControl(Control):
    """A compact control that shows a popup menu when clicked.

    The PopupMenuControl combines an icon button with a transient popup menu
    overlay. When the icon button is clicked, a menu appears to the right
    of the button with a list of selectable items. The menu automatically
    hides after selection or when the button is clicked again.

    Key features:
    - Compact icon button as the menu trigger
    - Popup overlay menu with automatic positioning
    - Vertical list layout for menu items
    - Automatic menu hiding after selection
    - Theme integration and consistent styling
    - Mouse event handling and visual feedback

    The control automatically manages:
    - Menu positioning relative to the button
    - Menu item creation and layout
    - Show/hide state transitions
    - Item selection callbacks

    Attributes:
        context: UI context for rendering and event handling
        _items: List of menu item labels
        _on_select: Callback function for item selection
        _expanded: Whether the popup menu is currently visible
        _item_height: Height of each menu item in pixels
        _menu_width: Width of the popup menu in pixels
        _margin: Margin spacing between elements in pixels
        _show_frame: Whether to show a frame around the menu
        _button: The icon button that triggers the menu
        _menu_buttons: List of menu item button controls
    """

    def __init__(
        self,
        context: UIContext,
        *,
        icon: str = "add.png",
        width: int = 24,
        height: int = 24,
        items: Iterable[str] | None = None,
        on_select: Callable[[str], None] | None = None,
        theme: Theme | None = None,
        show_frame: bool = True,
    ) -> None:
        """Initialize the popup menu control.

        Creates a new popup menu control with the specified icon button and
        menu items. The control starts with the menu hidden and ready for
        interaction.

        Args:
            context: UI context for rendering and event handling
            icon: Filename of the icon to display on the button
            width: Width of the control in pixels
            height: Height of the control in pixels
            items: Optional iterable of menu item labels
            on_select: Optional callback function called when an item is selected
            theme: Optional theme object for styling
            show_frame: Whether to show a frame around the popup menu
        """
        super().__init__(context=context, width=width, height=height, left=0, top=0, theme=theme)
        self._items: list[str] = list(items or [])
        self._on_select = on_select
        self._expanded: bool = False
        self._item_height: int = 22
        self._menu_width: int = 160
        self._margin: int = 4
        self._show_frame: bool = show_frame

        # Create the launcher button
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
            menu_item = self._create_menu_item(item)
            menu_item.hide()  # Start hidden
            self._menu_buttons.append(menu_item)

    def _create_menu_item(self, label: str) -> Control:
        """Create a menu item control.

        Creates a button control for each menu item with appropriate styling
        and click handling. The button is configured to call the item selection
        callback when clicked.

        Args:
            label: Text label for the menu item

        Returns:
            A Control instance representing the menu item
        """
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

    def _update_visuals(self) -> None:
        """Update the visual positioning of all elements.

        Positions the launcher button and menu items based on the current
        control position and expansion state. This method is called whenever
        the control's position changes or the menu state changes.
        """
        # Position the launcher at this control's position
        self._button.left = self.left
        self._button.top = self.top

        # Position menu items if expanded
        if self._expanded:
            left_px = self.left + self.width + 6  # 6px gap to the right
            top_px = self.top

            for i, menu_item in enumerate(self._menu_buttons):
                menu_item.left = left_px
                menu_item.top = top_px + i * (self._item_height + 2)
                menu_item._update_visuals()

    def set_items(self, items: Iterable[str]) -> None:
        """Update the menu items.

        Replaces the current menu items with new ones. If the menu is
        currently expanded, it will be automatically hidden.

        Args:
            items: New iterable of menu item labels
        """
        self._items = list(items or [])
        if self._expanded:
            self._hide_menu()

    def _on_button_click(self) -> None:
        """Handle button click - toggle menu state.

        Called when the icon button is clicked. Toggles between showing
        and hiding the popup menu.
        """
        if self._expanded:
            self._hide_menu()
        else:
            self._show_menu()

    def _show_menu(self) -> None:
        """Show the popup menu.

        Displays the popup menu with all menu items visible. The menu
        is positioned to the right of the button with appropriate spacing.
        """
        if not self._items or self._expanded:
            return

        self._expanded = True

        # Show all menu items
        for menu_item in self._menu_buttons:
            menu_item.show()

        self._update_visuals()

    def _hide_menu(self) -> None:
        """Hide the popup menu.

        Hides the popup menu and all menu items. This is called automatically
        after item selection or when the button is clicked again.
        """
        if not self._expanded:
            return

        self._expanded = False

        # Hide all menu items
        for menu_item in self._menu_buttons:
            menu_item.hide()

        self._update_visuals()

    def _on_item_click(self, value: str) -> None:
        """Handle menu item selection.

        Called when a menu item is clicked. Invokes the selection callback
        if one is provided and then automatically hides the menu.

        Args:
            value: The label of the selected menu item
        """
        if self._on_select:
            self._on_select(value)
        self._hide_menu()
