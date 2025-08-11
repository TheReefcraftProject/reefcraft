# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Lightweight versioned key-value data store for model inputs/outputs."""

from __future__ import annotations

from typing import Any


class DataStore:
    """A simple versioned dictionary-like registry with string keys."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._versions: dict[str, int] = {}

    # Versioned API ---------------------------------------------------------
    def put(self, key: str, value: Any) -> int:
        """Store a value and bump its version, returning the new version."""
        self._data[key] = value
        self._versions[key] = self._versions.get(key, 0) + 1
        return self._versions[key]

    def try_get(self, key: str) -> Any | None:
        """Return value or None if missing."""
        return self._data.get(key)

    def version(self, key: str) -> int:
        """Return the current version for a key (0 if unseen)."""
        return self._versions.get(key, 0)

    # Back-compat thin wrappers --------------------------------------------
    def set(self, key: str, value: Any) -> None:
        self.put(key, value)

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._data

    def keys(self, prefix: str | None = None) -> list[str]:
        if prefix is None:
            return list(self._data.keys())
        return [k for k in self._data.keys() if k.startswith(prefix)]


