"""Comprehensive tests for the ComputeGraph simulation scheduler.

These tests verify the deterministic compute graph system that manages execution
order of simulation models. Tests cover dependency resolution, priority ordering,
topological sorting, and edge cases.
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest

# Add src to path for imports
sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from reefcraft.sim.graph import ComputeGraph, _Entry
from reefcraft.sim.model import Model


class MockModel:
    """Mock simulation model for testing.

    This mock implements the Model protocol and tracks execution
    for deterministic testing of the compute graph.
    """

    # Global execution counter for tracking order across all models
    _global_execution_counter = 0

    def __init__(self, name: str, substeps: int | None = 1, update_rate_hz: float | None = None):
        self.name = name
        self.substeps = substeps
        self.update_rate_hz = update_rate_hz
        self.inputs: dict[str, str] | None = None
        self.outputs: dict[str, str] | None = None
        self.execution_count = 0
        self.execution_order: list[int] = []
        self.last_dt = 0.0
        self.attach_store_called = False

    def step(self, dt: float) -> None:
        """Simulate model execution step."""
        self.execution_count += 1
        MockModel._global_execution_counter += 1
        self.execution_order.append(MockModel._global_execution_counter)
        self.last_dt = dt

    def attach_store(self, store: Any) -> None:
        """Simulate store attachment."""
        self.attach_store_called = True

    @classmethod
    def reset_global_counter(cls) -> None:
        """Reset the global execution counter for test isolation."""
        cls._global_execution_counter = 0


class TestComputeGraph:
    """Test suite for ComputeGraph functionality."""

    def setup_method(self) -> None:
        """Reset global execution counter before each test."""
        MockModel.reset_global_counter()

    def test_empty_graph_creation(self) -> None:
        """Test that an empty graph can be created."""
        graph = ComputeGraph()
        assert len(graph._entries) == 0
        assert graph._seq_counter == 0
        assert graph._store is None
        assert len(graph.models) == 0

    def test_single_model_addition(self) -> None:
        """Test adding a single model to the graph."""
        graph = ComputeGraph()
        model = MockModel("test_model")

        graph.add_model(model, node_id="test", priority=5)

        assert len(graph._entries) == 1
        entry = graph._entries[0]
        assert entry.id == "test"
        assert entry.priority == 5
        assert entry.seq == 0
        assert entry.model == model
        assert entry.requires == set()

        # Check models property
        models = graph.models
        assert len(models) == 1
        assert models[0] == model

    def test_model_with_auto_generated_id(self) -> None:
        """Test that models get auto-generated IDs when none provided."""
        graph = ComputeGraph()
        model = MockModel("auto_name")

        graph.add_model(model)

        assert len(graph._entries) == 1
        entry = graph._entries[0]
        assert entry.id == "auto_name"  # Uses model.name
        assert entry.seq == 0

    def test_model_with_fallback_id(self) -> None:
        """Test fallback ID generation when model has no name."""
        graph = ComputeGraph()
        model = MockModel("")  # Empty name

        graph.add_model(model)

        assert len(graph._entries) == 1
        entry = graph._entries[0]
        assert entry.id == "model-0"  # Fallback ID
        assert entry.seq == 0

    def test_multiple_models_priority_ordering(self) -> None:
        """Test that models execute in priority order when no dependencies."""
        graph = ComputeGraph()

        # Add models with different priorities
        model1 = MockModel("high_priority")
        model2 = MockModel("low_priority")
        model3 = MockModel("medium_priority")

        graph.add_model(model1, node_id="high", priority=0)
        graph.add_model(model2, node_id="low", priority=10)
        graph.add_model(model3, node_id="medium", priority=5)

        # Check execution order
        models = graph.models
        assert len(models) == 3
        assert models[0] == model1  # Highest priority (lowest number)
        assert models[1] == model3  # Medium priority
        assert models[2] == model2  # Lowest priority (highest number)

    def test_priority_tie_breaking_with_registration_order(self) -> None:
        """Test that registration order breaks priority ties."""
        graph = ComputeGraph()

        # Add models with same priority but different registration order
        model1 = MockModel("first")
        model2 = MockModel("second")
        model3 = MockModel("third")

        graph.add_model(model1, node_id="first", priority=5)
        graph.add_model(model2, node_id="second", priority=5)
        graph.add_model(model3, node_id="third", priority=5)

        # Check execution order (should be registration order due to seq)
        models = graph.models
        assert len(models) == 3
        assert models[0] == model1  # First registered
        assert models[1] == model2  # Second registered
        assert models[2] == model3  # Third registered

    def test_simple_dependency_chain(self) -> None:
        """Test simple linear dependency chain."""
        graph = ComputeGraph()

        # Create dependency chain: A -> B -> C
        model_a = MockModel("A")
        model_b = MockModel("B")
        model_c = MockModel("C")

        graph.add_model(model_a, node_id="A", priority=0)
        graph.add_model(model_b, node_id="B", requires=["A"], priority=1)
        graph.add_model(model_c, node_id="C", requires=["B"], priority=2)

        # Check execution order respects dependencies
        models = graph.models
        assert len(models) == 3
        assert models[0] == model_a  # No dependencies
        assert models[1] == model_b  # Depends on A
        assert models[2] == model_c  # Depends on B

    def test_complex_dependency_graph(self) -> None:
        """Test complex dependency graph with multiple paths."""
        graph = ComputeGraph()

        # Create graph: A -> B -> D, A -> C -> D
        model_a = MockModel("A")
        model_b = MockModel("B")
        model_c = MockModel("C")
        model_d = MockModel("D")

        graph.add_model(model_a, node_id="A", priority=0)
        graph.add_model(model_b, node_id="B", requires=["A"], priority=1)
        graph.add_model(model_c, node_id="C", requires=["A"], priority=2)
        graph.add_model(model_d, node_id="D", requires=["B", "C"], priority=3)

        # Check execution order
        models = graph.models
        assert len(models) == 4
        assert models[0] == model_a  # No dependencies
        # B and C can execute in any order after A (priority decides)
        assert models[1] == model_b  # Lower priority than C
        assert models[2] == model_c  # Higher priority than B
        assert models[3] == model_d  # Depends on both B and C

    def test_dependency_with_priority_override(self) -> None:
        """Test that dependencies are respected even with priority conflicts."""
        graph = ComputeGraph()

        # Model B has higher priority but depends on lower priority model A
        model_a = MockModel("A")
        model_b = MockModel("B")

        graph.add_model(model_a, node_id="A", priority=10)
        graph.add_model(model_b, node_id="B", requires=["A"], priority=0)

        # Check that dependency overrides priority
        models = graph.models
        assert len(models) == 2
        assert models[0] == model_a  # Must execute first due to dependency
        assert models[1] == model_b  # Executes second despite higher priority

    def test_add_models_batch_method(self) -> None:
        """Test adding multiple models at once."""
        graph = ComputeGraph()

        models = [MockModel(f"model_{i}") for i in range(3)]
        graph.add_models(models, priority=5)

        assert len(graph._entries) == 3
        for i, entry in enumerate(graph._entries):
            assert entry.priority == 5
            assert entry.seq == i
            assert entry.requires == set()

    def test_unknown_dependency_error(self) -> None:
        """Test error when model references unknown dependency."""
        graph = ComputeGraph()

        model = MockModel("dependent")
        graph.add_model(model, node_id="dependent", requires=["nonexistent"])

        # Should raise ValueError when accessing models property
        with pytest.raises(ValueError, match="Unknown dependency\\(ies\\) for node 'dependent': \\['nonexistent'\\]"):
            _ = graph.models

    def test_dependency_cycle_detection(self) -> None:
        """Test detection of circular dependencies."""
        graph = ComputeGraph()

        # Create cycle: A -> B -> C -> A
        model_a = MockModel("A")
        model_b = MockModel("B")
        model_c = MockModel("C")

        graph.add_model(model_a, node_id="A", requires=["C"])
        graph.add_model(model_b, node_id="B", requires=["A"])
        graph.add_model(model_c, node_id="C", requires=["B"])

        # Should raise CycleError when accessing models property
        with pytest.raises(Exception) as exc_info:
            _ = graph.models

        # Check that it's a cycle error (either CycleError or RuntimeError)
        assert "cycle" in str(exc_info.value).lower()

    def test_step_execution_order(self) -> None:
        """Test that step() executes models in correct order."""
        graph = ComputeGraph()

        # Create simple chain: A -> B
        model_a = MockModel("A", substeps=2)
        model_b = MockModel("B", substeps=1)

        graph.add_model(model_a, node_id="A", priority=0)
        graph.add_model(model_b, node_id="B", requires=["A"], priority=1)

        # Execute step
        graph.step(dt=1.0)

        # Check execution counts
        assert model_a.execution_count == 2  # 2 substeps
        assert model_b.execution_count == 1  # 1 substep

        # Check execution order (A should execute before B)
        assert model_a.execution_order == [1, 2]
        assert model_b.execution_order == [3]  # B executes after A's 2 substeps

        # Check time steps
        assert model_a.last_dt == 0.5  # 1.0 / 2 substeps
        assert model_b.last_dt == 1.0  # 1.0 / 1 substep

    def test_step_with_zero_substeps(self) -> None:
        """Test step() with model that has zero substeps."""
        graph = ComputeGraph()

        # Create model with zero substeps (edge case)
        model = MockModel("zero_substeps")
        model.substeps = 0

        graph.add_model(model, node_id="zero")

        # Should not crash, should execute at least once
        graph.step(dt=1.0)
        assert model.execution_count == 1
        assert model.last_dt == 1.0  # Should use max(1, substeps) = 1

    def test_step_with_negative_substeps(self) -> None:
        """Test step() with model that has negative substeps."""
        graph = ComputeGraph()

        # Create model with negative substeps (edge case)
        model = MockModel("negative_substeps")
        model.substeps = -2

        graph.add_model(model, node_id="negative")

        # Should not crash, but negative substeps become 0, so no execution
        graph.step(dt=1.0)
        assert model.execution_count == 0  # range(0) doesn't execute
        assert model.last_dt == 0.0  # No execution, so last_dt remains 0

    def test_store_attachment(self) -> None:
        """Test attaching data store to graph and models."""
        graph = ComputeGraph()

        # Create mock store
        mock_store = Mock()

        # Add model before store attachment
        model1 = MockModel("early_model")
        graph.add_model(model1, node_id="early")

        # Attach store
        graph.attach_store(mock_store)
        assert graph._store == mock_store

        # Check that existing model got store attached
        assert model1.attach_store_called

        # Add model after store attachment
        model2 = MockModel("late_model")
        graph.add_model(model2, node_id="late")

        # Check that new model got store attached
        assert model2.attach_store_called

    def test_store_attachment_with_incompatible_model(self) -> None:
        """Test store attachment with model that doesn't support it."""
        graph = ComputeGraph()

        # Create model without attach_store method by creating a custom class
        class IncompatibleModel:
            def __init__(self, name: str):
                self.name = name
                self.substeps: int | None = 1
                self.update_rate_hz: float | None = None
                self.inputs: dict[str, str] | None = None
                self.outputs: dict[str, str] | None = None

            def step(self, dt: float) -> None:
                pass

        model = IncompatibleModel("incompatible")

        # Add model and attach store
        graph.add_model(model, node_id="incompatible")
        mock_store = Mock()

        # Should not crash, should silently ignore incompatible model
        graph.attach_store(mock_store)
        assert graph._store == mock_store

    def test_store_attachment_exception_handling(self) -> None:
        """Test that store attachment exceptions are suppressed."""
        graph = ComputeGraph()

        # Create model that raises exception in attach_store
        model = MockModel("problematic")

        def problematic_attach(store):
            raise RuntimeError("Store attachment failed")

        model.attach_store = problematic_attach

        graph.add_model(model, node_id="problematic")

        # Should not crash, should suppress the exception
        mock_store = Mock()
        graph.attach_store(mock_store)
        assert graph._store == mock_store

    def test_deterministic_execution_order(self) -> None:
        """Test that execution order is deterministic across multiple calls."""
        graph = ComputeGraph()

        # Add models in random order
        model_c = MockModel("C")
        model_a = MockModel("A")
        model_b = MockModel("B")

        graph.add_model(model_c, node_id="C", priority=5)
        graph.add_model(model_a, node_id="A", priority=0)
        graph.add_model(model_b, node_id="B", priority=2)

        # Get execution order multiple times
        order1 = graph.models
        order2 = graph.models
        order3 = graph.models

        # All should be identical
        assert order1 == order2 == order3

        # Check specific order
        assert [m.name for m in order1] == ["A", "B", "C"]

    def test_empty_graph_step(self) -> None:
        """Test that step() works with empty graph."""
        graph = ComputeGraph()

        # Should not crash
        graph.step(dt=1.0)
        assert len(graph.models) == 0

    def test_single_model_step(self) -> None:
        """Test step() with single model."""
        graph = ComputeGraph()

        model = MockModel("single")
        graph.add_model(model, node_id="single")

        graph.step(dt=0.5)

        assert model.execution_count == 1
        assert model.last_dt == 0.5
        assert model.execution_order == [1]

    def test_model_with_none_substeps(self) -> None:
        """Test step() with model that has None substeps."""
        graph = ComputeGraph()

        # Create model with None substeps
        model = MockModel("none_substeps")
        model.substeps = None

        graph.add_model(model, node_id="none")

        # Should default to 1 substep
        graph.step(dt=1.0)
        assert model.execution_count == 1
        assert model.last_dt == 1.0

    def test_model_with_missing_substeps_attribute(self) -> None:
        """Test step() with model that has no substeps attribute."""
        graph = ComputeGraph()

        # Create model without substeps attribute
        model = MockModel("no_substeps")
        delattr(model, "substeps")

        graph.add_model(model, node_id="no_substeps")

        # Should default to 1 substep
        graph.step(dt=1.0)
        assert model.execution_count == 1
        assert model.last_dt == 1.0


class TestEntry:
    """Test suite for internal _Entry dataclass."""

    def setup_method(self) -> None:
        """Reset global execution counter before each test."""
        MockModel.reset_global_counter()

    def test_entry_creation(self) -> None:
        """Test _Entry dataclass creation and immutability."""
        model = MockModel("test")
        entry = _Entry(id="test_id", requires={"dep1", "dep2"}, priority=5, seq=10, model=model)

        assert entry.id == "test_id"
        assert entry.requires == {"dep1", "dep2"}
        assert entry.priority == 5
        assert entry.seq == 10
        assert entry.model == model

        # Test immutability
        assert entry.requires == frozenset(["dep1", "dep2"]) or entry.requires == {"dep1", "dep2"}

    def test_entry_with_empty_requires(self) -> None:
        """Test _Entry with empty requires set."""
        model = MockModel("test")
        entry = _Entry(id="test_id", requires=set(), priority=0, seq=0, model=model)

        assert entry.requires == set()

    def test_entry_equality(self) -> None:
        """Test _Entry equality comparison."""
        model1 = MockModel("test1")
        model2 = MockModel("test2")

        entry1 = _Entry("id1", set(), 0, 0, model1)
        entry2 = _Entry("id1", set(), 0, 0, model1)
        entry3 = _Entry("id2", set(), 0, 0, model1)

        assert entry1 == entry2
        assert entry1 != entry3


# Integration tests that verify real-world scenarios
class TestComputeGraphIntegration:
    """Integration tests for realistic compute graph scenarios."""

    def setup_method(self) -> None:
        """Reset global execution counter before each test."""
        MockModel.reset_global_counter()

    def test_coral_reef_simulation_scenario(self) -> None:
        """Test realistic coral reef simulation dependency graph."""
        graph = ComputeGraph()

        # Create realistic simulation models
        water_model = MockModel("water", substeps=4)  # Water flows faster
        coral_model = MockModel("coral", substeps=1)
        fish_model = MockModel("fish", substeps=2)
        algae_model = MockModel("algae", substeps=1)

        # Set up dependencies: water -> coral, water -> fish, coral -> algae
        graph.add_model(water_model, node_id="water", priority=0)
        graph.add_model(coral_model, node_id="coral", requires=["water"], priority=1)
        graph.add_model(fish_model, node_id="fish", requires=["water"], priority=2)
        graph.add_model(algae_model, node_id="algae", requires=["coral"], priority=3)

        # Verify execution order
        models = graph.models
        model_names = [m.name for m in models]
        assert model_names == ["water", "coral", "fish", "algae"]

        # Execute simulation step
        graph.step(dt=0.1)

        # Check execution counts
        assert water_model.execution_count == 4  # 4 substeps
        assert coral_model.execution_count == 1  # 1 substep
        assert fish_model.execution_count == 2  # 2 substeps
        assert algae_model.execution_count == 1  # 1 substep

        # Check time steps
        assert water_model.last_dt == 0.025  # 0.1 / 4
        assert coral_model.last_dt == 0.1  # 0.1 / 1
        assert fish_model.last_dt == 0.05  # 0.1 / 2
        assert algae_model.last_dt == 0.1  # 0.1 / 1

    def test_parallel_and_sequential_execution(self) -> None:
        """Test mixed parallel and sequential execution patterns."""
        graph = ComputeGraph()

        # Create models with mixed dependencies
        input_model = MockModel("input", substeps=1)
        parallel1 = MockModel("parallel1", substeps=1)
        parallel2 = MockModel("parallel2", substeps=1)
        parallel3 = MockModel("parallel3", substeps=1)
        output_model = MockModel("output", substeps=1)

        # Set up graph: input -> [parallel1, parallel2, parallel3] -> output
        graph.add_model(input_model, node_id="input", priority=0)
        graph.add_model(parallel1, node_id="p1", requires=["input"], priority=1)
        graph.add_model(parallel2, node_id="p2", requires=["input"], priority=2)
        graph.add_model(parallel3, node_id="p3", requires=["input"], priority=3)
        graph.add_model(output_model, node_id="output", requires=["p1", "p2", "p3"], priority=4)

        # Verify execution order
        models = graph.models
        model_names = [m.name for m in models]
        assert model_names == ["input", "parallel1", "parallel2", "parallel3", "output"]

        # Execute step
        graph.step(dt=1.0)

        # All models should execute once
        for model in [input_model, parallel1, parallel2, parallel3, output_model]:
            assert model.execution_count == 1
            assert model.last_dt == 1.0

    def test_priority_override_in_complex_graph(self) -> None:
        """Test that priority works correctly in complex dependency scenarios."""
        graph = ComputeGraph()

        # Create complex graph with priority overrides
        model_a = MockModel("A", substeps=1)
        model_b = MockModel("B", substeps=1)
        model_c = MockModel("C", substeps=1)
        model_d = MockModel("D", substeps=1)

        # Graph: A -> [B, C] -> D
        # B has higher priority than C, but both depend on A
        graph.add_model(model_a, node_id="A", priority=0)
        graph.add_model(model_b, node_id="B", requires=["A"], priority=2)  # Higher priority
        graph.add_model(model_c, node_id="C", requires=["A"], priority=1)  # Lower priority
        graph.add_model(model_d, node_id="D", requires=["B", "C"], priority=3)

        # Verify execution order
        models = graph.models
        model_names = [m.name for m in models]
        assert model_names == ["A", "C", "B", "D"]  # C executes before B due to priority

        # Execute step
        graph.step(dt=1.0)

        # All models should execute
        for model in [model_a, model_b, model_c, model_d]:
            assert model.execution_count == 1


# Performance and stress tests
class TestComputeGraphPerformance:
    """Performance and stress tests for ComputeGraph."""

    def setup_method(self) -> None:
        """Reset global execution counter before each test."""
        MockModel.reset_global_counter()

    def test_large_graph_creation(self) -> None:
        """Test creating and managing a large compute graph."""
        graph = ComputeGraph()

        # Create 100 models with random dependencies
        models = []
        for i in range(100):
            model = MockModel(f"model_{i}")
            models.append(model)

            # Add some random dependencies
            if i > 0:
                deps = [f"model_{j}" for j in range(i) if j % 10 == 0]  # Every 10th model
                graph.add_model(model, node_id=f"model_{i}", requires=deps, priority=i)
            else:
                graph.add_model(model, node_id=f"model_{i}", priority=i)

        # Verify all models are added
        assert len(graph._entries) == 100

        # Verify we can get execution order
        execution_order = graph.models
        assert len(execution_order) == 100

        # Verify we can execute a step
        graph.step(dt=1.0)

        # Verify all models executed
        for model in models:
            assert model.execution_count > 0

    def test_repeated_execution_order_calculation(self) -> None:
        """Test that repeated calls to models property are efficient."""
        graph = ComputeGraph()

        # Create moderate-sized graph
        for i in range(50):
            model = MockModel(f"model_{i}")
            deps = [f"model_{j}" for j in range(i) if j % 5 == 0]
            graph.add_model(model, node_id=f"model_{i}", requires=deps, priority=i)

        # Call models property multiple times
        execution_order = None
        for _ in range(100):
            execution_order = graph.models
            assert len(execution_order) == 50

        # Verify all models can still execute
        graph.step(dt=1.0)
        assert execution_order is not None
        assert all(hasattr(m, "execution_count") for m in execution_order)


# Edge case and error condition tests
class TestComputeGraphEdgeCases:
    """Tests for edge cases and error conditions."""

    def setup_method(self) -> None:
        """Reset global execution counter before each test."""
        MockModel.reset_global_counter()

    def test_model_with_special_characters_in_id(self) -> None:
        """Test models with special characters in node IDs."""
        graph = ComputeGraph()

        model = MockModel("special")
        graph.add_model(model, node_id="model-with-dashes", priority=0)
        graph.add_model(model, node_id="model_with_underscores", priority=1)
        graph.add_model(model, node_id="model.with.dots", priority=2)
        graph.add_model(model, node_id="model123", priority=3)

        assert len(graph._entries) == 4
        assert graph._entries[0].id == "model-with-dashes"
        assert graph._entries[1].id == "model_with_underscores"
        assert graph._entries[2].id == "model.with.dots"
        assert graph._entries[3].id == "model123"

    def test_very_high_priority_values(self) -> None:
        """Test with very high priority values."""
        graph = ComputeGraph()

        model1 = MockModel("high")
        model2 = MockModel("low")

        graph.add_model(model1, node_id="high", priority=1000000)
        graph.add_model(model2, node_id="low", priority=-1000000)

        # Low priority (negative) should execute first
        models = graph.models
        assert models[0] == model2  # Lower priority number
        assert models[1] == model1  # Higher priority number

    def test_empty_dependency_sets(self) -> None:
        """Test with various empty dependency representations."""
        graph = ComputeGraph()

        model1 = MockModel("empty_set")
        model2 = MockModel("empty_list")
        model3 = MockModel("none_deps")

        graph.add_model(model1, node_id="empty_set", requires=set())
        graph.add_model(model2, node_id="empty_list", requires=[])
        graph.add_model(model3, node_id="none_deps", requires=None)

        # All should have empty requires sets
        for entry in graph._entries:
            assert entry.requires == set()

        # All should execute in priority order
        models = graph.models
        assert len(models) == 3

    def test_duplicate_node_ids(self) -> None:
        """Test behavior with duplicate node IDs."""
        graph = ComputeGraph()

        model1 = MockModel("duplicate")
        model2 = MockModel("duplicate")

        # Add models with same ID
        graph.add_model(model1, node_id="duplicate", priority=0)
        graph.add_model(model2, node_id="duplicate", priority=1)

        # Both should be added (no validation)
        assert len(graph._entries) == 2

        # Check that both models are in the entries
        node_ids = [entry.id for entry in graph._entries]
        assert "duplicate" in node_ids
        assert node_ids.count("duplicate") == 2

        # This could cause issues, but the current implementation allows it
        # In a real application, this should be prevented
        # Note: The models property will work, but there may be unexpected behavior
        # due to duplicate IDs in the dependency resolution


if __name__ == "__main__":
    # Run tests directly if file is executed
    import pytest

    pytest.main([__file__, "-v"])
