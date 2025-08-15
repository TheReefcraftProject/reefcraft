import importlib.util
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location(
    "simple_porag",
    Path(__file__).resolve().parents[2] / "src" / "reefcraft" / "sim" / "simple_porag.py",
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
SimpleP = module.SimpleP

spec_state = importlib.util.spec_from_file_location(
    "state",
    Path(__file__).resolve().parents[2] / "src" / "reefcraft" / "sim" / "state.py",
)
module_state = importlib.util.module_from_spec(spec_state)
assert spec_state.loader is not None
spec_state.loader.exec_module(module_state)
SimState = module_state.SimState

"""Tests for the SimpleP growth model."""


def test_hemisphere_initialization() -> None:
    """Mesh starts as a watertight hemisphere with a base centre vertex."""
    sim_state = SimState()
    simple_p = SimpleP(sim_state=sim_state)

    verts = simple_p.mesh.vertices
    assert np.all(verts[:, 2] >= -1e-6)
    assert np.allclose(verts[-1], [0.0, 0.0, 0.0])
    assert simple_p.mesh.is_watertight


def test_growth_step_moves_along_normals() -> None:
    """Vertices move outward along their normals during growth."""
    sim_state = SimState()
    simple_p = SimpleP(sim_state=sim_state)

    initial_pos = simple_p.mesh.vertices[0].copy()
    initial_normal = simple_p.mesh.vertex_normals[0].copy()
    simple_p.growth_step()
    new_pos = simple_p.mesh.vertices[0]

    displacement = new_pos - initial_pos
    assert np.dot(displacement, initial_normal) > 0


def test_add_polyp_increases_vertex_count() -> None:
    """Adding a polyp inserts a new vertex which can grow later."""
    sim_state = SimState()
    simple_p = SimpleP(sim_state=sim_state)

    initial_count = len(simple_p.mesh.vertices)
    new_pos = np.array(
        [
            0.0,
            0.0,
            simple_p.radius + 2 * simple_p.polyp_spacing,
        ],
        dtype=np.float32,
    )

    simple_p.add_polyp(new_pos)
    assert len(simple_p.mesh.vertices) == initial_count + 1
    assert np.allclose(simple_p.mesh.vertices[-1], new_pos)
