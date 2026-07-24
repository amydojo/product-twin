from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2]))

EXPECTED_OBJECTS = [
    "BODY",
    "BODY_INNER",
    "NECK",
    "CLOSURE",
    "DROPPER_BULB",
    "PIPETTE",
    "LIQUID",
    "LABEL",
    "GROUND",
    "CAM_FRONT",
    "CAM_THREE_QUARTER",
    "CAM_ECOM",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--label")
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None
    return parser.parse_args(arguments)


def git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value or None


def composite_over_white(path: Path) -> None:
    from PIL import Image

    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        white.alpha_composite(rgba)
        white.convert("RGB").save(path, format="PNG")


def main() -> None:
    import bpy

    from product_twin.blender.archetypes.round_dropper import build
    from product_twin.blender.cameras import add_cameras
    from product_twin.blender.export import export_glb
    from product_twin.blender.labels import add_front_label
    from product_twin.blender.lighting import add_studio_lighting
    from product_twin.blender.materials import (
        create_ground_material,
        create_material,
        principled_values,
    )
    from product_twin.blender.scene import configure_scene, reset_scene
    from product_twin.blender.schema_validation import validate_spec

    arguments = parse_args()
    output = Path(arguments.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    raw = json.loads(Path(arguments.spec).read_text())
    spec = validate_spec(raw)
    started = time.perf_counter()
    stages: dict[str, float] = {}
    warnings: list[str] = []

    reset_scene(bpy)
    ground = configure_scene(bpy, spec["render"]["resolution"])
    ground.data.materials.append(create_ground_material(bpy))

    body_values = principled_values(
        spec["body"]["material"],
        spec["body"]["roughness"],
        spec["body"]["transmission"],
        spec["body"]["ior"],
    )
    materials = {
        "body": create_material(bpy, "BODY_MATERIAL", spec["body"]["colorHex"], body_values),
        "closure": create_material(
            bpy,
            "CLOSURE_MATERIAL",
            spec["closure"]["colorHex"],
            principled_values(spec["closure"]["material"], spec["closure"]["roughness"], 0, 1.46),
        ),
        "glass": create_material(
            bpy,
            "PIPETTE_MATERIAL",
            "#f4f4f4",
            principled_values("clear-glass", 0.08, 1, 1.5),
            0.45,
        ),
        "liquid": create_material(
            bpy,
            "LIQUID_MATERIAL",
            spec["liquid"]["colorHex"],
            principled_values("clear-glass", 0.14, 0.5, 1.34),
            spec["liquid"]["opacity"],
        ),
        "label": create_material(
            bpy,
            "LABEL_MATERIAL",
            "#f7f2e8",
            principled_values("matte-plastic", 0.48, 0, 1.46),
        ),
    }

    stage_started = time.perf_counter()
    build(bpy, spec, materials)
    add_front_label(bpy, spec, arguments.label, materials["label"])
    stages["preparing geometry and applying materials"] = time.perf_counter() - stage_started

    add_studio_lighting(bpy, spec["dimensions"]["heightMm"])
    cameras = add_cameras(
        bpy,
        spec["dimensions"]["heightMm"],
        spec["dimensions"]["bodyDiameterMm"],
    )

    render_plan = [
        ("CAM_FRONT", "front.png", True),
        ("CAM_THREE_QUARTER", "three-quarter.png", True),
        ("CAM_ECOM", "ecommerce.png", True),
    ]
    for camera_name, filename, transparent in render_plan:
        stage_started = time.perf_counter()
        bpy.context.scene.camera = cameras[camera_name]
        bpy.context.scene.render.film_transparent = transparent
        ground.hide_render = transparent
        output_path = output / filename
        bpy.context.scene.render.filepath = str(output_path)
        bpy.ops.render.render(write_still=True)
        if filename == "ecommerce.png":
            composite_over_white(output_path)
        stages[filename] = time.perf_counter() - stage_started

    stage_started = time.perf_counter()
    export_glb(bpy, output / "product.glb")
    stages["product.glb"] = time.perf_counter() - stage_started

    present = sorted(obj.name for obj in bpy.context.scene.objects)
    missing = [
        name
        for name in EXPECTED_OBJECTS
        if name not in present and not (name == "LIQUID" and not spec["liquid"]["enabled"])
    ]
    if missing:
        warnings.append(f"missing expected objects: {missing}")

    output_names = ["front.png", "three-quarter.png", "ecommerce.png", "product.glb"]
    file_sizes = {name: (output / name).stat().st_size for name in output_names}
    if file_sizes["product.glb"] > 10 * 1024 * 1024:
        warnings.append("product.glb exceeds the 10 MB fixture target")

    manifest = {
        "schemaVersion": spec["schemaVersion"],
        "blenderVersion": bpy.app.version_string,
        "renderEngine": bpy.context.scene.render.engine,
        "renderResolution": spec["render"]["resolution"],
        "generatedObjectNames": present,
        "outputFilenames": output_names,
        "outputPaths": {name: name for name in output_names},
        "durationsSeconds": stages,
        "warnings": warnings,
        "fileSizes": file_sizes,
        "sourceGitCommit": git_commit(),
        "totalDurationSeconds": time.perf_counter() - started,
        "inputs": {
            "specFilename": Path(arguments.spec).name,
            "labelFilename": Path(arguments.label).name if arguments.label else None,
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
