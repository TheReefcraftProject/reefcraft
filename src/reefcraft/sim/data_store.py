# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Lightweight versioned key-value data store for model inputs/outputs.

This module provides a simple, versioned key-value storage system designed for
storing simulation model inputs, outputs, and intermediate data. The DataStore
class maintains version numbers for each key, allowing tracking of data changes
over time.

Example:
    >>> store = DataStore()
    >>> version = store.put("temperature", 25.5)
    >>> print(f"Stored temperature data, version: {version}")
    >>> value = store.try_get("temperature")
    >>> print(f"Retrieved: {value}")
"""

from __future__ import annotations

from typing import Any


class DataStore:
    """A simple versioned dictionary-like registry with string keys.

    The DataStore provides a thread-safe, versioned storage mechanism for
    simulation data. Each key-value pair maintains a version counter that
    increments with each update, allowing clients to track data freshness
    and detect changes.

    Attributes:
        _data: Internal dictionary storing the key-value pairs
        _versions: Internal dictionary tracking version numbers for each key
    """

    def __init__(self) -> None:
        """Initialize an empty DataStore.

        Creates a new DataStore instance with empty data and version dictionaries.
        """
        self._data: dict[str, Any] = {}
        self._versions: dict[str, int] = {}

    # Versioned API ---------------------------------------------------------
    def put(self, key: str, value: Any) -> int:
        """Store a value and bump its version, returning the new version.

        This is the primary method for storing data in the DataStore. Each call
        to put() increments the version counter for the specified key, allowing
        clients to track when data was last modified.

        Args:
            key: String identifier for the data item. Must be a valid string.
            value: The data to store. Can be any Python object.

        Returns:
            The new version number for this key (incremented from previous value).

        Example:
            >>> store = DataStore()
            >>> v1 = store.put("coral_growth", 0.15)
            >>> v2 = store.put("coral_growth", 0.18)
            >>> print(f"Version increased from {v1} to {v2}")
        """
        self._data[key] = value
        self._versions[key] = self._versions.get(key, 0) + 1
        return self._versions[key]

    def try_get(self, key: str) -> Any | None:
        """Return value or None if missing.

        Safely retrieves a value from the store without raising exceptions.
        Returns None if the key doesn't exist, making it suitable for
        cases where missing data is expected.

        Args:
            key: String identifier for the data item to retrieve.

        Returns:
            The stored value if the key exists, None otherwise.

        Example:
            >>> store = DataStore()
            >>> store.put("water_temp", 22.5)
            >>> temp = store.try_get("water_temp")
            >>> missing = store.try_get("nonexistent_key")
            >>> print(f"Water temp: {temp}, Missing: {missing}")
        """
        return self._data.get(key)

    def version(self, key: str) -> int:
        """Return the current version for a key (0 if unseen).

        Retrieves the current version number for a specific key. Returns 0
        for keys that have never been stored, allowing clients to distinguish
        between new and existing data.

        Args:
            key: String identifier for the data item.

        Returns:
            The current version number (1 or higher for stored keys, 0 for new keys).

        Example:
            >>> store = DataStore()
            >>> print(f"Initial version: {store.version('new_key')}")
            >>> store.put('new_key', 'value')
            >>> print(f"After first put: {store.version('new_key')}")
        """
        return self._versions.get(key, 0)

    # Back-compat thin wrappers --------------------------------------------
    def set(self, key: str, value: Any) -> None:
        """Store a value without returning version (backward compatibility).

        This method provides backward compatibility with older code that
        expects a set() method. It calls put() internally but discards
        the version number return value.

        Args:
            key: String identifier for the data item.
            value: The data to store.

        Note:
            This method is deprecated. Use put() for new code to get version tracking.
        """
        self.put(key, value)

    def get(self, key: str, default: Any | None = None) -> Any:
        """Return value or default if missing (backward compatibility).

        Retrieves a value from the store, returning a specified default value
        if the key doesn't exist. This provides backward compatibility with
        older code that expects a get() method with default handling.

        Args:
            key: String identifier for the data item to retrieve.
            default: Value to return if the key doesn't exist. Defaults to None.

        Returns:
            The stored value if the key exists, otherwise the default value.

        Example:
            >>> store = DataStore()
            >>> value = store.get("missing_key", "default_value")
            >>> print(f"Retrieved: {value}")  # Prints: "default_value"
        """
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        """Check if a key exists in the store (backward compatibility).

        Provides a simple boolean check for key existence, useful for
        conditional logic without retrieving the actual value.

        Args:
            key: String identifier to check for existence.

        Returns:
            True if the key exists, False otherwise.

        Example:
            >>> store = DataStore()
            >>> store.put("coral_data", [1, 2, 3])
            >>> if store.has("coral_data"):
            ...     print("Coral data is available")
        """
        return key in self._data

    def keys(self, prefix: str | None = None) -> list[str]:
        """Get all keys or keys matching a prefix (backward compatibility).

        Retrieves a list of all keys in the store, optionally filtered by
        a prefix string. This is useful for discovering available data or
        finding related keys with common naming patterns.

        Args:
            prefix: Optional string prefix to filter keys. If None, returns all keys.

        Returns:
            List of string keys matching the criteria.

        Example:
            >>> store = DataStore()
            >>> store.put("coral_growth_2024", 0.15)
            >>> store.put("coral_growth_2025", 0.18)
            >>> store.put("water_temp", 22.5)
            >>> coral_keys = store.keys("coral_growth")
            >>> print(f"Coral growth keys: {coral_keys}")
        """
        if prefix is None:
            return list(self._data.keys())
        return [k for k in self._data.keys() if k.startswith(prefix)]
