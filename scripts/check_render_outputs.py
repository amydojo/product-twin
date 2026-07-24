#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageStat
import trimesh

REQUIRED_FILES = ("front.png", "three-quarter.png", "ecommerce.png", "product.glb", "manifest.json")
REQUIRED_GLTF_NODES = {"BODY", "NECK", "CLOSURE", "DROPPER_BULB", "PIPETTE", "LABEL"}


def check_image(path: Path, transparent: bool) -> dict[str, object]:
    with Image.open(path) as source:
        source.load()
        mode = source.mode
        size = source.size
        rgba = source.convert("RGBA")
    if size[0] != size[1] or size[0] < 512:
        raise AssertionError(
            f"{path.name} must be a square render of at least 512 px; got {size}"
        )
    alpha = rgba.getchannel("A")
    alpha_min, alpha_max = alpha.getextrema()
    if transparent and not (alpha_min == 0 and alpha_max > 0):
        raise AssertionError(f"{path.name} does not contain a transparent background and visible product")
    if not transparent and (alpha_min, alpha_max) != (255, 255):
        raise AssertionError(
            f"{path.name} must be fully opaque; alpha range was {(alpha_min, alpha_max)}"
        )
    corners = [
        rgba.getpixel((0, 0)),
        rgba.getpixel((rgba.width - 1, 0)),
        rgba.getpixel((0, rgba.height - 1)),
        rgba.getpixel((rgba.width - 1, rgba.height - 1)),
    ]
    if not transparent:
        if any(pixel != (255, 255, 255, 255) for pixel in corners):
            raise AssertionError(
                f"{path.name} corners must be literal white; got {corners}"
            )
    luminance = ImageStat.Stat(rgba.convert("L"))
    if luminance.var[0] < 2:
        raise AssertionError(
            f"{path.name} appears visually empty; luminance variance was {luminance.var[0]}"
        )
    return {
        "mode": mode,
        "size": [size[0], size[1]],
        "alphaRange": [alpha_min, alpha_max],
        "cornerPixels": [list(pixel) for pixel in corners],
        "luminanceVariance": luminance.var[0],
    }


def check(output: Path) -> dict[str, object]:
    for filename in REQUIRED_FILES:
        path = output / filename
        if not path.is_file() or path.stat().st_size <= 10:
            raise AssertionError(f"missing or empty output: {filename}")
    image_results = {
        "front": check_image(output / "front.png", True),
        "threeQuarter": check_image(output / "three-quarter.png", True),
        "ecommerce": check_image(output / "ecommerce.png", False),
    }
    glb = output / "product.glb"
    if glb.stat().st_size >= 10 * 1024 * 1024:
        raise AssertionError("fixture GLB exceeds 10 MB")
    scene = trimesh.load(glb, force="scene")
    nodes = {str(node) for node in scene.graph.nodes}
    normalized_nodes = {node.split(".")[0] for node in nodes}
    manifest = json.loads((output / "manifest.json").read_text())
    manifest_objects = set(manifest.get("generatedObjectNames", []))
    missing_from_manifest = REQUIRED_GLTF_NODES - manifest_objects
    if missing_from_manifest:
        raise AssertionError(f"manifest is missing required generated object names: {sorted(missing_from_manifest)}")
    missing_from_glb = REQUIRED_GLTF_NODES - normalized_nodes
    if missing_from_glb:
        raise AssertionError(
            "GLB is missing required named nodes: "
            f"{sorted(missing_from_glb)}; exported nodes were {sorted(nodes)}"
        )
    manifest_outputs = set(manifest.get("outputFilenames", []))
    expected_outputs = set(REQUIRED_FILES) - {"manifest.json"}
    if manifest_outputs != expected_outputs:
        raise AssertionError(
            "manifest output filenames differ from rendered files: "
            f"expected {sorted(expected_outputs)}, got {sorted(manifest_outputs)}"
        )
    manifest_sizes = manifest.get("fileSizes", {})
    size_mismatches = {
        filename: {
            "manifest": manifest_sizes.get(filename),
            "actual": (output / filename).stat().st_size,
        }
        for filename in expected_outputs
        if manifest_sizes.get(filename) != (output / filename).stat().st_size
    }
    if size_mismatches:
        raise AssertionError(f"manifest file sizes are inaccurate: {size_mismatches}")
    return {
        "images": image_results,
        "glbBytes": glb.stat().st_size,
        "glbNodes": sorted(nodes),
        "manifestRenderer": manifest.get("renderer") or manifest.get("renderEngine"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.output), indent=2))
    except Exception as exc:
        diagnostics = {
            "output": str(args.output),
            "files": {
                path.name: path.stat().st_size
                for path in args.output.iterdir()
                if path.is_file()
            } if args.output.is_dir() else {},
            "error": f"{type(exc).__name__}: {exc}",
        }
        print(json.dumps(diagnostics, indent=2))
        raise


if __name__ == "__main__":
    main()
