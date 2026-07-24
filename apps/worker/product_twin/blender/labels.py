from __future__ import annotations

from pathlib import Path


def _artwork_material(bpy, artwork_path: str, fallback_material):
    path = Path(artwork_path)
    if not path.is_file():
        raise ValueError("label artwork path does not exist")
    material = bpy.data.materials.new("LABEL_ARTWORK_MATERIAL")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    image_node = nodes.new("ShaderNodeTexImage")
    image_node.image = bpy.data.images.load(str(path), check_existing=True)
    image_node.interpolation = "Linear"
    links.new(image_node.outputs["Color"], bsdf.inputs["Base Color"])
    if "Alpha" in image_node.outputs and "Alpha" in bsdf.inputs:
        links.new(image_node.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.46
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    elif hasattr(material, "blend_method"):
        material.blend_method = "BLEND"
    return material


def add_front_label(bpy, spec: dict, artwork_path: str | None, fallback_material):
    dimensions = spec["dimensions"]
    label = spec["label"]
    body_height = dimensions["heightMm"] - dimensions["capHeightMm"]
    width = dimensions["bodyDiameterMm"] * label["widthRatio"]
    height = body_height * label["heightRatio"]
    z = body_height * label["verticalCenterRatio"]
    radius = dimensions["bodyDiameterMm"] / 2

    bpy.ops.mesh.primitive_plane_add(
        size=1,
        location=(0, -radius - 0.22, z),
        rotation=(1.57079632679, 0, 0),
    )
    obj = bpy.context.object
    obj.name = "LABEL"
    obj.scale = (width, height, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    material = _artwork_material(bpy, artwork_path, fallback_material) if artwork_path else fallback_material
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("LABEL_EDGE_BEVEL", "BEVEL")
    bevel.width = 0.08
    bevel.segments = 2
    return obj
