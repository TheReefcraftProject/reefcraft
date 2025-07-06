import sys
import time
import types
from pathlib import Path

if "taichi" not in sys.modules:
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

    ui_stub = types.SimpleNamespace(Window=object, Gui=object, Scene=object, make_camera=lambda: object())

    def vector(values: object | None = None) -> object | None:
        return values

    vector.field = fake_field

    ti_stub = types.SimpleNamespace(
        ui=ui_stub,
        vulkan="vulkan",
        init=lambda arch=None: None,
        kernel=lambda f: f,
        data_oriented=lambda cls: cls,
        Vector=vector,
        field=fake_field,
        f32=0.0,
        ijk=0,
        ndrange=ndrange,
        root=types.SimpleNamespace(pointer=lambda *a, **k: types.SimpleNamespace(dense=lambda *a, **k: types.SimpleNamespace(place=lambda *a, **k: None))),
    )
    sys.modules["taichi"] = ti_stub

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from reefcraft.sim.engine import Engine
from reefcraft.sim.timer import Timer
from reefcraft.sim.volume import Volume

Volume._fill_test_pattern = lambda self: None


def test_timer_pause_and_resume() -> None:
    timer = Timer()
    timer.start()
    time.sleep(0.01)
    first = timer.time
    assert first > 0
    timer.pause()
    paused = timer.time
    time.sleep(0.01)
    assert abs(timer.time - paused) < 0.001
    timer.start()
    time.sleep(0.01)
    assert timer.time > paused


def test_sim_controls_timer() -> None:
    sim = Engine()
    sim.start()
    time.sleep(0.01)
    t1 = sim.get_time()
    assert t1 > 0
    sim.pause()
    paused = sim.get_time()
    time.sleep(0.01)
    assert abs(sim.get_time() - paused) < 0.001
    sim.start()
    time.sleep(0.01)
    assert sim.get_time() > paused
    sim.reset()
    assert sim.get_time() == 0.0
