# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Global UI context for rendering and scene management.

This module provides the UIContext class that serves as the central
rendering context for all UI controls in the Reefcraft application.
It manages the PyGFX renderer, scene, camera, and viewport, providing
a unified interface for UI rendering operations.

The UIContext provides:
- PyGFX WGPU renderer for hardware-accelerated graphics
- 3D scene management for UI controls and overlays
- Orthographic camera for 2D UI rendering
- Viewport management for rendering output
- Coordinate system conversion utilities
- Headless mode fallback for testing

The context automatically handles:
- Renderer initialization and error handling
- Scene hierarchy management
- Camera setup and projection
- Coordinate transformations
- Resource cleanup and lifecycle

The context supports both normal rendering mode and a lightweight
headless mode for unit testing scenarios where a real renderer
is not available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygfx as gfx

if TYPE_CHECKING:
    from rendercanvas.auto import RenderCanvas


class UIContext:
    """Global rendering context shared by all UI controls.

    The UIContext class provides a unified interface for all UI
    rendering operations in the Reefcraft application. It manages
    the PyGFX renderer, scene, camera, and viewport, and provides
    utility methods for coordinate transformations and scene management.

    Key features:
    - Hardware-accelerated rendering with PyGFX WGPU
    - 3D scene management for UI controls
    - Orthographic camera for 2D UI rendering
    - Automatic headless mode fallback for testing
    - Coordinate system conversion utilities
    - Scene object lifecycle management

    The context automatically manages:
    - Renderer initialization and error handling
    - Scene hierarchy and object management
    - Camera setup and projection
    - Viewport configuration
    - Resource cleanup

    Attributes:
        canvas: Render canvas for graphics output
        renderer: PyGFX WGPU renderer (None in headless mode)
        scene: 3D scene containing all UI objects (or headless stub)
        camera: Orthographic camera for UI rendering (None in headless mode)
        viewport: PyGFX viewport for rendering (None in headless mode)
    """

    def __init__(self, canvas: RenderCanvas, width: int = 1920, height: int = 1080) -> None:
        """Initialize the UI rendering context.

        Creates a new UI context with the specified canvas and dimensions.
        Attempts to initialize a PyGFX WGPU renderer, but falls back to
        a lightweight headless mode if rendering initialization fails
        (e.g., during unit testing or in headless environments).

        Args:
            canvas: Render canvas for graphics output
            width: Initial width of the rendering area in pixels
            height: Initial height of the rendering area in pixels

        Note:
            The headless fallback mode preserves the public API while
            providing minimal functionality for testing scenarios.
        """
        self.canvas = canvas

        try:
            # Initialize PyGFX rendering components
            self.renderer = gfx.WgpuRenderer(canvas)
            self.scene = gfx.Scene()
            self.camera = gfx.OrthographicCamera(width=width, height=height)
            self.viewport = gfx.Viewport(self.renderer)
        except Exception:  # pragma: no cover - exercised in tests
            # Headless fallback for testing scenarios
            self._setup_headless_mode()

    def _setup_headless_mode(self) -> None:
        """Set up lightweight headless mode for testing.

        Creates minimal stub implementations of rendering components
        that preserve the public API while providing no actual
        rendering functionality. This allows UI controls to be
        tested without requiring a real graphics context.
        """

        class _SimpleScene:
            """Minimal scene stub for headless mode."""

            def __init__(self) -> None:
                self.children: list[object] = []

            def add(self, obj: object) -> None:
                """Add an object to the scene (no-op in headless mode)."""
                self.children.append(obj)

        # Set all rendering components to None or stubs
        self.renderer = None  # type: ignore[assignment]
        self.scene = _SimpleScene()  # type: ignore[assignment]
        self.camera = None  # type: ignore[assignment]
        self.viewport = None  # type: ignore[assignment]

    def add(self, *objs: object) -> None:
        """Add one or more PyGFX objects to the UI scene.

        Adds the specified objects to the scene for rendering.
        In headless mode, this operation is a no-op but preserves
        the object references for testing purposes.

        Args:
            *objs: One or more PyGFX WorldObject instances to add
        """
        for obj in objs:
            if hasattr(self.scene, "add"):
                self.scene.add(obj)  # type: ignore[attr-defined]

    def remove(self, *objs: object) -> None:
        """Remove one or more PyGFX objects from the UI scene.

        Removes the specified objects from the scene. In headless mode,
        this operation is a no-op but maintains the object references
        for testing purposes.

        Args:
            *objs: One or more PyGFX WorldObject instances to remove
        """
        for obj in objs:
            children = getattr(self.scene, "children", None)
            if isinstance(children, list) and obj in children:
                children.remove(obj)

    def draw(self) -> None:
        """Render the UI scene to the viewport.

        Renders the current scene using the camera and viewport.
        This method is a no-op in headless mode since no actual
        rendering is performed.

        Note:
            This method should be called regularly to update the
            display with any changes to the scene.
        """
        if self.viewport is not None and self.renderer is not None and self.camera is not None:
            self.viewport.render(self.scene, self.camera)

    @property
    def width(self) -> int:
        """Get the logical width of the canvas in pixels.

        Returns:
            Width of the canvas in pixels
        """
        return self.canvas.get_logical_size()[0]

    @property
    def height(self) -> int:
        """Get the logical height of the canvas in pixels.

        Returns:
            Height of the canvas in pixels
        """
        return self.canvas.get_logical_size()[1]

    def screen_to_world(self, x: float, y: float, z: float = 0.0) -> tuple[float, float, float]:
        """Convert screen-space coordinates to world coordinates.

        Transforms pixel coordinates from the screen coordinate system
        to the world coordinate system using an orthographic projection.
        The conversion centers the coordinate system and flips the Y-axis
        to match typical UI coordinate conventions.

        Args:
            x: Screen x-coordinate in pixels
            y: Screen y-coordinate in pixels
            z: Screen z-coordinate (depth, defaults to 0.0)

        Returns:
            Tuple of (world_x, world_y, world_z) coordinates

        Note:
            The coordinate system is centered at the canvas center,
            with positive Y pointing upward in world space.
        """
        # Center-based world space conversion
        world_x = x - self.width / 2
        world_y = self.height / 2 - y
        world_z = z
        return (world_x, world_y, world_z)
