# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Simple operator registry for discoverability and instantiation by name."""

from __future__ import annotations

from typing import Any, Callable, Dict, Type

from reefcraft.sim.model import Model


class OperatorRegistry:
    """Registry mapping operator names to classes."""

    def __init__(self) -> None:
        self._name_to_cls: Dict[str, Type[Model]] = {}

    def register(self, name: str, op_cls: Type[Model]) -> None:
        self._name_to_cls[name] = op_cls

    def list(self) -> list[str]:
        return sorted(self._name_to_cls.keys())

    def get_class(self, name: str) -> Type[Model]:
        return self._name_to_cls[name]

    def create(self, name: str, **kwargs: Any) -> Model:
        cls = self.get_class(name)
        return cls(**kwargs)  # type: ignore[misc]


