"""ImGui renderer for pygfx using pyimgui."""

import imgui
import wgpu

from .imgui_backend import ImguiWgpuBackend


class ImguiRenderer:
    """Render a pyimgui UI on top of a pygfx canvas."""
    KEY_MAP = {
        "ArrowDown": imgui.KEY_DOWN_ARROW,
        "ArrowUp": imgui.KEY_UP_ARROW,
        "ArrowLeft": imgui.KEY_LEFT_ARROW,
        "ArrowRight": imgui.KEY_RIGHT_ARROW,
        "Backspace": imgui.KEY_BACKSPACE,
        "Delete": imgui.KEY_DELETE,
        "End": imgui.KEY_END,
        "Enter": imgui.KEY_ENTER,
        "Escape": imgui.KEY_ESCAPE,
        "Home": imgui.KEY_HOME,
        "Insert": imgui.KEY_INSERT,
        "PageDown": imgui.KEY_PAGE_DOWN,
        "PageUp": imgui.KEY_PAGE_UP,
        "Tab": imgui.KEY_TAB,
        "A": imgui.KEY_A,
        "C": imgui.KEY_C,
        "V": imgui.KEY_V,
        "X": imgui.KEY_X,
        "Y": imgui.KEY_Y,
        "Z": imgui.KEY_Z,
    }

    KEY_MAP_MOD = {
        "Shift": imgui.KEY_MOD_SHIFT,
        "Control": imgui.KEY_MOD_CTRL,
        "Alt": imgui.KEY_MOD_ALT,
        "Meta": imgui.KEY_MOD_SUPER,
    }

    def __init__(
        self,
        device: wgpu.GPUDevice,
        canvas: wgpu.gui.WgpuCanvasBase,
        render_target_format: str | None = None,
    ) -> None:
        """Create the renderer and bind event handlers."""
        # Prepare present context
        self._canvas_context = canvas.get_context("wgpu")

        # if the canvas is not configured, we configure it self.
        if self._canvas_context._config is None:
            if render_target_format is None:
                render_target_format = self._canvas_context.get_preferred_format(
                    device.adapter
                )
            self._canvas_context.configure(device=device, format=render_target_format)
        else:
            config_format = self._canvas_context._config.get("format")
            if (
                render_target_format is not None
                and config_format != render_target_format
            ):
                raise ValueError(
                    "The canvas is already configured with a different format."
                )
            render_target_format = config_format

        self._imgui_context = imgui.create_context()
        imgui.set_current_context(self._imgui_context)

        self._backend = ImguiWgpuBackend(device, render_target_format)

        self._backend.io.display_size = canvas.get_logical_size()
        scale = canvas.get_pixel_ratio()
        self._backend.io.display_framebuffer_scale = (scale, scale)

        canvas.add_event_handler(self._on_resize, "resize")
        canvas.add_event_handler(self._on_mouse_move, "pointer_move", order=-99)
        canvas.add_event_handler(
            self._on_mouse, "pointer_up", "pointer_down", order=-99
        )
        canvas.add_event_handler(self._on_key, "key_up", "key_down", order=-99)
        canvas.add_event_handler(self._on_wheel, "wheel", order=-99)
        canvas.add_event_handler(self._on_char_input, "char", order=-99)

        self._update_gui_function = None

    def set_gui(self, gui_updater: callable) -> None:
        """Set the function used to update the ImGui interface each frame.

        Arguments
        ---------
        gui_updater: callable
            Function that returns ``imgui.core._DrawData`` from
            ``imgui.get_draw_data()``.

        Returns
        -------
        None
        """
        self._update_gui_function = gui_updater

    @property
    def imgui_context(self) -> "imgui.core._ImGuiContext":
        """imgui context for this renderer."""
        return self._imgui_context

    @property
    def backend(self):
        """The backend instance used by this renderer."""
        return self._backend

    def render(self):
        """
        render the imgui draw data to the canvas
        """

        if self._update_gui_function is None:
            raise AttributeError(
                "Must set the GUI update function using set_gui() before calling render()"
            )

        imgui.set_current_context(self.imgui_context)
        draw_data = self._update_gui_function()

        pixel_ratio = self._canvas_context.canvas.get_pixel_ratio()
        lsize = self._canvas_context.canvas.get_logical_size()
        self._backend.io.display_framebuffer_scale = (pixel_ratio, pixel_ratio)
        self._backend.io.display_size = lsize

        command_encoder = self._backend._device.create_command_encoder()
        current_texture_view = self._canvas_context.get_current_texture().create_view()
        render_pass = command_encoder.begin_render_pass(
            color_attachments=[
                {
                    "view": current_texture_view,
                    "resolve_target": None,
                    "clear_value": (0, 0, 0, 1),
                    "load_op": wgpu.LoadOp.load,
                    "store_op": wgpu.StoreOp.store,
                }
            ],
        )
        self._backend.render(draw_data, render_pass)
        render_pass.end()
        self._backend._device.queue.submit([command_encoder.finish()])

    def _on_resize(self, event):
        self._backend.io.display_size = (event["width"], event["height"])

    def _on_mouse_move(self, event):
        self._backend.io.add_mouse_pos_event(event["x"], event["y"])

        if self._backend.io.want_capture_mouse:
            event["stop_propagation"] = True

    def _on_mouse(self, event):
        event_type = event["event_type"]
        down = event_type == "pointer_down"
        self._backend.io.add_mouse_button_event(event["button"] - 1, down)

        if self._backend.io.want_capture_mouse:
            event["stop_propagation"] = True

    def _on_key(self, event):
        event_type = event["event_type"]
        down = event_type == "key_down"

        key_name = event["key"]
        if key_name in self.KEY_MAP:
            key = self.KEY_MAP[key_name]
        else:
            try:
                code = ord(key_name.lower())
                if 97 <= code <= 122:  # letters a-z
                    key_const = f"KEY_{key_name.upper()}"
                    key = getattr(imgui, key_const)
                else:
                    return
            except (ValueError, AttributeError):
                return  # Unknown key

        self._backend.io.add_key_event(key, down)

        if key_name in self.KEY_MAP_MOD:
            key = self.KEY_MAP_MOD[key_name]
            self._backend.io.add_key_event(key, down)

        if self._backend.io.want_capture_keyboard:
            event["stop_propagation"] = True

    def _on_wheel(self, event):
        self._backend.io.add_mouse_wheel_event(event["dx"] / 100, -event["dy"] / 100)

        if self._backend.io.want_capture_mouse:
            event["stop_propagation"] = True

    def _on_char_input(self, event):
        self._backend.io.add_input_characters_utf8(event["char_str"])

        if self._backend.io.want_text_input:
            event["stop_propagation"] = True
