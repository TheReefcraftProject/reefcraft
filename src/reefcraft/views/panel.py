# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Defines the main GUI layout as a side panel."""

import pygfx as gfx


class Section:
    """A sub-section of the UI to show/hide."""

    def __init__(self) -> None:
        """Initialize the section TBD."""
        print("NOT IMPL")


class Panel:
    """A left-docked panel: covers left 300px of canvas height."""

    def __init__(self, renderer, width=300, height=1080) -> None:
        """Initialize the panel and its correstponding 3D scene and ortho cameras."""
        self.renderer = renderer

        geom = gfx.plane_geometry(width=width, height=height, width_segments=1, height_segments=1)
        mat = gfx.MeshBasicMaterial(color="#08080A")
        mesh = gfx.Mesh(geom, mat)
        mesh.local.position = (-((1920 / 2) - (300 / 2)), 0, 0)

        self.scene = gfx.Scene()
        self.camera = gfx.OrthographicCamera(width=1920, height=1080)
        self.scene.add(mesh)

    def draw(self) -> None:
        """Draw a solid rectangle on the left side of the UI scene."""
        self.renderer.render(self.scene, self.camera, flush=False)
