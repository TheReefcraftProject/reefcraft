# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Compute graph scheduler for loosely-coupled simulation models.

This module provides a deterministic compute graph system that manages the execution
order of simulation models. The ComputeGraph class supports both simple priority-based
ordering and complex dependency-aware execution using declarative constraints.

The graph ensures that models execute in the correct order by:
1. Respecting explicit dependency declarations via "requires" constraints
2. Using priority values as tie-breakers for independent models
3. Maintaining deterministic execution order across runs

Example:
    >>> graph = ComputeGraph()
    >>> # Add models with dependencies
    >>> graph.add_model(water_model, node_id="water", priority=0)
    >>> graph.add_model(coral_model, node_id="coral", requires=["water"], priority=1)
    >>> # Execute in dependency order
    >>> graph.step(dt=0.01)
"""

from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass
from graphlib import TopologicalSorter
from typing import TYPE_CHECKING

from reefcraft.sim.model import Model

if TYPE_CHECKING:  # Avoid import cycles during runtime
    from reefcraft.sim.data_store import DataStore


@dataclass(frozen=True)
class _Entry:
    """Internal entry representing a model in the compute graph.

    This dataclass stores all the metadata needed to manage model execution
    order, including dependencies, priorities, and registration sequence.

    Attributes:
        id: Unique identifier for the model node
        requires: Set of node IDs that must execute before this model
        priority: Execution priority (lower values execute first)
        seq: Registration sequence number for tie-breaking
        model: The actual model instance to execute
    """

    id: str
    requires: set[str]
    priority: int
    seq: int
    model: Model


class ComputeGraph:
    """Deterministic compute graph with optional dependency constraints.

    The ComputeGraph manages the execution order of simulation models using
    a combination of dependency constraints and priority values. It ensures
    deterministic execution by using topological sorting for dependencies
    and stable sorting for priority-based ordering.

    The graph supports two execution modes:
    - Simple priority ordering: Models execute in priority order
    - Dependency-aware ordering: Models wait for dependencies to complete

    Attributes:
        _entries: List of graph entries containing model metadata
        _seq_counter: Counter for assigning unique sequence numbers
        _store: Optional data store for model I/O operations
    """

    def __init__(self) -> None:
        """Create an empty compute graph.

        Initializes a new compute graph with no models. The graph is ready
        to accept models immediately after creation.
        """
        self._entries: list[_Entry] = []
        self._seq_counter: int = 0
        self._store: "DataStore | None" = None  # Lazy-injected DataStore

    def attach_store(self, store: "DataStore") -> None:
        """Attach a shared data store for model I/O operations.

        Connects a data store to the compute graph, which will be shared
        with all models that support store attachment. This enables models
        to read from and write to a common data store during execution.

        Args:
            store: The data store instance to attach to the graph.

        Note:
            Only models that implement an `attach_store` method will receive
            the store. Models without this method are silently ignored.

        Example:
            >>> graph = ComputeGraph()
            >>> data_store = DataStore()
            >>> graph.attach_store(data_store)
            >>> # All compatible models now have access to the store
        """
        self._store = store
        # Attach to existing models if they accept a store
        for entry in self._entries:
            model = entry.model
            if hasattr(model, "attach_store"):
                with suppress(Exception):
                    model.attach_store(store)  # type: ignore[attr-defined]

    def add_model(self, model: Model, *, node_id: str | None = None, requires: Iterable[str] | None = None, priority: int = 0) -> None:
        """Register a model for execution in the compute graph.

        Adds a model to the graph with specified execution constraints.
        The model will be executed according to its dependencies and priority
        during the graph's step() method.

        Args:
            model: The model instance to add to the graph.
            node_id: Unique identifier for the model node. If None, attempts
                     to use model.name or generates a default ID.
            requires: Iterable of node IDs that must execute before this model.
                      If None, the model has no dependencies.
            priority: Execution priority for tie-breaking. Lower values execute
                      first when multiple models are ready.

        Note:
            The node_id must be unique within the graph. If a duplicate ID is
            provided, it may cause unexpected behavior.

        Example:
            >>> graph = ComputeGraph()
            >>> # Add a water model with high priority
            >>> graph.add_model(water_model, node_id="water", priority=0)
            >>> # Add a coral model that depends on water
            >>> graph.add_model(coral_model, node_id="coral",
            ...                requires=["water"], priority=1)
        """
        nid = node_id or getattr(model, "name", None) or f"model-{self._seq_counter}"
        reqs = set(requires or [])
        entry = _Entry(id=nid, requires=reqs, priority=priority, seq=self._seq_counter, model=model)
        self._entries.append(entry)
        # Best-effort store attach for newly added models
        if self._store is not None and hasattr(model, "attach_store"):
            with suppress(Exception):
                model.attach_store(self._store)  # type: ignore[attr-defined]
        self._seq_counter += 1

    def add_models(self, models: Iterable[Model], *, priority: int = 0) -> None:
        """Register multiple models with the same priority and no dependencies.

        A convenience method for adding multiple independent models that
        can execute in any order relative to each other.

        Args:
            models: Iterable of model instances to add.
            priority: Execution priority for all models in the batch.

        Example:
            >>> graph = ComputeGraph()
            >>> independent_models = [model1, model2, model3]
            >>> graph.add_models(independent_models, priority=5)
            >>> # All models have priority 5 and no dependencies
        """
        for m in models:
            self.add_model(m, priority=priority)

    def _topo_sorted_entries(self) -> list[_Entry]:
        """Return entries sorted by dependencies, then priority, then registration order.

        This internal method performs topological sorting to respect declared
        dependencies, then uses priority and registration order for tie-breaking.
        The result ensures deterministic execution order across multiple runs.

        Uses graphlib.TopologicalSorter to respect declared dependencies; when
        multiple nodes are ready, we choose deterministically by (priority, seq).

        Returns:
            List of entries in execution order.

        Raises:
            ValueError: If an entry declares an unknown dependency id.
            RuntimeError: If a dependency cycle is detected.

        Note:
            This method is called internally by the models property and step()
            method. It performs validation and raises descriptive errors for
            invalid graph configurations.
        """
        by_id: dict[str, _Entry] = {e.id: e for e in self._entries}
        # Validate dependencies reference known nodes
        for e in self._entries:
            unknown = e.requires - set(by_id.keys())
            if unknown:
                raise ValueError(f"Unknown dependency(ies) for node '{e.id}': {sorted(unknown)}")

        ts = TopologicalSorter()
        for e in self._entries:
            ts.add(e.id, *e.requires)

        ts.prepare()
        ordered: list[_Entry] = []
        ready_ids = list(ts.get_ready())
        ready = sorted((by_id[rid] for rid in ready_ids), key=lambda x: (x.priority, x.seq))

        while ready:
            current = ready.pop(0)
            ordered.append(current)
            ts.done(current.id)
            new_ready_ids = list(ts.get_ready())
            ready.extend(by_id[rid] for rid in new_ready_ids)
            ready.sort(key=lambda x: (x.priority, x.seq))

        if ts.is_active():
            # Nodes remain unprocessed due to a cycle
            raise RuntimeError("Dependency cycle detected in ComputeGraph.")

        return ordered

    @property
    def models(self) -> list[Model]:
        """Models in the current dependency-respecting execution order.

        Returns a list of models ordered according to their dependencies
        and priorities. This property recalculates the order each time it's
        accessed, ensuring it's always up to date with the current graph state.

        Returns:
            List of models in execution order.

        Example:
            >>> graph = ComputeGraph()
            >>> graph.add_model(water_model, node_id="water")
            >>> graph.add_model(coral_model, node_id="coral", requires=["water"])
            >>> execution_order = graph.models
            >>> print([model.name for model in execution_order])
            # Output: ['water', 'coral']
        """
        return [e.model for e in self._topo_sorted_entries()]

    def step(self, dt: float) -> None:
        """Step all registered models in dependency-respecting order.

        Executes one simulation step for all models in the graph. Models
        are executed in the order determined by their dependencies and
        priorities. Each model's step() method is called with the appropriate
        time step.

        The method honors optional `substeps` on models to repeat work within
        a frame, which is useful for models that need finer temporal resolution.

        Args:
            dt: Time step for the simulation frame in seconds.

        Example:
            >>> graph = ComputeGraph()
            >>> graph.add_model(water_model)
            >>> graph.add_model(coral_model, requires=["water"])
            >>> # Execute one simulation step
            >>> graph.step(dt=0.01)
            >>> # Models execute in dependency order: water first, then coral
        """
        for entry in self._topo_sorted_entries():
            model = entry.model
            substeps = getattr(model, "substeps", None) or 1
            sub_dt = dt / max(1, substeps)
            for _ in range(int(substeps)):
                model.step(sub_dt)
