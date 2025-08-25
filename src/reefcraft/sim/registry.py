# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Registry for simulation operators and models.

This module provides a registry system for managing simulation models and operators.
The OperatorRegistry class allows dynamic registration and instantiation of model
classes by name, enabling flexible configuration of simulation components.

The registry supports:
- Dynamic registration of model classes
- Name-based lookup and instantiation
- Automatic parameter passing to constructors
- Listing of all available model types
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reefcraft.sim.model import Model


class OperatorRegistry:
    """Registry mapping operator names to model classes.

    The OperatorRegistry provides a centralized way to manage and instantiate
    simulation models. It maintains a mapping between human-readable names
    and model classes, allowing models to be created dynamically based on
    configuration or user input.

    This registry is particularly useful for:
    - Loading models from configuration files
    - Supporting plugin architectures
    - Enabling runtime model selection
    - Maintaining a catalog of available models

    Attributes:
        _name_to_cls: Internal mapping from names to model classes.
    """

    def __init__(self) -> None:
        """Initialize an empty operator registry.

        Creates a new registry with no registered models. Models can be
        added using the register() method.
        """
        self._name_to_cls: dict[str, type["Model"]] = {}

    def register(self, name: str, op_cls: type["Model"]) -> None:
        """Register a model class with a given name.

        Associates a human-readable name with a model class, making it
        available for later lookup and instantiation. If a name is already
        registered, it will be overwritten with the new class.

        Args:
            name: Human-readable identifier for the model class.
            op_cls: The model class to register.

        Example:
            >>> registry = OperatorRegistry()
            >>> from reefcraft.sim.models.water_model import WaterModel
            >>> registry.register("water", WaterModel)
            >>> print("water" in registry.list())  # True
        """
        self._name_to_cls[name] = op_cls

    def list(self) -> list[str]:
        """Get a sorted list of all registered model names.

        Returns all the names that have been registered with this registry,
        sorted alphabetically for consistent ordering.

        Returns:
            List of registered model names in alphabetical order.

        Example:
            >>> registry = OperatorRegistry()
            >>> registry.register("coral", CoralModel)
            >>> registry.register("water", WaterModel)
            >>> names = registry.list()
            >>> print(names)  # ['coral', 'water']
        """
        return sorted(self._name_to_cls.keys())

    def get_class(self, name: str) -> type["Model"]:
        """Retrieve a registered model class by name.

        Looks up a model class that was previously registered with the
        given name. Raises a KeyError if the name is not found.

        Args:
            name: The name of the registered model class.

        Returns:
            The model class associated with the given name.

        Raises:
            KeyError: If no model class is registered with the given name.

        Example:
            >>> registry = OperatorRegistry()
            >>> registry.register("coral", CoralModel)
            >>> coral_cls = registry.get_class("coral")
            >>> print(coral_cls.__name__)  # 'CoralModel'
        """
        return self._name_to_cls[name]

    def create(self, name: str, **kwargs: Any) -> "Model":
        """Create an instance of a registered model class.

        Instantiates a model of the specified type, passing any provided
        keyword arguments to the model's constructor. This is a convenience
        method that combines lookup and instantiation.

        Args:
            name: The name of the registered model class.
            **kwargs: Keyword arguments to pass to the model constructor.

        Returns:
            A new instance of the specified model class.

        Raises:
            KeyError: If no model class is registered with the given name.

        Example:
            >>> registry = OperatorRegistry()
            >>> registry.register("coral", CoralModel)
            >>> # Create a coral model with specific parameters
            >>> coral = registry.create("coral", growth_rate=0.1, size=10.0)
            >>> print(type(coral))  # <class 'CoralModel'>
        """
        cls = self.get_class(name)
        return cls(**kwargs)
