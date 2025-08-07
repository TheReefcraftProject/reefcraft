# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Dropdown menu control for selecting from a list of options."""

from collections.abc import Callable

from reefcraft.ui.button import Button
from reefcraft.ui.control import Control
from reefcraft.ui.theme import Theme
from reefcraft.ui.ui_context import UIContext
from reefcraft.utils.logger import logger


class Dropdown(Control):
    """Dropdown control with selectable options."""

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
        """Create a dropdown menu."""
        super().__init__(context, left=left, top=top, width=width, height=height, theme=theme)

        self.options = options
        self.on_select = on_select
        self.selected = default or options[0]
        self.expanded = False

        # Button to show current selection
        self.button = Button(
            self.context,
            label=self.selected,
            width=self.width,
            height=self.height,
            on_click=self.toggle,
        )
        self.root.add(self.button.root)

        # Create and initially hide option buttons
        self.option_buttons: list[Button] = []
        for i, opt in enumerate(options):
            btn = Button(
                self.context,
                label=opt,
                width=self.width,
                height=self.height,
                on_click=lambda opt=opt: self.select(opt),
            )
            btn.hide()
            self.option_buttons.append(btn)
            self.root.add(btn.root)

        self._update_visuals()

    def toggle(self) -> None:
        """Toggle dropdown open or closed."""
        self.expanded = not self.expanded
        self._update_visuals()

    def select(self, value: str) -> None:
        """Select an option and close the menu."""
        self.selected = value
        self.button.text_string = value
        self.button._text.set_text(value)
        self.on_select(value)
        self.expanded = False
        self._update_visuals()

    def close(self) -> None:
        """Programmatically close the dropdown."""
        self.expanded = False
        self._update_visuals()

    def _update_visuals(self) -> None:
        """Update dropdown layout and visibility."""
        self.button.left = self.left
        self.button.top = self.top
        self.button._update_visuals()

        for i, btn in enumerate(self.option_buttons):
            btn.left = self.left
            btn.top = self.top + self.height * (i + 1)
            if self.expanded:
                btn.show()
            else:
                btn.hide()
            btn._update_visuals()
