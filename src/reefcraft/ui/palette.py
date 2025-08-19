# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Base class for a UI palette, managing scene and input capture.

This module provides the Palette class that creates a left-docked UI panel
in the Reefcraft application. The Palette provides a dedicated rendering
area with its own background, input capture, and scene management.

The Palette provides:
- Left-docked positioning with configurable dimensions
- Dedicated background rendering with pointer capture
- Input event handling for mouse interactions
- Scene management and rendering coordination
- Blocking of scene clicks behind the palette
- Integration with the main UI context

Palettes are commonly used for:
- Control panels and toolbars
- Property editors and settings
- Navigation menus and hierarchies
- Simulation controls and displays
- Status information and metrics
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygfx as gfx

if TYPE_CHECKING:
    from reefcraft.sim.state import SimState
    from reefcraft.ui.ui_context import UIContext


class Palette:
    """A left-docked UI palette with a dedicated scene and input handling.

    The Palette class provides a specialized UI container that docks to
    the left side of the application window. It creates a dedicated
    rendering area with its own background and input capture system,
    allowing it to block interactions with the main scene while providing
    a clean interface for UI controls.

    Key features:
    - Left-docked positioning with configurable dimensions
    - Solid background with pointer capture
    - Mouse event handling and pointer management
    - Scene integration and rendering coordination
    - Automatic positioning relative to main window

    The palette automatically positions itself on the left side of the
    main window and provides a dedicated area for UI controls while
    preventing accidental interaction with the main simulation scene.

    Attributes:
        context: UI context for rendering and event handling
        width: Width of the palette in pixels
        height: Height of the palette in pixels
        _background_mesh: Background mesh for visual styling and input capture
    """

    def __init__(self, context: UIContext, width: int = 300, height: int = 1080) -> None:
        """Initialize the palette with its own scene and camera.

        Creates a new Palette instance with the specified dimensions.
        Sets up the background mesh with pointer capture and positions
        it on the left side of the main window.

        Args:
            context: UI context for rendering and event handling
            width: Width of the palette in pixels (default: 300)
            height: Height of the palette in pixels (default: 1080)
        """
        self.context = context
        self.width = width
        self.height = height

        # Initialize background and input capture
        self._init_background()

    def _init_background(self) -> None:
        """Add solid background mesh with pointer capture to block scene clicks.

        Creates a background mesh that covers the entire palette area.
        The mesh is configured with pointer capture to intercept mouse
        events and prevent them from reaching the main scene behind it.
        The background is positioned on the left side of the main window.
        """
        # Create background geometry and material
        geom = gfx.plane_geometry(width=self.width, height=self.height)
        mat = gfx.MeshBasicMaterial(color="#08080A", pick_write=True)

        # Create and position the background mesh
        self._background_mesh = gfx.Mesh(geom, mat)

        # Position on left side of main window
        left_offset = -((self.context.width / 2) - (self.width / 2))
        self._background_mesh.local.position = (left_offset, 0, -100)

        # Set up input event handling
        self._background_mesh.add_event_handler(self._on_mouse_down, "pointer_down")
        self._background_mesh.add_event_handler(self._on_mouse_up, "pointer_up")

        # Add to the scene
        self.context.add(self._background_mesh)

    def _on_mouse_down(self, event: gfx.PointerEvent) -> None:
        """When clicked, capture mouse and block others.

        Handles mouse down events by capturing the pointer to prevent
        other UI elements from receiving mouse events while the palette
        is being interacted with.

        Args:
            event: Mouse down event containing pointer information
        """
        event.target.set_pointer_capture(event.pointer_id, self.context.renderer)

    def _on_mouse_up(self, event: gfx.PointerEvent) -> None:
        """Release the mouse after click.

        Handles mouse up events by releasing the pointer capture,
        allowing other UI elements to receive mouse events again.

        Args:
            event: Mouse up event containing pointer information
        """
        event.target.release_pointer_capture(event.pointer_id)

    def draw(self, state: SimState) -> None:
        """Render the palette contents.

        Triggers the rendering of the palette and all its child elements.
        This method coordinates with the main UI context to ensure
        proper rendering order and scene management.

        Args:
            state: Current simulation state for context-aware rendering
        """
        self.context.draw()
