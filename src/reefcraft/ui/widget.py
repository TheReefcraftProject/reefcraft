# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines an widget parent class for all UI elements."""

from reefcraft.ui.theme import Theme


class Widget:
    """A base cass for all widget types."""

    def __init__(
        self,
        top: int,
        left: int,
        width: int,
        height: int,
        theme: Theme | None = None,
    ) -> None:
        """A widget is essentially a rectangle."""
        self.top = top
        self.left = left
        self.width = width
        self.height = height
        self.theme = theme or Theme()
