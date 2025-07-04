"""Application management for Reefcraft."""

from __future__ import annotations

from pathlib import Path

from ..sim.engine import Engine
from ..utils.settings import load_settings


class ReefcraftApp:
    """Main application framework for Reefcraft."""

    def __init__(self, app_root: Path | None = None) -> None:
        """Initialize the application state."""
        self.app_root = Path(app_root) if app_root else Path(__file__).resolve().parents[1]
        self.settings = load_settings()
        self.engine = Engine()

    def run(self) -> None:
        """Start the application."""
        from ..gui.window import Window

        window = Window(self.engine, self.app_root)

        while window.running:
            self.engine.update()
            window.update()
