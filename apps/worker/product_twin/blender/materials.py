from __future__ import annotations

from typing import Any


def principled_values(
    material: str,
    roughness: float | None,
    transmission: float | None,
    ior: float | None,
) -> dict[str, float]:
    presets = {
        "clear-glass": (0.08, 1.0, 1.50),
        "frosted-glass": (0.32, 0.90, 1.50),
        "glossy-plastic": (0.16, 0.0, 1.46),
        "matte-plastic": (0.50, 0.0, 1.46),
        "metal": (0.24, 0.0, 1.46),
    }
    if material not in presets:
        raise ValueError(f"unsupported material preset: {material}")
    base_roughness, base_transmission, base_ior = presets[material]
    return {
        "roughness": max(0.0, min(1.0, base_roughness if roughness is None else roughness)),
        "transmission": max(0.0, min(1.0, base_transmission if transmission is None else transmission)),
        "ior": max(1.0, min(2.5, base_ior if ior is None else ior)),
        "metallic": 1.0 if material == "metal" else 0.0,
    }


def _input(bsdf: Any, *names: str):
    for name in names:
        if name in bsdf.inputs:
            return bsdf.inputs[name]
    return None


def create_material(bpy, name: str, color: str, values: dict[str, float], alpha: float = 1.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    is_transmissive = values["transmission"] > 0
    render_alpha = min(alpha, 0.82) if is_transmissive else alpha
    rgba = tuple(int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)) + (render_alpha,)
    _input(bsdf, "Base Color").default_value = rgba
    _input(bsdf, "Roughness").default_value = values["roughness"]
    transmission = _input(bsdf, "Transmission Weight", "Transmission")
    if transmission is not None:
        # Eevee's headless CPU path turns high transmission nearly black without an HDRI.
        # Bound the viewport approximation while preserving the requested value in the spec/manifest.
        transmission.default_value = min(values["transmission"], 0.38)
    ior = _input(bsdf, "IOR")
    if ior is not None:
        ior.default_value = values["ior"]
    metallic = _input(bsdf, "Metallic")
    if metallic is not None:
        metallic.default_value = values.get("metallic", 0.0)
    coat = _input(bsdf, "Coat Weight", "Clearcoat")
    if coat is not None:
        coat.default_value = 0.22 if is_transmissive else 0.12
    alpha_input = _input(bsdf, "Alpha")
    if alpha_input is not None:
        alpha_input.default_value = render_alpha
    if render_alpha < 1:
        if hasattr(material, "surface_render_method"):
            material.surface_render_method = "DITHERED"
        elif hasattr(material, "blend_method"):
            material.blend_method = "BLEND"
        if hasattr(material, "use_screen_refraction"):
            material.use_screen_refraction = True
    return material


def create_ground_material(bpy):
    """Create an unlit white ecommerce backdrop.

    A lit white Principled surface can render below RGB 245 after Blender color
    management, even at the image corners. An emission surface preserves a
    deterministic pure-white background while product lighting remains unchanged.
    """
    material = bpy.data.materials.new("GROUND_MATERIAL")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    emission.inputs["Strength"].default_value = 1.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material
