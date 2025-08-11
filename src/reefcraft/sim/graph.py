# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Compute graph scheduler for loosely-coupled simulation models.

Supports deterministic execution using either:
- simple priority ordering, or
- dependency-aware ordering via declarative "requires" constraints (DAG).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING
from graphlib import TopologicalSorter

if TYPE_CHECKING:  # Avoid import cycles during runtime
    from reefcraft.sim.model import Model
    from reefcraft.sim.data_store import DataStore

from reefcraft.sim.model import Model


@dataclass(frozen=True)
class _Entry:
    id: str
    requires: set[str]
    priority: int
    seq: int
    model: Model


class ComputeGraph:
    """Deterministic compute graph with optional dependency constraints."""

    def __init__(self) -> None:
        """Create an empty compute graph."""
        self._entries: list[_Entry] = []
        self._seq_counter: int = 0
        self._store = None  # Lazy-injected DataStore

    def attach_store(self, store: DataStore) -> None:
        """Attach a shared data store for model I/O."""
        self._store = store
        # Attach to existing models if they accept a store
        for entry in self._entries:
            model = entry.model
            if hasattr(model, "attach_store"):
                try:
                    model.attach_store(store)  # type: ignore[attr-defined]
                except Exception:
                    # Models are allowed to ignore or delay store usage
                    pass

    def add_model(self, model: Model, *, node_id: str | None = None, requires: Iterable[str] | None = None, priority: int = 0) -> None:
        """Register a model for execution.

        - node_id: unique identifier; defaults to model.name
        - requires: set of ids that must execute before this one
        - priority: tie-breaker for nodes without dependencies; lower runs earlier
        """
        nid = node_id or getattr(model, "name", None) or f"model-{self._seq_counter}"
        reqs = set(requires or [])
        entry = _Entry(id=nid, requires=reqs, priority=priority, seq=self._seq_counter, model=model)
        self._entries.append(entry)
        # Best-effort store attach for newly added models
        if self._store is not None and hasattr(model, "attach_store"):
            try:
                model.attach_store(self._store)  # type: ignore[attr-defined]
            except Exception:
                pass
        self._seq_counter += 1

    def add_models(self, models: Iterable[Model], *, priority: int = 0) -> None:
        """Register multiple models with the same priority."""
        for m in models:
            self.add_model(m, priority=priority)

    def _topo_sorted_entries(self) -> list[_Entry]:
        """Return entries sorted by dependencies, then priority, then registration order.

        Uses graphlib.TopologicalSorter to respect declared dependencies; when
        multiple nodes are ready, we choose deterministically by (priority, seq).

        Raises:
            ValueError: If an entry declares an unknown dependency id.
            RuntimeError: If a dependency cycle is detected.
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
        """Models in the current dependency-respecting execution order."""
        return [e.model for e in self._topo_sorted_entries()]

    def step(self, dt: float) -> None:
        """Step all registered models in dependency-respecting order.

        Honors optional `substeps` on models to repeat work within a frame.
        """
        for entry in self._topo_sorted_entries():
            model = entry.model
            substeps = getattr(model, "substeps", None) or 1
            sub_dt = dt / max(1, substeps)
            for _ in range(int(substeps)):
                model.step(sub_dt)



