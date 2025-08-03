import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

import matplotlib.pyplot as plt
import numpy as np
import warp as wp

from reefcraft.sim.simple_porag import SimpleP

"""Test SimpleP class."""


def test_add_polyp() -> None:
    """Test add polyp function"""
    pass


def test_growth_function() -> None:
    """Test Growth Function."""
    pass
