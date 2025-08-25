# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Main entry point for the Reefcraft coral reef simulation application.

This module serves as the primary entry point when the Reefcraft package
is run directly as a Python module (e.g., `python -m reefcraft`). It
provides the main function that initializes and launches the application.

The main entry point handles:
- Application root directory detection and setup
- ReefcraftApp initialization with proper configuration
- Application lifecycle management (startup, run, shutdown)
- Graceful error handling and exit codes

Usage:
    Direct execution:
        python -m reefcraft

    From command line:
        uv run python -m reefcraft

    From IDE:
        Run this file directly as the main module

Dependencies:
    - reefcraft.app.ReefcraftApp: Main application class
    - pathlib.Path: Path resolution and manipulation
    - sys: System-specific parameters and functions

The application will run until explicitly closed by the user or
an unrecoverable error occurs.
"""

import sys
from pathlib import Path
from typing import NoReturn

from .app import ReefcraftApp
from .utils.logger import logger


def main() -> None:
    """Launch the Reefcraft application and block until it closes.

    This function serves as the main entry point for the Reefcraft
    coral reef simulation application. It performs the following steps:

    1. **Path Resolution**: Determines the application root directory
       by resolving the path to this file and navigating to its parent
       directory. This ensures the application can locate resources
       regardless of the current working directory.

    2. **Application Initialization**: Creates a new ReefcraftApp
       instance with the resolved root directory, which initializes
       all necessary components including the simulation engine,
       rendering system, and user interface.

    3. **Application Execution**: Calls the app.run() method to
       start the main event loop, which handles user input, simulation
       updates, and rendering until the application is closed.

    4. **Blocking Behavior**: This function blocks until the
       application terminates, ensuring proper resource cleanup
       and preventing premature exit.

    The application will continue running until:
    - The user closes the main window
    - An unrecoverable error occurs
    - The application is terminated by the system

    Raises:
        RuntimeError: If the application fails to initialize
        SystemExit: If the application encounters a fatal error
        KeyboardInterrupt: If the user interrupts execution (Ctrl+C)

    Note:
        This function is designed to be called from the command line
        or as a module entry point. It should not be called from
        within other parts of the application.

    Example:
        >>> if __name__ == "__main__":
        ...     main()  # Launch the application
    """
    try:
        # Resolve the application root directory
        # This ensures resources can be found regardless of CWD
        app_root = Path(__file__).resolve().parent
        logger.info(f"Application root directory: {app_root}")

        # Initialize and launch the application
        logger.info("Initializing Reefcraft application...")
        app = ReefcraftApp(app_root=app_root)

        logger.info("Starting Reefcraft application...")
        app.run()

        logger.info("Reefcraft application closed successfully")

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in main application: {e}")
        sys.exit(1)


def _handle_early_exit() -> NoReturn:
    """Handle early exit scenarios with proper cleanup.

    This function is called when the application needs to exit
    before the main application loop can start. It ensures
    proper cleanup and provides informative error messages.

    This is typically used for:
    - Missing dependencies
    - Configuration errors
    - System compatibility issues
    - Early validation failures

    Raises:
        SystemExit: Always raises SystemExit with appropriate code
    """
    logger.error("Application cannot start due to configuration or dependency issues")
    logger.error("Please check the installation and try again")
    sys.exit(1)


if __name__ == "__main__":
    # Set up basic logging before main execution
    try:
        from .utils.logger import configure_logging

        configure_logging()
        logger.info("Starting Reefcraft from __main__")
        main()
    except ImportError as e:
        print(f"Failed to import required modules: {e}")
        print("Please ensure all dependencies are installed correctly")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during startup: {e}")
        sys.exit(1)
