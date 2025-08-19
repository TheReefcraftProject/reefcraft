# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""The Reefcraft-specific UI panel and layout structure.

This module provides the Panel class that creates the main left-docked
user interface for the Reefcraft application. The panel serves as the
primary control center, organizing various UI sections in a vertical
layout for easy access to simulation controls and monitoring tools.

The Panel provides:
- A header with the Reefcraft logo
- Engine control section for simulation playback
- Pipeline management section for simulation components
- Consistent styling and layout management
- Integration with the simulation engine

This panel integrates with the main UI context and simulation engine
to provide a centralized interface for all simulation operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from reefcraft.ui.control import Control
from reefcraft.ui.icon import Icon
from reefcraft.ui.list import LayoutDirection, List
from reefcraft.ui.palette import Palette
from reefcraft.ui.views.engine_section import EngineSection
from reefcraft.ui.views.pipeline_section import PipelineSection

if TYPE_CHECKING:
    from reefcraft.sim.engine import Engine
    from reefcraft.ui.ui_context import UIContext


class Panel(Palette):
    """Left-docked UI panel with Reefcraft-specific tools and sections.

    The Panel class creates the main left-side control panel for the
    Reefcraft application. It inherits from Palette to provide consistent
    styling and serves as a container for organizing various UI sections
    in a logical, accessible layout.

    The panel layout consists of:
    - A header section with the Reefcraft logo
    - Engine controls for simulation playback and monitoring
    - Pipeline management for simulation component configuration
    - Consistent spacing and visual organization

    Attributes:
        context: UI context for rendering and event handling
        engine: Simulation engine for integration with UI sections
        main_layout: Primary vertical layout containing all sections
    """

    def __init__(self, context: UIContext, engine: "Engine") -> None:
        """Initialize the panel and populate it with UI sections.

        Creates the main panel layout with a header logo and organized
        sections for engine control and pipeline management. The panel
        is designed to provide easy access to all simulation controls
        in a single, well-organized interface.

        Args:
            context: UI context for rendering and event handling
            engine: Simulation engine for integration with UI sections
        """
        super().__init__(context=context)
        self.engine = engine

        # Create header with logo
        header = List(
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
        )

        # Create main layout with all sections
        self.main_layout = List(
            context=context,
            controls=[
                header,
                Control(context=context, height=15),  # Spacing
                EngineSection(context=context, engine=engine),
                PipelineSection(context=context, engine=engine),
            ],
            direction=LayoutDirection.VERTICAL,
            margin=15,
        )

        # Store the main layout for potential future use
        # Note: The Palette class handles its own rendering, so we don't
        # need to explicitly add controls to the context
