# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""UI section for simulation engine control and monitoring.

This module provides the EngineSection class that creates a user interface
for controlling the Reefcraft simulation engine. The interface displays
simulation status and provides controls for play/pause functionality.

The EngineSection provides:
- A title bar displaying "SIMULATION"
- A play/pause toggle button with visual feedback
- Real-time display of simulation metrics (time, step rate, speed)
- Integration with the simulation engine for control operations

This UI integrates with the simulation engine to provide real-time
control and monitoring of the simulation state.
"""

from reefcraft.sim.engine import Engine
from reefcraft.ui.control import Control
from reefcraft.ui.icon_button import IconButton
from reefcraft.ui.label import Label, TextAlign
from reefcraft.ui.list import LayoutDirection, List
from reefcraft.ui.ui_context import UIContext


class EngineSection(List):
    """UI section for controlling and monitoring the simulation engine.

    The EngineSection provides a complete interface for engine management,
    including play/pause controls and real-time status display. It consists
    of a title bar and a control row with the play button and metrics display.

    The section integrates with the simulation engine to:
    - Control simulation playback (play/pause)
    - Display real-time simulation metrics
    - Provide visual feedback for engine state

    Attributes:
        engine: Reference to the simulation engine for control operations
        controls: List of UI controls that make up the section
    """

    def __init__(self, context: UIContext, engine: Engine) -> None:
        """Initialize the engine section with the given context and engine.

        Creates a vertical layout containing a title bar and a control row.
        The title bar displays "SIMULATION" and the control row provides
        the play/pause button and real-time metrics display.

        Args:
            context: UI context for rendering and event handling
            engine: Simulation engine for control and monitoring operations
        """
        super().__init__(
            context=context,
            background=True,
            direction=LayoutDirection.VERTICAL,
            margin=0,
        )
        self.engine = engine

        # Create title bar
        title_bar = List(
            context,
            controls=[
                Control(context, width=10),  # Left spacing
                Label(context, text="SIMULATION", width=250, align=TextAlign.LEFT, font_color="#F3F6FA"),
            ],
            direction=LayoutDirection.HORIZONTAL,
            margin=5,
        )

        # Create control row with play button and metrics
        control_row = List(
            context,
            controls=[
                Control(context, width=24),  # Left spacing
                IconButton(
                    context,
                    "play.png",
                    width=24,
                    height=24,
                    toggle=True,
                    on_toggle=self._on_play_toggle,
                    normal_tint=(0.0, 0.5),
                    hover_tint=(0.0, 1.0),
                    pressed_tint=(194.0, 1.5),  # theme.highlight_color play state
                ),
                Label(
                    context,
                    text=self._get_metrics_text,
                    width=200,
                    align=TextAlign.RIGHT,
                ),
            ],
            direction=LayoutDirection.HORIZONTAL,
        )

        # Add spacing at the bottom
        bottom_spacing = Control(context, height=5)

        # Add all controls to the section
        self.add_control(title_bar)
        self.add_control(control_row)
        self.add_control(bottom_spacing)

    def _on_play_toggle(self, playing: bool) -> None:
        """Handle play/pause button toggle events.

        Controls the simulation engine playback state based on the
        button toggle. When the button is pressed (playing=True),
        the simulation starts; when released (playing=False), it pauses.

        Args:
            playing: True if the play button is pressed, False if released
        """
        if playing:
            self.engine.play()
        else:
            self.engine.pause()

    def _get_metrics_text(self) -> str:
        """Generate the current simulation metrics display text.

        Returns a formatted string showing the current simulation time,
        step rate, and speed multiplier. This method is called by the
        metrics label to provide real-time updates.

        Returns:
            Formatted string with simulation metrics (time, step rate, speed)
        """
        return f"{self.engine.get_time():6.2f}s  {self.engine.step_rate_hz:5.1f} Hz   {self.engine.sim_speed_ratio:4.2f}×"
