# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Render bridge for decoupling simulation data from 3D visualization.

This module provides the RenderBridge class and related viewer classes that
create a clean separation between simulation data and 3D visualization.
The bridge automatically synchronizes data changes from the simulation
store to visual representations in the 3D scene.

The RenderBridge provides:
- Automatic data synchronization between store and viewers
- Protocol-based viewer system for different data types
- Mesh visualization for coral geometry
- Velocity field visualization with glyphs
- Change detection and incremental updates
- Scene lifecycle management for viewers

The system uses a version-based approach to detect when data has changed
and automatically updates the corresponding visual representations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pygfx as gfx

if TYPE_CHECKING:
    from reefcraft.sim.data_store import DataStore


class Viewer:
    """Protocol-like base class for data viewers.

    The Viewer class defines the interface that all data viewers must implement.
    Viewers are responsible for creating, updating, and managing visual
    representations of simulation data in the 3D scene.

    Viewers automatically handle:
    - Scene attachment and detachment
    - Data updates and visual synchronization
    - Resource cleanup and lifecycle management

    Attributes:
        _mesh: Optional mesh object for visualization
        _points: Optional points object for particle visualization
    """

    def attach(self, scene: gfx.Scene) -> None:  # pragma: no cover - tiny wrapper
        """Attach the viewer to a 3D scene.

        Creates the visual representation and adds it to the scene.
        This method is called when the viewer is registered.

        Args:
            scene: The PyGFX scene to attach the viewer to
        """
        raise NotImplementedError

    def detach(self, scene: gfx.Scene) -> None:  # pragma: no cover
        """Detach the viewer from a 3D scene.

        Removes the visual representation and cleans up resources.
        This method is called when the viewer is unregistered.

        Args:
            scene: The PyGFX scene to detach the viewer from
        """
        raise NotImplementedError

    def update(self, value: Any) -> None:  # pragma: no cover
        """Update the visual representation with new data.

        Updates the viewer's visual elements to reflect the new
        simulation data. This method is called automatically when
        data changes in the store.

        Args:
            value: The new data value to visualize
        """
        raise NotImplementedError


class MeshViewer(Viewer):
    """Viewer for 3D mesh data representing coral geometry.

    The MeshViewer creates and manages 3D mesh representations
    of coral entities. It handles mesh creation, updates, and
    coordinate system transformations between simulation and
    rendering coordinate systems.

    Key features:
    - Automatic mesh creation from vertex/face data
    - Coordinate system conversion (right-handed to left-handed)
    - Support for both dict and tuple data formats
    - Warp array compatibility for GPU data
    - Type safety for NumPy arrays

    Attributes:
        _mesh: PyGFX mesh object for 3D rendering
    """

    def __init__(self) -> None:
        """Initialize the mesh viewer with no initial mesh."""
        self._mesh: gfx.Mesh | None = None

    def attach(self, scene: gfx.Scene) -> None:
        """Create and attach a placeholder mesh to the scene.

        Creates a simple triangular mesh as a placeholder and adds
        it to the scene. The mesh uses a blue material for visibility.

        Args:
            scene: The PyGFX scene to add the mesh to
        """
        if self._mesh is None:
            # Create placeholder geometry
            geom = gfx.Geometry(positions=np.zeros((3, 3), dtype=np.float32), indices=np.array([[0, 1, 2]], dtype=np.uint32))
            self._mesh = gfx.Mesh(geom, gfx.MeshPhongMaterial(color="#0040ff"))
            scene.add(self._mesh)

    def detach(self, scene: gfx.Scene) -> None:
        """Remove the mesh from the scene and clean up.

        Removes the mesh object from the scene and clears the
        internal reference for proper cleanup.

        Args:
            scene: The PyGFX scene to remove the mesh from
        """
        if self._mesh is not None:
            scene.remove(self._mesh)
            self._mesh = None

    def update(self, value: object) -> None:
        """Update the mesh with new geometry data.

        Accepts either a dictionary with 'vertices' and 'indices' keys
        or a tuple of (vertices, indices). Automatically handles
        Warp arrays, converts to appropriate NumPy types, and
        transforms coordinates for left-handed rendering.

        Args:
            value: Mesh data in dict or tuple format
        """
        if self._mesh is None:
            return

        # Extract positions and indices from the data
        positions = None
        indices = None
        if isinstance(value, dict):
            positions = value.get("vertices")
            indices = value.get("indices")
        elif isinstance(value, tuple) and len(value) == 2:
            positions, indices = value

        if positions is None or indices is None:
            return

        # Convert Warp arrays to NumPy if needed
        if hasattr(positions, "numpy"):
            positions = positions.numpy()
        if hasattr(indices, "numpy"):
            indices = indices.numpy()

        # Ensure correct data types (NumPy 2.0 safe)
        positions = np.asarray(positions)
        if positions.dtype != np.float32:
            positions = positions.astype(np.float32, copy=False)
        indices = np.asarray(indices)
        if indices.dtype != np.uint32:
            indices = indices.astype(np.uint32, copy=False)

        # Swap Y/Z coordinates for left-handed rendering
        if positions.ndim == 2 and positions.shape[1] >= 3:
            positions = positions.copy()
            positions[:, [1, 2]] = positions[:, [2, 1]]

        # Update the mesh geometry
        if self._mesh is not None and self._mesh.geometry is not None:
            self._mesh.geometry.positions = gfx.Buffer(positions)
            self._mesh.geometry.indices = gfx.Buffer(indices)


class VelocityGlyphViewer(Viewer):
    """Viewer for velocity field visualization using point glyphs.

    The VelocityGlyphViewer creates point-based representations
    of velocity fields for fluid visualization. Currently a stub
    implementation that can be extended for advanced glyph rendering.

    Key features:
    - Point-based velocity field representation
    - Configurable glyph appearance and density
    - Automatic sampling from velocity data
    - Future support for advanced glyph types

    Attributes:
        _points: PyGFX points object for particle visualization
    """

    def __init__(self) -> None:
        """Initialize the velocity glyph viewer with no initial points."""
        self._points: gfx.Points | None = None

    def attach(self, scene: gfx.Scene) -> None:
        """Create and attach placeholder points to the scene.

        Creates a simple point cloud as a placeholder and adds
        it to the scene. The points use a cyan color for visibility.

        Args:
            scene: The PyGFX scene to add the points to
        """
        if self._points is None:
            positions = np.zeros((100, 3), dtype=np.float32)
            geom = gfx.Geometry(positions=positions)
            self._points = gfx.Points(geom, gfx.PointsMaterial(color="#00ffbf", size=4))
            scene.add(self._points)

    def detach(self, scene: gfx.Scene) -> None:
        """Remove the points from the scene and clean up.

        Removes the points object from the scene and clears the
        internal reference for proper cleanup.

        Args:
            scene: The PyGFX scene to remove the points from
        """
        if self._points is not None:
            scene.remove(self._points)
            self._points = None

    def update(self, value: np.ndarray) -> None:
        """Update the velocity glyph visualization.

        Currently a stub implementation. Future versions will
        sample the velocity field and create appropriate glyphs
        for fluid visualization.

        Args:
            value: Velocity field data as a NumPy array
        """
        # For now this is a stub: advanced glyphs can be added later
        # We could sample velocities into points, but keep simple for now
        return


class RenderBridge:
    """Bridge between simulation data store and 3D visualization.

    The RenderBridge automatically synchronizes data changes from
    the simulation store to registered viewers. It tracks data
    versions and only updates viewers when their data has changed.

    Key features:
    - Automatic change detection using version tracking
    - Viewer registration and lifecycle management
    - Efficient updates only when data changes
    - Support for multiple data types and viewers
    - Scene integration and cleanup

    The bridge maintains a mapping between store keys and viewers,
    automatically calling update() on viewers when their data
    changes in the store.

    Attributes:
        store: Data store containing simulation data
        scene: 3D scene for visual representation
        _key_to_viewer: Mapping from store keys to viewer instances
        _last_versions: Last known version for each store key
    """

    def __init__(self, store: DataStore, scene: gfx.Scene) -> None:
        """Initialize the render bridge.

        Creates a new bridge connecting the simulation data store
        to the 3D visualization scene.

        Args:
            store: Data store containing simulation data
            scene: 3D scene for visual representation
        """
        self.store = store
        self.scene = scene
        self._key_to_viewer: dict[str, Viewer] = {}
        self._last_versions: dict[str, int] = {}

    def register_viewer(self, key: str, viewer: Viewer) -> None:
        """Register a viewer for a specific data key.

        Associates a viewer with a store key and automatically
        attaches it to the scene. The viewer will be updated
        whenever the data for this key changes.

        Args:
            key: Store key identifying the data to visualize
            viewer: Viewer instance to handle the data
        """
        self._key_to_viewer[key] = viewer
        self._last_versions[key] = 0
        viewer.attach(self.scene)

    def unregister_viewer(self, key: str) -> None:
        """Unregister a viewer for a specific data key.

        Removes the association between a key and viewer,
        detaches the viewer from the scene, and cleans up
        the version tracking.

        Args:
            key: Store key to unregister
        """
        viewer = self._key_to_viewer.pop(key, None)
        if viewer is not None:
            viewer.detach(self.scene)
        self._last_versions.pop(key, None)

    def sync(self) -> None:
        """Synchronize all registered viewers with current store data.

        Checks each registered viewer's data for changes and
        updates the viewer if new data is available. This method
        should be called regularly (e.g., each frame) to keep
        the visualization synchronized with simulation data.
        """
        for key, viewer in self._key_to_viewer.items():
            current_version = self.store.version(key)
            last_version = self._last_versions.get(key, 0)

            if current_version > last_version:
                value = self.store.try_get(key)
                if value is not None:
                    viewer.update(value)
                self._last_versions[key] = current_version
