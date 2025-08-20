# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Primary window for the application and views.

This module provides the Window class that serves as the main application
window for the Reefcraft coral reef simulation. It manages the OS-level
window, render canvas, 3D scene, and UI panel integration.

The Window class provides:
- OS-level window management with dark mode titlebar
- Render canvas and WGPU renderer setup
- 3D reef visualization scene
- UI panel for simulation controls
- Render bridge for data-driven visualization
- Main rendering loop and frame updates

The window integrates all major components:
- Simulation engine for physics and growth
- 3D reef scene with coral and water visualization
- UI controls for simulation interaction
- Real-time rendering with configurable frame rate
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rendercanvas.auto import RenderCanvas

from reefcraft.ui.reef import Reef
from reefcraft.ui.render_bridge import MeshViewer, RenderBridge
from reefcraft.ui.ui_context import UIContext
from reefcraft.ui.views.panel import Panel
from reefcraft.utils.window_style import apply_dark_titlebar_and_icon

if TYPE_CHECKING:
    from pathlib import Path

    from reefcraft.sim.engine import Engine


class Window:
    """The main application window integrating OS window, render canvas, and UI.

    The Window class serves as the central coordinator for the Reefcraft
    application, managing both the OS-level window and the rendering
    infrastructure. It creates and coordinates all major components
    including the 3D reef scene, UI panel, and simulation engine.

    Key features:
    - OS window with dark mode titlebar and custom icon
    - High-performance render canvas with configurable frame rate
    - 3D reef visualization with coral and water effects
    - UI panel for simulation controls and monitoring
    - Render bridge for data-driven mesh visualization
    - Integrated rendering loop with automatic updates

    The window automatically manages:
    - Window styling and icon application
    - Component initialization and coordination
    - Rendering loop and frame synchronization
    - Resource cleanup and lifecycle management

    Attributes:
        engine: Reference to the simulation engine
        canvas: Render canvas for graphics output
        context: Global UI context for rendering and events
        reef: 3D reef visualization scene
        bridge: Render bridge for data-driven visualization
        panel: UI panel with simulation controls
    """

    def __init__(self, engine: Engine, app_root: Path) -> None:
        """Initialize the window and all major components.

        Creates the main application window with dark mode styling,
        sets up the render canvas and 3D scene, and initializes
        all UI components. The window is ready for rendering
        immediately after initialization.

        Args:
            engine: Simulation engine for physics and growth simulation
            app_root: Root path of the application for resource loading
        """
        self.engine = engine
        self.canvas = RenderCanvas(size=(1920, 1080), title="Reefcraft", update_mode="continuous", max_fps=60)

        # Apply dark mode titlebar and custom icon
        icon_path = str((app_root / "resources" / "icons" / "logo.ico").resolve())
        apply_dark_titlebar_and_icon("Reefcraft", icon_path)

        # Create the global UI context with renderer state
        self.context = UIContext(canvas=self.canvas)

        # Create the 3D reef visualization scene
        if self.context.renderer is not None:
            self.reef = Reef(self.context.renderer, engine=self.engine)

            # Create render bridge for data-driven visualization
            # This connects simulation data to 3D mesh rendering
            self.bridge = RenderBridge(store=self.engine.state.store, scene=self.reef.scene)

            # Register mesh viewers for coral visualization
            # Each viewer handles a specific coral's mesh data
            for i in range(4):
                self.bridge.register_viewer(f"coral.{i}.mesh", MeshViewer())

            # Create the UI panel for simulation controls
            self.panel = Panel(self.context, engine=self.engine)

            # Set up the main rendering loop
            self.context.renderer.request_draw(self.draw)
        else:
            raise RuntimeError("Failed to initialize renderer")

    @property
    def is_open(self) -> bool:
        """Check if the window is still open and active.

        Returns:
            True if the window is open, False if it has been closed
        """
        return not self.canvas.get_closed()

    def draw(self) -> None:
        """Render one frame of the simulation and overlay UI.

        This method is called automatically by the renderer to update
        the display. It synchronizes data-driven visuals, renders the
        3D reef scene, updates the UI panel, and flushes the renderer.

        The draw method coordinates:
        - Mesh updates from simulation data
        - 3D scene rendering with coral and water
        - UI panel updates and control rendering
        - Renderer state synchronization
        """
        # Synchronize data-driven visuals (mesh/fields) from the store
        self.bridge.sync()

        # Render the 3D reef scene with current simulation state
        self.reef.draw(self.engine.state)

        # Update and render the UI panel
        self.panel.draw(self.engine.state)

        # Flush the renderer to complete the frame
        if self.context.renderer is not None:
            self.context.renderer.flush()
