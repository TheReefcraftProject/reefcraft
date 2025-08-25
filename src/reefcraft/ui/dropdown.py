# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Dropdown menu control for selecting from a list of options.

This module provides the Dropdown class that creates an interactive
dropdown menu control for the Reefcraft UI. The dropdown displays
a list of selectable options and allows users to choose from them
through a simple click interface.

The Dropdown provides:
- A main button showing the currently selected option
- Expandable list of all available options
- Automatic positioning and layout management
- Selection callback system for handling user choices
- Theme integration for consistent styling
- Programmatic control for opening/closing

The dropdown automatically handles the visual state (expanded/collapsed)
and positions option buttons below the main button when expanded.
"""

from collections.abc import Callable

from reefcraft.ui.button import Button
from reefcraft.ui.control import Control
from reefcraft.ui.theme import Theme
from reefcraft.ui.ui_context import UIContext


class Dropdown(Control):
    """Dropdown control with selectable options.

    The Dropdown class creates an interactive dropdown menu that displays
    a list of options for user selection. It consists of a main button
    showing the current selection and a collapsible list of option buttons
    that appear below when the dropdown is expanded.

    The dropdown automatically manages:
    - Visual state (expanded/collapsed)
    - Option button positioning and visibility
    - Selection state and callback execution
    - Layout updates when properties change

    Key features:
    - Click to expand/collapse
    - Automatic option positioning
    - Selection callback system
    - Theme integration
    - Programmatic control

    Attributes:
        options: List of available options to choose from
        on_select: Callback function called when an option is selected
        selected: Currently selected option value
        expanded: Whether the dropdown is currently expanded
        button: Main button showing the current selection
        option_buttons: List of buttons for each option
    """

    def __init__(
        self,
        context: UIContext,
        *,
        left: int = 0,
        top: int = 0,
        width: int = 150,
        height: int = 24,
        options: list[str],
        on_select: Callable[[str], None],
        default: str = "",
        theme: Theme | None = None,
    ) -> None:
        """Create a dropdown menu.

        Initializes a dropdown with the specified options and creates
        the main button and option buttons. The dropdown starts in a
        collapsed state with the default option selected.

        Args:
            context: UI context for rendering and event handling
            left: Left position in pixels from layout origin
            top: Top position in pixels from layout origin
            width: Width of the dropdown in pixels
            height: Height of each button in pixels
            options: List of string options to choose from
            on_select: Function called when an option is selected
            default: Default selected option (uses first option if empty)
            theme: Optional theme object (uses default if None)
        """
        super().__init__(context, left=left, top=top, width=width, height=height, theme=theme)

        self.options = options
        self.on_select = on_select
        self.selected = default or options[0] if options else ""
        self.expanded = False

        # Create main button showing current selection
        self.button = Button(
            self.context,
            label=self.selected,
            width=self.width,
            height=self.height,
            on_click=self.toggle,
        )
        self.root.add(self.button.root)

        # Create option buttons for each available option
        self.option_buttons: list[Button] = []
        for i, opt in enumerate(options):
            btn = Button(
                self.context,
                label=opt,
                width=self.width,
                height=self.height,
                on_click=lambda opt=opt: self.select(opt),
            )
            btn.hide()  # Initially hidden
            self.option_buttons.append(btn)
            self.root.add(btn.root)

        # Initialize visual state
        self._update_visuals()

    def toggle(self) -> None:
        """Toggle dropdown open or closed.

        Switches the dropdown between expanded and collapsed states.
        When expanded, all option buttons become visible below the
        main button. When collapsed, only the main button is visible.
        """
        self.expanded = not self.expanded
        self._update_visuals()

    def select(self, value: str) -> None:
        """Select an option and close the menu.

        Updates the selected value, changes the main button label,
        calls the selection callback, and collapses the dropdown.

        Args:
            value: The selected option value
        """
        self.selected = value

        # Update the main button label
        self.button.set_label(value)

        # Call the selection callback
        self.on_select(value)

        # Collapse the dropdown
        self.expanded = False
        self._update_visuals()

    def close(self) -> None:
        """Programmatically close the dropdown.

        Collapses the dropdown menu without changing the selection.
        This is useful for closing the dropdown in response to
        external events (like clicking outside the dropdown).
        """
        self.expanded = False
        self._update_visuals()

    def _update_visuals(self) -> None:
        """Update dropdown layout and visibility.

        Positions all buttons correctly and shows/hides option
        buttons based on the expanded state. The main button
        is always visible at the dropdown's position, while
        option buttons are positioned below it when expanded.
        """
        # Update main button position
        self.button.left = self.left
        self.button.top = self.top
        self.button._update_visuals()

        # Update option button positions and visibility
        for i, btn in enumerate(self.option_buttons):
            btn.left = self.left
            btn.top = self.top + self.height * (i + 1)

            # Show/hide based on expanded state
            if self.expanded:
                btn.show()
            else:
                btn.hide()

            # Update button visuals
            btn._update_visuals()
