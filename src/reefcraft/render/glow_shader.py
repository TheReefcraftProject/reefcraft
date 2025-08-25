# -----------------------------------------------------------------------------
# Copyright (c) 2025 The Reefcraft Project.
#
# Licensed under the MIT License. See the LICENSE file for details.
# -----------------------------------------------------------------------------

"""Glowing shader/material for water particles."""
import pathlib
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pygfx as gfx
import wgpu
from pygfx.materials import (
    PointsGaussianBlobMaterial,
    PointsMarkerMaterial,
    PointsMaterial,
    PointsSpriteMaterial,
)
from pygfx.objects import Points
from pygfx.renderers.wgpu import (
    BaseShader,
    Binding,
    GfxSampler,
    GfxTextureView,
    RenderMask,
    nchannels_from_format,
    register_wgpu_render_function,
    to_texture_format,
)
from pygfx.resources import Texture


class GlowPointsMaterial(PointsMaterial):
    """Custom material so we don't override normal PointsMaterial."""
    uniform_type = dict(
        gfx.PointsMaterial.uniform_type,
    )

    def __init__(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize glow mat with glow intensity."""
        super().__init__(**kwargs)

@register_wgpu_render_function(Points, GlowPointsMaterial)
class GlowPointsShader(BaseShader):
    """Glowing shader for water particles."""
    type = "render" #render pass shader, not compute

    def __init__(self, wobject: gfx.WorldObject) -> None:
        """Initialize glow shader."""
        super().__init__(wobject)

        material = cast("GlowPointsMaterial", wobject.material)
        geometry = wobject.geometry
        assert geometry is not None, "WaterParticles has no geometry!"

        color_mode = str(material.color_mode).split(".")[-1]
        if color_mode == "auto":
            if material.map is not None:
                self["color_mode"] = "vertex_map"
                self["color_buffer_channels"] = 0
            else:
                self["color_mode"] = "uniform"
                self["color_buffer_channels"] = 0
        elif color_mode == "uniform":
            self["color_mode"] = "uniform"
            self["color_buffer_channels"] = 0
        elif color_mode == "vertex":
            nchannels = nchannels_from_format(geometry.colors.format)
            self["color_mode"] = "vertex"
            self["color_buffer_channels"] = nchannels
            if nchannels not in (1, 2, 3, 4):
                raise ValueError(f"Geometry.colors needs 1-4 columns, not {nchannels}")
        elif color_mode == "vertex_map":
            self["color_mode"] = "vertex_map"
            self["color_buffer_channels"] = 0
            if material.map is None:
                raise ValueError("Cannot apply colormap is no material.map is set.")
        elif color_mode == "debug":
            self["color_mode"] = "debug"
            self["color_buffer_channels"] = 0
        else:
            raise RuntimeError(f"Unknown color_mode: '{color_mode}'")

        edge_color_mode = str(material.edge_color_mode).split(".")[-1] if isinstance(material, PointsMarkerMaterial) else "uniform"

        if edge_color_mode == "vertex":
            nchannels = nchannels_from_format(geometry.edge_colors.format)
            self["edge_color_mode"] = "vertex"
            self["edge_color_buffer_channels"] = nchannels
            if nchannels not in (1, 2, 3, 4):
                raise ValueError(
                    f"Geometry.edge_colors needs 1-4 columns, not {self['edge_color_buffer_channels']}"
                )
        else:  # auto or uniform
            self["edge_color_mode"] = "uniform"
            self["edge_color_buffer_channels"] = 0

        self["edge_mode"] = material.edge_mode

        self["rotation_mode"] = material.rotation_mode

        self["is_sprite"] = 0  # 0, 1, 2
        if isinstance(material, PointsSpriteMaterial):
            self["is_sprite"] = 1
            if material.sprite is not None:
                self["is_sprite"] = 2  # i.e. is sprite and has a texture

        self["size_mode"] = str(material.size_mode).split(".")[-1]
        self["size_space"] = material.size_space
        self["aa"] = material.aa

        self["draw_line_on_edge"] = False
        if isinstance(material, PointsMarkerMaterial):
            self["draw_line_on_edge"] = True

    def get_bindings(self, wobject: gfx.WorldObject, shared: SimpleNamespace) -> dict[Any, Any]:
        """Define shader bindings."""
        geometry = wobject.geometry
        material = wobject.material
        assert geometry is not None, "WaterParticles has no geometry!"
        assert material is not None, "WaterParticles has no material!"

        rbuffer = "buffer/read_only_storage"
        bindings = [
            Binding("u_stdinfo", "buffer/uniform", shared.uniform_buffer),
            Binding("u_wobject", "buffer/uniform", wobject.uniform_buffer),
            Binding("u_material", "buffer/uniform", material.uniform_buffer),
            Binding("s_positions", rbuffer, geometry.positions, "VERTEX"), #type: ignore
        ]

        if self["size_mode"] == "vertex":
            bindings.append(Binding("s_sizes", rbuffer, geometry.sizes, "VERTEX")) #type: ignore

        # Per-vertex color, colormap, or a uniform color?
        if self["color_mode"] == "vertex":
            bindings.append(Binding("s_colors", rbuffer, geometry.colors, "VERTEX")) #type: ignore
        elif self["color_mode"] == "vertex_map":
            bindings.append(
                Binding("s_texcoords", rbuffer, geometry.texcoords, "VERTEX") #type: ignore
            )
            bindings.extend(
                self.define_generic_colormap(material.map, geometry.texcoords) # pyright: ignore[reportAttributeAccessIssue]
            )

        if self["edge_color_mode"] == "vertex":
            bindings.append(
                Binding("s_edge_colors", rbuffer, geometry.edge_colors, "VERTEX") #type: ignore
            )

        if self["rotation_mode"] == "vertex":
            bindings.append(
                Binding("s_rotations", rbuffer, geometry.rotations, "VERTEX") #type: ignore
            )

        # Process sprite texture. Note that we can *also* have a colormap for the base color.
        if self["is_sprite"] == 2:
            sprite_sampler = GfxSampler("linear", "clamp")
            if not isinstance(material.sprite, Texture): # pyright: ignore[reportAttributeAccessIssue]
                raise TypeError("material sprite must be a Texture")
            sprite_view = GfxTextureView(material.sprite) # pyright: ignore[reportAttributeAccessIssue]
            if sprite_view.view_dim != "2d":
                raise ValueError("Sprite textures must be 2D")
            fmt = to_texture_format(sprite_view.format)
            if not ("norm" in fmt or "float" in fmt):
                raise ValueError("Sprite textures must be u8norm or float")
            self["sprite_nchannels"] = len(fmt) - len(fmt.lstrip("rgba"))
            bindings += [
                Binding("s_sprite", "sampler/filtering", sprite_sampler, "FRAGMENT"), #type: ignore
                Binding("t_sprite", "texture/auto", sprite_view, "FRAGMENT"), #type:ignore
            ]

        self["shape"] = "circle"
        if isinstance(material, PointsGaussianBlobMaterial):
            self["shape"] = "gaussian"
        elif isinstance(material, PointsMarkerMaterial):
            self["shape"] = material.marker
            custom_sdf = material.custom_sdf
            if custom_sdf is None:
                # Make a nice full square to help the user better design their
                # custom SDF
                custom_sdf = "return max(abs(coord.x), abs(coord.y)) - size * 0.5;"
            self["custom_sdf"] = custom_sdf

        bindings = dict(enumerate(bindings))
        self.define_bindings(0, bindings)

        return {
            0: bindings,
        }
    
    def get_pipeline_info(self, wobject: gfx.WorldObject, shared: SimpleNamespace) -> dict[Any, Any]:
        """Define GPU pipeline config."""
        return {
            "primitive_topology": wgpu.PrimitiveTopology.triangle_list,
            "cull_mode": wgpu.CullMode.none,
        }
    
    def get_render_info(self, wobject: gfx.WorldObject, shared: SimpleNamespace) -> dict[Any, Any]:
        """Describe how to draw the object each frame."""
        material = cast("GlowPointsMaterial", wobject.material)
        assert wobject.geometry is not None

        offset, size = wobject.geometry.positions.draw_range
        offset, size = offset * 6, size * 6

        render_mask = 0
        if wobject.render_mask:
            render_mask = wobject.render_mask
        elif material.is_transparent:
            render_mask = RenderMask.transparent
        else:
            # Get what passes are needed for the color
            if self["color_mode"] == "uniform":
                if material.color_is_transparent:
                    render_mask |= RenderMask.transparent
                else:
                    render_mask |= RenderMask.opaque
            elif self["color_mode"] == "vertex":
                if self["color_buffer_channels"] in (2, 4):
                    render_mask |= RenderMask.all
                else:
                    render_mask |= RenderMask.opaque
            elif self["color_mode"] == "vertex_map":
                if self["colormap_nchannels"] in (2, 4):
                    render_mask |= RenderMask.all
                else:
                    render_mask |= RenderMask.opaque
            elif self["color_mode"] == "debug":
                render_mask |= RenderMask.all
            else:
                raise RuntimeError(f"Unexpected color mode {self['color_mode']}")
            # Need transparency for aa
            if material.aa:
                render_mask |= RenderMask.transparent
            # More cases
            elif isinstance(material, PointsSpriteMaterial):
                if self["sprite_nchannels"] in [2, 4]:
                    render_mask |= RenderMask.transparent
                else:
                    pass  # mixed with color, so no need to OR with opaque
            elif isinstance(material, PointsMarkerMaterial):
                if self["edge_color_mode"] == "vertex":
                    if self["edge_color_buffer_channels"] in (2, 4):
                        render_mask |= RenderMask.all
                    else:
                        render_mask |= RenderMask.opaque
                elif self["edge_color_mode"] == "uniform":
                    if material.edge_color_is_transparent:
                        render_mask |= RenderMask.transparent
                    else:
                        render_mask |= RenderMask.opaque

        return {
            "indices": (size, 1, offset, 0),
            "render_mask": render_mask,
        }
    
    def get_code(self) -> str:
        """Define WGSL shader code for glowing particles."""
        shader_path = pathlib.Path(__file__).parent/"glow.wgsl"
        return shader_path.read_text()
    
def make_test_point() -> gfx.Points:
    """Test point."""
    pos = np.array([[0, 0, -5]], dtype = np.float32)
    geometry = gfx.Geometry(positions = gfx.Buffer(pos))
    material = GlowPointsMaterial(color = (1.0, 0.2, 0.8, 1.0), size = 1000)
    return gfx.Points(geometry, material)
