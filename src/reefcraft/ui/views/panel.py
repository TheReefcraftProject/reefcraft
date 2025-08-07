# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""The Reefcraft-specific UI panel and layout structure."""

from __future__ import annotations

from typing import TYPE_CHECKING

from reefcraft.sim.state import SimState
from reefcraft.ui.icon import Icon
from reefcraft.ui.list import LayoutDirection, List
from reefcraft.ui.palette import Palette
from reefcraft.ui.views.coral_section import CoralSection
from reefcraft.ui.views.engine_section import EngineSection

if TYPE_CHECKING:
    from reefcraft.sim.engine import Engine
    from reefcraft.ui.ui_context import UIContext


class Panel(Palette):
    """Left-docked UI panel with Reefcraft-specific tools and sections."""

    def __init__(self, context: UIContext, engine: Engine) -> None:
        """Initialize the panel and populate it with UI sections."""
        super().__init__(context=context)

        List(
            context=context,
            controls=[
                List(
                    context=context,
                    controls=[
                        Icon(
                            context=context,
                            icon="logo.png",
                            width=64,
                            height=64,
                        ),
                    ],
                    direction=LayoutDirection.HORIZONTAL,
                ),
                EngineSection(context=context, engine=engine),
                CoralSection(context=context, engine=engine),
            ],
            margin=15,
        )
