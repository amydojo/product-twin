from __future__ import annotations

import math


def rotational_profile(spec: dict) -> list[tuple[float, float]]:
    dimensions = spec["dimensions"]
    body_height = dimensions["heightMm"] - dimensions["capHeightMm"]
    radius = dimensions["bodyDiameterMm"] / 2
    neck_radius = dimensions["neckDiameterMm"] / 2
    shoulder_z = body_height * spec["body"]["shoulderStartRatio"]
    curvature = spec["body"]["shoulderCurvature"]
    shoulder_height = body_height - shoulder_z
    return [
        (0.0, radius * 0.91),
        (1.0, radius * 0.98),
        (2.2, radius),
        (shoulder_z, radius),
        (shoulder_z + shoulder_height * (0.26 + 0.16 * curvature), radius - (radius - neck_radius) * 0.18),
        (shoulder_z + shoulder_height * (0.58 + 0.18 * curvature), radius - (radius - neck_radius) * 0.68),
        (body_height - 1.0, neck_radius),
        (body_height, neck_radius),
    ]


def _lathe_mesh(bpy, name: str, profile: list[tuple[float, float]], segments: int = 64):
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for z, radius in profile:
        for index in range(segments):
            angle = 2 * math.pi * index / segments
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), z))
    for row in range(len(profile) - 1):
        for index in range(segments):
            current = row * segments + index
            next_current = row * segments + (index + 1) % segments
            next_row = (row + 1) * segments + (index + 1) % segments
            current_row = (row + 1) * segments + index
            faces.append((current, next_current, next_row, current_row))
    bottom_center = len(vertices)
    vertices.append((0, 0, profile[0][0]))
    top_center = len(vertices)
    vertices.append((0, 0, profile[-1][0]))
    for index in range(segments):
        faces.append((bottom_center, (index + 1) % segments, index))
        top_start = (len(profile) - 1) * segments
        faces.append((top_center, top_start + index, top_start + (index + 1) % segments))
    mesh = bpy.data.meshes.new(f"{name}_MESH")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    mesh.validate(verbose=False)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def _shade_smooth(obj) -> None:
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def build(bpy, spec: dict, materials: dict):
    dimensions = spec["dimensions"]
    profile = rotational_profile(spec)
    body = _lathe_mesh(bpy, "BODY", profile)
    body.data.materials.append(materials["body"])
    _shade_smooth(body)
    bevel = body.modifiers.new("EDGE_BEVEL", "BEVEL")
    bevel.width = 0.55
    bevel.segments = 3
    solidify = body.modifiers.new("WALL_THICKNESS", "SOLIDIFY")
    solidify.thickness = -dimensions["wallThicknessMm"]
    solidify.use_even_offset = True

    inner = body.copy()
    inner.data = body.data.copy()
    inner.name = "BODY_INNER"
    inner.hide_render = True
    inner.hide_viewport = True
    bpy.context.collection.objects.link(inner)

    body_height = dimensions["heightMm"] - dimensions["capHeightMm"]
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=dimensions["neckDiameterMm"] / 2,
        depth=5,
        location=(0, 0, body_height - 2.5),
    )
    neck = bpy.context.object
    neck.name = "NECK"
    neck.data.materials.append(materials["body"])
    _shade_smooth(neck)

    cap_height = dimensions["capHeightMm"]
    cap_center = dimensions["heightMm"] - cap_height / 2
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=dimensions["neckDiameterMm"] * 0.72,
        depth=cap_height * 0.65,
        location=(0, 0, cap_center - cap_height * 0.12),
    )
    closure = bpy.context.object
    closure.name = "CLOSURE"
    closure.data.materials.append(materials["closure"])
    _shade_smooth(closure)
    closure_bevel = closure.modifiers.new("CLOSURE_BEVEL", "BEVEL")
    closure_bevel.width = 0.6
    closure_bevel.segments = 3

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=48,
        ring_count=24,
        location=(0, 0, cap_center + cap_height * 0.25),
    )
    bulb = bpy.context.object
    bulb.name = "DROPPER_BULB"
    bulb.scale = (
        dimensions["neckDiameterMm"] * 0.82,
        dimensions["neckDiameterMm"] * 0.82,
        cap_height * 0.42,
    )
    bulb.data.materials.append(materials["closure"])
    _shade_smooth(bulb)

    pipette_depth = dimensions["heightMm"] * 0.48
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=max(0.9, dimensions["neckDiameterMm"] * 0.075),
        depth=pipette_depth,
        location=(0, 0, dimensions["heightMm"] * 0.52),
    )
    pipette = bpy.context.object
    pipette.name = "PIPETTE"
    pipette.data.materials.append(materials["glass"])
    _shade_smooth(pipette)

    if spec["liquid"]["enabled"]:
        liquid_height = body_height * spec["liquid"]["fillPercent"] / 100 * 0.72
        liquid_radius = dimensions["bodyDiameterMm"] / 2 - dimensions["wallThicknessMm"] - 0.8
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=64,
            radius=max(0.5, liquid_radius),
            depth=max(0.5, liquid_height),
            location=(0, 0, 1.2 + liquid_height / 2),
        )
        liquid = bpy.context.object
        liquid.name = "LIQUID"
        liquid.data.materials.append(materials["liquid"])
        _shade_smooth(liquid)
    return body
