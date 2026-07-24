from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .commands import blender_command, safe_child
from .fallback_renderer import render as fallback_render
from .models import PackagingSpec

REQUIRED_OUTPUTS = ("front.png", "three-quarter.png", "ecommerce.png", "product.glb", "manifest.json")


def validate_outputs(output: Path) -> dict:
    missing = [name for name in REQUIRED_OUTPUTS if not (output / name).is_file()]
    if missing:
        raise RuntimeError(f"renderer did not produce required outputs: {missing}")
    empty = [name for name in REQUIRED_OUTPUTS if (output / name).stat().st_size <= 10]
    if empty:
        raise RuntimeError(f"renderer produced empty outputs: {empty}")
    manifest = json.loads((output / "manifest.json").read_text())
    expected = {"BODY", "CLOSURE", "DROPPER_BULB", "PIPETTE", "LABEL"}
    present = set(manifest.get("generatedObjectNames", []))
    if not expected.issubset(present):
        raise RuntimeError(f"manifest is missing expected objects: {sorted(expected - present)}")
    return manifest


def render_fixture(
    spec_path: Path,
    output: Path,
    label: Path | None = None,
    allow_fallback: bool = True,
) -> dict:
    PackagingSpec.model_validate_json(spec_path.read_text())
    output.mkdir(parents=True, exist_ok=True)
    blender = shutil.which("blender")
    if blender:
        script = Path(__file__).parent / "blender" / "generate.py"
        command = blender_command(
            blender,
            spec_path.resolve(),
            output.resolve(),
            script.resolve(),
            label.resolve() if label else None,
        )
        subprocess.run(command, check=True, timeout=900)
        return validate_outputs(output)
    if not allow_fallback:
        raise RuntimeError("Blender is not installed")
    fallback_render(spec_path, output)
    return validate_outputs(output)


def resolve_work_path(root: Path, relative_name: str) -> Path:
    if Path(relative_name).is_absolute():
        raise ValueError("absolute paths are not accepted")
    return safe_child(root, root / relative_name)
