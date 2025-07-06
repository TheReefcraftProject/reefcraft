import sys
import types
from pathlib import Path

if "taichi" not in sys.modules:
    ti_stub = types.SimpleNamespace()
    ti_stub.vulkan = "vulkan"
    ti_stub.init = lambda arch=None: None
    ti_stub.kernel = lambda f: f

    def fake_field(*args: object, shape: tuple[int, ...] | None = None, **kwargs: object) -> object:
        class Dummy:
            def __init__(self, shape: tuple[int, ...] | None) -> None:
                self.shape = shape

        return Dummy(shape)

    def ndrange(*sizes: int) -> list[tuple[int, int, int]]:
        result = []
        for i in range(sizes[0]):
            for j in range(sizes[1]):
                for k in range(sizes[2]):
                    result.append((i, j, k))
        return result

    def vector(values: object | None = None) -> object | None:
        return values

    vector.field = fake_field

    ti_stub.Vector = vector
    ti_stub.field = fake_field
    ti_stub.f32 = 0.0
    ti_stub.ndrange = ndrange
    ti_stub.ijk = 0
    ti_stub.root = types.SimpleNamespace(pointer=lambda *a, **k: types.SimpleNamespace(dense=lambda *a, **k: types.SimpleNamespace(place=lambda *a, **k: None)))
    ti_stub.ui = types.SimpleNamespace(Scene=object, make_camera=lambda: object())
    sys.modules["taichi"] = ti_stub

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from reefcraft.sim.volume import Volume

Volume._fill_test_pattern = lambda self: None


def test_volume_initializes_fields() -> None:
    vol = Volume(active_region=4)
    assert vol.resolution == 1000
    assert vol.coords.shape == 4 ** 3

