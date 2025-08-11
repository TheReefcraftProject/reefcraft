# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Render bridge that syncs pygfx scene from the DataStore on version changes."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pygfx as gfx

from reefcraft.sim.data_store import DataStore


class Viewer:
    """Protocol-like base for viewers."""

    def attach(self, scene: gfx.Scene) -> None:  # pragma: no cover - tiny wrapper
        raise NotImplementedError

    def detach(self, scene: gfx.Scene) -> None:  # pragma: no cover
        raise NotImplementedError

    def update(self, value: Any) -> None:  # pragma: no cover
        raise NotImplementedError


class MeshViewer(Viewer):
    def __init__(self) -> None:
        self._mesh: gfx.Mesh | None = None

    def attach(self, scene: gfx.Scene) -> None:
        if self._mesh is None:
            # Create placeholder geometry
            geom = gfx.Geometry(positions=np.zeros((3, 3), dtype=np.float32), indices=np.array([[0, 1, 2]], dtype=np.uint32))
            self._mesh = gfx.Mesh(geom, gfx.MeshPhongMaterial(color="#0040ff"))
            scene.add(self._mesh)

    def detach(self, scene: gfx.Scene) -> None:
        if self._mesh is not None:
            scene.remove(self._mesh)
            self._mesh = None

    def update(self, value: object) -> None:
        if self._mesh is None:
            return
        # Accept either a dict with keys or a (verts, indices) tuple
        positions = None
        indices = None
        if isinstance(value, dict):
            positions = value.get("vertices")
            indices = value.get("indices")
        elif isinstance(value, tuple) and len(value) == 2:
            positions, indices = value
        if positions is None or indices is None:
            return
        # Convert Warp arrays to numpy if needed and swap Y/Z for left-handed view
        if hasattr(positions, "numpy"):
            positions = positions.numpy()
        if hasattr(indices, "numpy"):
            indices = indices.numpy()
        # Ensure float32/uint32 types (NumPy 2.0 safe)
        positions = np.asarray(positions)
        if positions.dtype != np.float32:
            positions = positions.astype(np.float32, copy=False)
        indices = np.asarray(indices)
        if indices.dtype != np.uint32:
            indices = indices.astype(np.uint32, copy=False)
        # Swap Y/Z for left-handed rendering
        if positions.ndim == 2 and positions.shape[1] >= 3:
            positions = positions.copy()
            positions[:, [1, 2]] = positions[:, [2, 1]]
        self._mesh.geometry.positions = gfx.Buffer(positions)
        self._mesh.geometry.indices = gfx.Buffer(indices)


class VelocityGlyphViewer(Viewer):
    def __init__(self) -> None:
        self._points: gfx.Points | None = None

    def attach(self, scene: gfx.Scene) -> None:
        if self._points is None:
            positions = np.zeros((100, 3), dtype=np.float32)
            geom = gfx.Geometry(positions=positions)
            self._points = gfx.Points(geom, gfx.PointsMaterial(color="#00ffbf", size=4))
            scene.add(self._points)

    def detach(self, scene: gfx.Scene) -> None:
        if self._points is not None:
            scene.remove(self._points)
            self._points = None

    def update(self, value: np.ndarray) -> None:
        # For now this is a stub: advanced glyphs can be added later
        # We could sample velocities into points, but keep simple for now
        return


class RenderBridge:
    """Track versions in the store and update registered viewers on change."""

    def __init__(self, store: DataStore, scene: gfx.Scene) -> None:
        self.store = store
        self.scene = scene
        self._key_to_viewer: Dict[str, Viewer] = {}
        self._last_versions: Dict[str, int] = {}

    def register_viewer(self, key: str, viewer: Viewer) -> None:
        self._key_to_viewer[key] = viewer
        self._last_versions[key] = 0
        viewer.attach(self.scene)

    def unregister_viewer(self, key: str) -> None:
        viewer = self._key_to_viewer.pop(key, None)
        if viewer is not None:
            viewer.detach(self.scene)
        self._last_versions.pop(key, None)

    def sync(self) -> None:
        for key, viewer in self._key_to_viewer.items():
            v = self.store.version(key)
            if v > self._last_versions.get(key, 0):
                value = self.store.try_get(key)
                if value is not None:
                    viewer.update(value)
                self._last_versions[key] = v


