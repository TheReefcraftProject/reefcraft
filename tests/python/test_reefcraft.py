# -----------------------------------------------------------------------------
# Copyright (c) 2025
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

import math

import reefcraft


def test_sim_value_returns_finite_float() -> None:
    """sim_value() should return a float within expected bounds at key times."""
    for in_time in [0.0, 0.3, 1.0, 2.5, 5.0, 7.7, 10.0]:
        value = reefcraft.sim_value(in_time)
        assert isinstance(value, float), f"Not a float: {value}"
        assert math.isfinite(value), f"Not finite: {value}"
        assert -1.05 <= value <= 1.05, f"Out of bounds: {value}"


def test_sim_value_varies_over_time() -> None:
    """sim_value() output should vary over time."""
    values = [reefcraft.sim_value(i * 0.2) for i in range(20)]
    unique_values = set(values)
    assert len(unique_values) > 1, "Output does not vary over time"


def test_sim_value_is_reproducible_with_seed() -> None:
    """Seeding should result in reproducible output."""
    in_seed = 123456
    sample_times = [i * 0.1 for i in range(20)]

    reefcraft.seed(in_seed)
    first_run = [reefcraft.sim_value(t) for t in sample_times]

    reefcraft.seed(in_seed)
    second_run = [reefcraft.sim_value(t) for t in sample_times]

    assert first_run == second_run, f"Seeded runs differ:\n{first_run}\nvs\n{second_run}"


def test_sim_value_changes_with_different_seed() -> None:
    """Different seeds should lead to different output sequences."""
    sample_times = [i * 0.1 for i in range(20)]

    reefcraft.seed(111)
    values_one = [reefcraft.sim_value(t) for t in sample_times]

    reefcraft.seed(222)
    values_two = [reefcraft.sim_value(t) for t in sample_times]

    assert values_one != values_two, "Output did not change with new seed"
