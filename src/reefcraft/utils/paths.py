# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Centralized path management for Reefcraft application resources and directories.

This module provides a unified system for managing file paths throughout
the Reefcraft application. It maintains a centralized application root
directory and provides convenient accessor functions for common resource
directories like icons, fonts, and other assets.

The path management system provides:
- Centralized application root directory management
- Safe path resolution and validation
- Convenient accessor functions for resource directories
- Cross-platform path handling using pathlib
- Runtime validation to ensure paths are properly initialized

All paths are resolved to absolute paths to ensure consistent behavior
regardless of the current working directory when the application is run.
"""

from pathlib import Path

# Global application root directory (set once at startup)
_APP_ROOT: Path | None = None


def set_app_root(path: Path) -> None:
    """Set the root directory of the application.

    This function should be called once at application startup to establish
    the base directory for all resource path resolution. The path is resolved
    to an absolute path to ensure consistent behavior.

    Args:
        path: Path to the application root directory

    Note:
        This function should only be called once during application
        initialization. Subsequent calls will overwrite the previous
        root directory setting.

    Example:
        >>> from pathlib import Path
        >>> set_app_root(Path(__file__).parent.parent)
        >>> root = get_app_root()
        >>> print(f"App root: {root}")
    """
    global _APP_ROOT
    _APP_ROOT = path.resolve()


def get_app_root() -> Path:
    """Get the application root directory.

    Returns the absolute path to the application root directory that
    was previously set using set_app_root(). This is the base directory
    from which all other resource paths are calculated.

    Returns:
        Absolute path to the application root directory

    Raises:
        RuntimeError: If set_app_root() has not been called to initialize
                     the application root directory

    Example:
        >>> root = get_app_root()
        >>> config_file = root / "config" / "settings.json"
        >>> print(f"Config file: {config_file}")
    """
    if _APP_ROOT is None:
        raise RuntimeError("Application root directory not set. Call set_app_root() during application startup.")
    return _APP_ROOT


def icons_dir() -> Path:
    """Get the path to the application's icons directory.

    Returns the absolute path to the directory containing icon resources
    used throughout the application's user interface.

    Returns:
        Absolute path to the icons directory (resources/icons)

    Raises:
        RuntimeError: If the application root has not been set

    Example:
        >>> icons_path = icons_dir()
        >>> logo_icon = icons_path / "logo.png"
        >>> add_icon = icons_path / "add.png"
    """
    return get_app_root() / "resources" / "icons"


def fonts_dir() -> Path:
    """Get the path to the application's fonts directory.

    Returns the absolute path to the directory containing font resources
    used for text rendering in the application's user interface.

    Returns:
        Absolute path to the fonts directory (resources/fonts)

    Raises:
        RuntimeError: If the application root has not been set

    Example:
        >>> fonts_path = fonts_dir()
        >>> main_font = fonts_path / "Archivo-Regular.ttf"
        >>> if main_font.exists():
        ...     print("Main font available")
    """
    return get_app_root() / "resources" / "fonts"


def resources_dir() -> Path:
    """Get the path to the application's root resources directory.

    Returns the absolute path to the main resources directory that
    contains all application assets including icons, fonts, models,
    and other resource files.

    Returns:
        Absolute path to the resources directory (resources/)

    Raises:
        RuntimeError: If the application root has not been set

    Example:
        >>> resources_path = resources_dir()
        >>> models_path = resources_path / "models"
        >>> coral_model = models_path / "coral.stl"
    """
    return get_app_root() / "resources"


def models_dir() -> Path:
    """Get the path to the application's 3D models directory.

    Returns the absolute path to the directory containing 3D model
    files used for coral visualization and simulation.

    Returns:
        Absolute path to the models directory (resources/models)

    Raises:
        RuntimeError: If the application root has not been set

    Example:
        >>> models_path = models_dir()
        >>> coral_stl = models_path / "coral.stl"
        >>> if coral_stl.exists():
        ...     print("Coral model found")
    """
    return get_app_root() / "resources" / "models"
