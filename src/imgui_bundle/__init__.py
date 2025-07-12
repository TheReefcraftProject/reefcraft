"""Compatibility shim for :mod:`wgpu.utils.imgui` to use :mod:`pyimgui`."""

from importlib import import_module

# Re-export pyimgui as ``imgui`` so packages expecting ``imgui_bundle.imgui``
# can import it transparently.
imgui = import_module("imgui")

__all__ = ["imgui"]
