import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from reefcraft.sim.engine import Engine
from reefcraft.sim.growth_model_factory import CoralModel


def test_default_coral_creation() -> None:
    """Test that a default coral is created on startup with the llabres model."""
    with Engine(dt=0.01) as engine:
        # Check that exactly one coral was created
        assert len(engine.state.corals) == 1

        # Check that it's the llabres model
        coral = engine.state.corals[0]
        assert coral.model == "LLABRES"
        assert coral._model_enum == CoralModel.LLABRES

        # Check that it's registered in the compute graph
        coral_node_ids = [entry.id for entry in engine.state.graph._entries]
        assert "coral.0" in coral_node_ids


# def test_sim_controls_timer() -> None:
#     sim = Engine()
#     sim.play()
#     time.sleep(0.01)
#     t1 = sim.get_time()
#     assert t1 > 0
#     sim.pause()
#     paused = sim.get_time()
#     time.sleep(0.01)
#     assert abs(sim.get_time() - paused) < 0.001
#     sim.play()
#     time.sleep(0.01)
#     assert sim.get_time() > paused
#     sim.reset()
#     assert sim.get_time() == 0.0
