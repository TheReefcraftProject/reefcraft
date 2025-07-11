import numpy as np

from reefcraft.render.scene import TriangleScene


def test_triangle_geometry_shapes() -> None:
    scene = TriangleScene()
    geo = scene.mesh.geometry
    assert geo.positions.data.shape == (3, 3)
    assert geo.indices.data.shape == (3,)
    assert geo.positions.data.dtype == np.float32
    assert geo.indices.data.dtype == np.uint32


def test_triangle_material_color() -> None:
    scene = TriangleScene()
    r, g, b, a = scene.material.color
    for v in (r, g, b, a):
        assert 0.0 <= v <= 1.0
