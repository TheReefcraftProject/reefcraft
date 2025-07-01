import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.sim.sim import Sim
from app.sim.timer import Timer


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
    sim = Sim()
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
