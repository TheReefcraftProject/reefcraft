"""Application management for Reefcraft."""

from __future__ import annotations

from pathlib import Path

from rendercanvas.auto import loop

from reefcraft.gui.window import Window
from reefcraft.render.renderer import Renderer
from reefcraft.sim.engine import Engine


class ReefcraftApp:
    """Main application framework for Reefcraft."""

    def __init__(self, app_root: Path | None = None) -> None:
        """Initialize the application state."""
        self.app_root = Path(app_root) if app_root else Path(__file__).resolve().parents[1]
        self.engine = Engine()
        self.window = Window(self.engine, self.app_root)
        self.renderer = Renderer(self.window.canvas)

    def run(self) -> None:
        """Start the application."""
        loop.run()
        # while not self.window.is_closed:
        # self.renderer.update()
        # self.window.update()
        # Process events (important for window management and responsiveness)
        # wgpu.gui.handle_events()

        # Render your scene (optional, if you're not continuously rendering)
        # renderer.render(scene, window.camera)

        # Request a draw and present the frame
        # window.request_draw()
        # window.present()

        # Add a small delay to prevent busy-waiting and reduce CPU usage
        # sleep(0.01)
