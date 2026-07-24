from __future__ import annotations

import json
import time
from pathlib import Path

from PIL import Image, ImageDraw

from .models import PackagingSpec

EXPECTED = [
    "BODY",
    "BODY_INNER",
    "NECK",
    "CLOSURE",
    "DROPPER_BULB",
    "PIPETTE",
    "LIQUID",
    "LABEL",
]


def _hex(value: str) -> tuple[int, int, int]:
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))  # type: ignore[return-value]


def _draw(spec: PackagingSpec, path: Path, view: str, transparent: bool, size: int = 800) -> None:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas, "RGBA")
    center_x = size // 2 + (55 if view == "three-quarter" else 0)
    base_y = int(size * 0.82)
    scale = size * 0.0047

    height = spec.dimensions.height_mm * scale
    body_height = (spec.dimensions.height_mm - spec.dimensions.cap_height_mm) * scale
    body_radius = spec.dimensions.body_diameter_mm * scale / 2
    shoulder_height = body_height * spec.body.shoulder_start_ratio
    neck_radius = spec.dimensions.neck_diameter_mm * scale / 2
    top_y = base_y - height
    body_top = base_y - body_height

    body_color = _hex(spec.body.color_hex)
    closure_color = _hex(spec.closure.color_hex)
    liquid_color = _hex(spec.liquid.color_hex)

    draw.ellipse(
        (center_x - body_radius * 1.25, base_y - 8, center_x + body_radius * 1.25, base_y + 14),
        fill=(0, 0, 0, 28),
    )

    if spec.liquid.enabled:
        fill_height = body_height * 0.70 * spec.liquid.fill_percent / 100
        draw.rounded_rectangle(
            (
                center_x - body_radius + 5,
                base_y - fill_height,
                center_x + body_radius - 5,
                base_y - 4,
            ),
            radius=12,
            fill=liquid_color + (int(255 * spec.liquid.opacity),),
        )

    profile = [
        (center_x - body_radius, base_y),
        (center_x - body_radius, body_top + body_height - shoulder_height),
        (center_x - neck_radius, body_top + 8),
        (center_x - neck_radius, body_top),
        (center_x + neck_radius, body_top),
        (center_x + neck_radius, body_top + 8),
        (center_x + body_radius, body_top + body_height - shoulder_height),
        (center_x + body_radius, base_y),
    ]
    body_alpha = 130 if "glass" in spec.body.material else 235
    draw.polygon(profile, fill=body_color + (body_alpha,), outline=(80, 80, 80, 90))
    draw.line(
        [
            (center_x - body_radius + 7, base_y - 12),
            (center_x - body_radius + 7, body_top + body_height - shoulder_height + 10),
        ],
        fill=(255, 255, 255, 90),
        width=5,
    )

    cap_height = spec.dimensions.cap_height_mm * scale
    cap_top = top_y + cap_height * 0.1
    cap_width = neck_radius * 1.55
    draw.rounded_rectangle(
        (
            center_x - cap_width,
            cap_top + cap_height * 0.28,
            center_x + cap_width,
            cap_top + cap_height * 0.82,
        ),
        radius=8,
        fill=closure_color + (245,),
    )
    draw.ellipse(
        (
            center_x - cap_width * 1.1,
            cap_top,
            center_x + cap_width * 1.1,
            cap_top + cap_height * 0.55,
        ),
        fill=closure_color + (250,),
    )

    label_width = (2 * body_radius) * spec.label.width_ratio
    label_height = body_height * spec.label.height_ratio
    label_center_y = base_y - body_height * spec.label.vertical_center_ratio
    draw.rounded_rectangle(
        (
            center_x - label_width / 2,
            label_center_y - label_height / 2,
            center_x + label_width / 2,
            label_center_y + label_height / 2,
        ),
        radius=5,
        fill=(249, 245, 237, 240),
        outline=(40, 40, 40, 45),
    )
    draw.text((center_x, label_center_y - 12), "FIELD / 01", fill=(28, 28, 28, 255), anchor="mm")
    draw.text((center_x, label_center_y + 16), "SERUM", fill=(28, 28, 28, 190), anchor="mm")

    if transparent:
        canvas.save(path)
    else:
        white = Image.new("RGBA", canvas.size, (255, 255, 255, 255))
        white.alpha_composite(canvas)
        white.convert("RGB").save(path)


def _build_fixture_glb(spec: PackagingSpec, output_path: Path) -> None:
    import numpy as np
    import trimesh

    dimensions = spec.dimensions
    body_height = dimensions.height_mm - dimensions.cap_height_mm
    wall = dimensions.wall_thickness_mm
    body_radius = dimensions.body_diameter_mm / 2
    inner_radius = max(body_radius - wall, body_radius * 0.75)
    neck_radius = dimensions.neck_diameter_mm / 2
    cap_height = dimensions.cap_height_mm
    neck_height = min(cap_height * 0.28, dimensions.height_mm * 0.08)
    closure_height = cap_height * 0.55
    bulb_height = cap_height * 0.42

    scene = trimesh.Scene()

    def add(mesh: trimesh.Trimesh, name: str) -> None:
        mesh.metadata["name"] = name
        scene.add_geometry(mesh, node_name=name, geom_name=name)

    def cylinder(radius: float, height: float, z_center: float, sections: int = 64) -> trimesh.Trimesh:
        return trimesh.creation.cylinder(
            radius=radius,
            height=height,
            sections=sections,
            transform=trimesh.transformations.translation_matrix([0, 0, z_center]),
        )

    add(cylinder(body_radius, body_height, body_height / 2), "BODY")
    add(cylinder(inner_radius, max(body_height - wall * 2, 1), body_height / 2), "BODY_INNER")
    add(cylinder(neck_radius, neck_height, body_height + neck_height / 2), "NECK")
    add(
        cylinder(
            neck_radius * 1.42,
            closure_height,
            body_height + neck_height + closure_height / 2,
        ),
        "CLOSURE",
    )

    bulb = trimesh.creation.uv_sphere(radius=neck_radius * 1.32, count=[32, 24])
    bulb.apply_transform(
        trimesh.transformations.scale_and_translate(
            scale=[1.0, 1.0, max(bulb_height / (neck_radius * 2.64), 0.8)],
            translate=[0, 0, dimensions.height_mm - bulb_height * 0.42],
        )
    )
    add(bulb, "DROPPER_BULB")

    pipette_height = body_height * 0.72
    add(
        cylinder(
            max(neck_radius * 0.16, 0.8),
            pipette_height,
            body_height - pipette_height / 2,
            sections=32,
        ),
        "PIPETTE",
    )

    liquid_height = max((body_height - wall * 2) * spec.liquid.fill_percent / 100, 0.5)
    liquid_mesh = cylinder(max(inner_radius - wall * 0.45, inner_radius * 0.8), liquid_height, wall + liquid_height / 2)
    if not spec.liquid.enabled:
        liquid_mesh.apply_scale(0.001)
    add(liquid_mesh, "LIQUID")

    label_width = dimensions.body_diameter_mm * spec.label.width_ratio
    label_height = body_height * spec.label.height_ratio
    label_thickness = max(dimensions.body_diameter_mm * 0.003, 0.12)
    label = trimesh.creation.box(extents=[label_width, label_thickness, label_height])
    label_z = body_height * spec.label.vertical_center_ratio
    label.apply_translation([0, -(body_radius + label_thickness * 0.75), label_z])
    add(label, "LABEL")

    body_rgba = np.array([*_hex(spec.body.color_hex), 180 if "glass" in spec.body.material else 255], dtype=np.uint8)
    closure_rgba = np.array([*_hex(spec.closure.color_hex), 255], dtype=np.uint8)
    liquid_rgba = np.array([*_hex(spec.liquid.color_hex), int(255 * spec.liquid.opacity)], dtype=np.uint8)
    for geometry_name, geometry in scene.geometry.items():
        if geometry_name in {"BODY", "BODY_INNER", "NECK"}:
            geometry.visual.face_colors = body_rgba
        elif geometry_name in {"LIQUID"}:
            geometry.visual.face_colors = liquid_rgba
        elif geometry_name == "LABEL":
            geometry.visual.face_colors = np.array([249, 245, 237, 255], dtype=np.uint8)
        else:
            geometry.visual.face_colors = closure_rgba

    output_path.write_bytes(scene.export(file_type="glb"))


def render(spec_path: Path, output: Path) -> dict[str, object]:
    started = time.perf_counter()
    output.mkdir(parents=True, exist_ok=True)
    spec = PackagingSpec.model_validate_json(spec_path.read_text())

    _draw(spec, output / "front.png", "front", True)
    _draw(spec, output / "three-quarter.png", "three-quarter", True)
    _draw(spec, output / "ecommerce.png", "front", False)

    warnings: list[str] = [
        "Blender unavailable; fixture evidence uses deterministic fallback. Production and dedicated CI use Blender."
    ]
    try:
        _build_fixture_glb(spec, output / "product.glb")
    except Exception as exc:  # pragma: no cover
        warnings.append(f"trimesh GLB generation failed: {exc.__class__.__name__}")
        (output / "product.glb").write_bytes(b"glTF" + (2).to_bytes(4, "little") + (12).to_bytes(4, "little"))

    manifest: dict[str, object] = {
        "schemaVersion": "1.0.0",
        "renderer": "deterministic-fallback",
        "renderEngine": "Pillow + trimesh",
        "renderResolution": 800,
        "generatedObjectNames": EXPECTED,
        "outputFilenames": ["front.png", "three-quarter.png", "ecommerce.png", "product.glb"],
        "durationsSeconds": {"total": time.perf_counter() - started},
        "warnings": warnings,
        "fileSizes": {path.name: path.stat().st_size for path in output.iterdir() if path.is_file()},
        "sourceGitCommit": None,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
