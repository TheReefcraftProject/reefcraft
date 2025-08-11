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
from reefcraft.ui.label import Label, TextAlign
from reefcraft.ui.list import LayoutDirection, List

if TYPE_CHECKING:
    from reefcraft.sim.engine import Engine
    from reefcraft.ui.ui_context import UIContext


class PipelineSection(List):
    def __init__(self, context: UIContext, engine: Engine) -> None:
        super().__init__(context=context, background=True, direction=LayoutDirection.VERTICAL, margin=0)
        self.engine = engine

        # Header row to align with CORALS section (left padding + label)
        self.add_control(
            List(
                context,
                controls=[
                    Control(context, width=10),
                    Label(context, text="PIPELINE", width=250, align=TextAlign.LEFT, font_color="#F3F6FA"),
                ],
                direction=LayoutDirection.HORIZONTAL,
                margin=5,
            )
        )

        # Container for rows (icon + name) to match CoralSection spacing/margins
        # Match CoralSection inner list spacing/margins exactly
        self.rows = List(context=context, direction=LayoutDirection.VERTICAL, spacing=4, margin=4, background=False)
        self.add_control(self.rows)

        # Add rows lazily when models are added; avoids per-frame rebuild/copies
        self._row_items: list[tuple[Icon, Label]] = []

        def _ensure_rows(_event: object | None = None) -> None:
            models = self.engine.state.graph.models
            while len(self._row_items) < len(models):
                model = models[len(self._row_items)]
                # Match CoralItem row spacing (spacing=6, margin=4)
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

        self.context.renderer.add_event_handler(_ensure_rows, "before_render")


