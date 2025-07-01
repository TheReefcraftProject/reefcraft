"""Taichi-based simulation utilities for Reefcraft."""

from __future__ import annotations

import math
import random
import taichi as ti

# Initialize Taichi in CPU mode for cross-platform consistency
ti.init(arch=ti.cpu)

_rng = random.Random()

# Simulation state fields accessible to Taichi kernels
_cycle_start = ti.field(dtype=ti.f32, shape=())
_period = ti.field(dtype=ti.f32, shape=())
_amplitude = ti.field(dtype=ti.f32, shape=())

# Python-side copies for update logic
_cycle_start_py = 0.0
_period_py = 1.0
_amplitude_py = 1.0

def _reset_cycle() -> None:
    global _period_py, _amplitude_py
    _period_py = _rng.uniform(0.5, 1.5)
    _amplitude_py = _rng.uniform(0.1, 1.0)
    _period[None] = _period_py
    _amplitude[None] = _amplitude_py

def seed(in_seed: int) -> None:
    """Seed the random number generator used by the simulator."""
    global _cycle_start_py
    _rng.seed(in_seed)
    _cycle_start_py = 0.0
    _cycle_start[None] = 0.0
    _reset_cycle()

def _advance_time(in_time: float) -> None:
    global _cycle_start_py
    while in_time >= _cycle_start_py + _period_py:
        _cycle_start_py += _period_py
        _cycle_start[None] = _cycle_start_py
        _reset_cycle()

def sim_value(in_time: float) -> float:
    """Generate a randomly varying sine value at ``in_time``."""
    _advance_time(float(in_time))
    theta = 2.0 * math.pi * (in_time - _cycle_start_py) / _period_py
    return _amplitude_py * float(ti.sin(theta))

# Initialize with a default seed for deterministic runs
seed(12345)

