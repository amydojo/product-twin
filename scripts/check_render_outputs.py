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
    image = Image.open(path)
    if image.width != image.height or image.width < 512:
        raise AssertionError(f"{path.name} must be a square render of at least 512 px")
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    alpha_min, alpha_max = alpha.getextrema()
    if transparent and not (alpha_min == 0 and alpha_max > 0):
        raise AssertionError(f"{path.name} does not contain a transparent background and visible product")
    if not transparent and alpha_min != 255:
        raise AssertionError(f"{path.name} must be fully opaque")
    luminance = ImageStat.Stat(rgba.convert("L"))
    if luminance.var[0] < 2:
        raise AssertionError(f"{path.name} appears visually empty")
    return {"mode":image.mode,"size":[image.width,image.height],"alphaRange":[alpha_min,alpha_max],"luminanceVariance":luminance.var[0]}


def check(output: Path) -> dict[str, object]:
    for filename in REQUIRED_FILES:
        path = output / filename
        if not path.is_file() or path.stat().st_size <= 10:
            raise AssertionError(f"missing or empty output: {filename}")
    image_results={"front":check_image(output/"front.png",True),"threeQuarter":check_image(output/"three-quarter.png",True),"ecommerce":check_image(output/"ecommerce.png",False)}
    glb=output/"product.glb"
    if glb.stat().st_size>=10*1024*1024: raise AssertionError("fixture GLB exceeds 10 MB")
    scene=trimesh.load(glb,force="scene");nodes=set(scene.graph.nodes_geometry);missing=REQUIRED_GLTF_NODES-nodes
    if missing: raise AssertionError(f"GLB missing required named nodes: {sorted(missing)}")
    manifest=json.loads((output/"manifest.json").read_text());manifest_objects=set(manifest.get("generatedObjectNames",[]))
    if not REQUIRED_GLTF_NODES.issubset(manifest_objects): raise AssertionError("manifest is missing required generated object names")
    return {"images":image_results,"glbBytes":glb.stat().st_size,"glbNodes":sorted(nodes),"manifestRenderer":manifest.get("renderer") or manifest.get("renderEngine")}


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("output",type=Path);args=parser.parse_args();print(json.dumps(check(args.output),indent=2))
if __name__=="__main__": main()
