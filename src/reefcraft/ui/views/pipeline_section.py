# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""UI section to list models/operators currently in the pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from reefcraft.ui.control import Control
from reefcraft.ui.icon import Icon
from reefcraft.ui.popup_menu import PopupMenuControl
from reefcraft.ui.label import Label, TextAlign
from reefcraft.ui.list import LayoutDirection, List

if TYPE_CHECKING:
    from reefcraft.sim.engine import Engine
    from reefcraft.ui.ui_context import UIContext


class PipelineSection(List):
    """Pipeline palette section with add-model popup and model list."""

    def __init__(self, context: UIContext, engine: Engine) -> None:
        """Build header with popup and a lazy-updating list of models."""
        super().__init__(context=context, background=True, direction=LayoutDirection.VERTICAL, margin=0)
        self.engine = engine

        # Header row to align with CORALS section (left padding + label)
        header = List(
            context,
            controls=[
                Control(context, width=10),
                Label(context, text="PIPELINE", width=224, align=TextAlign.LEFT, font_color="#F3F6FA"),
            ],
            direction=LayoutDirection.HORIZONTAL,
            margin=5,
        )
        # Add a plus icon button aligned to the right, similar to CORALS
        self._popup = PopupMenuControl(
            context,
            icon="add.png",
            width=24,
            height=24,
            items=["LLABRES", "PORAG"],
            on_select=self._on_add_model_selected,
        )
        header.add_control(self._popup)
        self.add_control(header)

        # Container for rows (icon + name)
        self.rows = List(context=context, direction=LayoutDirection.VERTICAL, spacing=4, margin=4, background=False)
        self.add_control(self.rows)

        # Add rows lazily when models are added; avoids per-frame rebuild/copies
        self._row_items: list[tuple[Icon, Label]] = []
        self._last_model_count: int = 0  # Track when models change

        def _ensure_rows(_event: object | None = None) -> None:
            models = self.engine.state.graph.models
            current_count = len(models)
            
            # Only update if the number of models has changed
            if current_count == self._last_model_count:
                return
                
            self._last_model_count = current_count
            
            # Clear existing rows and rebuild
            self.rows.controls.clear()
            self._row_items.clear()
            
            # Add new rows
            for model in models:
                row = List(context=context, direction=LayoutDirection.HORIZONTAL, spacing=6, margin=4, background=False)
                name = getattr(model, "name", model.__class__.__name__)
                lname = name.lower()
                icon_name = "plus.png"
                if lname.startswith("water"):
                    icon_name = "water.png"
                elif lname.startswith("llabres") or lname.startswith("porag"):
                    icon_name = "coral.png"
                space = Control(context, width=16, height=24)
                icon = Icon(context, icon=icon_name, width=24, height=24, icon_width=24, icon_height=24)
                label = Label(context, text=name, width=194, align=TextAlign.LEFT)
                row.add_control(space)
                row.add_control(icon)
                row.add_control(label)
                self.rows.add_control(row)
                self._row_items.append((icon, label))

        # Guard renderer access during headless tests
        renderer = getattr(self.context, "renderer", None)
        if renderer is not None and hasattr(renderer, "add_event_handler"):
            renderer.add_event_handler(_ensure_rows, "before_render")

    # ------------------------------------------------------------------
    # Add-model dropdown + actions
    # ------------------------------------------------------------------
    def _on_add_model_selected(self, opt: str) -> None:
        # Add the requested model
        from reefcraft.sim.growth_model_factory import CoralModel

        if opt.upper() == "LLABRES":
            self.engine.state.add_coral_with_model(CoralModel.LLABRES)
        elif opt.upper() == "PORAG":
            self.engine.state.add_coral_with_model(CoralModel.PORAG)


