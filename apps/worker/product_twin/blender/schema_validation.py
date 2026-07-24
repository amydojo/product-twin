"""Dependency-free validation used inside Blender's bundled Python."""

from __future__ import annotations

import re
from typing import Any

_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_MATERIALS = {"clear-glass", "frosted-glass", "glossy-plastic", "matte-plastic"}


def _number(mapping: dict[str, Any], key: str, minimum: float, maximum: float) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    number = float(value)
    if not minimum < number <= maximum:
        raise ValueError(f"{key} must be greater than {minimum} and at most {maximum}")
    return number


def validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("schemaVersion") != "1.0.0":
        raise ValueError("unsupported schemaVersion")
    if spec.get("archetype") != "round-dropper":
        raise ValueError("unsupported archetype")

    dimensions = spec.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("dimensions must be an object")
    height = _number(dimensions, "heightMm", 20, 400)
    diameter = _number(dimensions, "bodyDiameterMm", 5, 200)
    neck = _number(dimensions, "neckDiameterMm", 3, 80)
    cap = _number(dimensions, "capHeightMm", 5, 120)
    wall = _number(dimensions, "wallThicknessMm", 0.2, 8)
    if neck >= diameter:
        raise ValueError("neckDiameterMm must be narrower than bodyDiameterMm")
    if wall * 2 >= diameter:
        raise ValueError("wallThicknessMm leaves no inner volume")
    if cap >= height * 0.7:
        raise ValueError("capHeightMm is implausibly tall")

    body = spec.get("body")
    if not isinstance(body, dict) or body.get("material") not in _MATERIALS:
        raise ValueError("invalid body material")
    if not _COLOR.fullmatch(str(body.get("colorHex", ""))):
        raise ValueError("invalid body colorHex")
    shoulder_start = body.get("shoulderStartRatio")
    shoulder_curve = body.get("shoulderCurvature")
    if not isinstance(shoulder_start, (int, float)) or not 0.45 <= shoulder_start <= 0.95:
        raise ValueError("invalid shoulderStartRatio")
    if not isinstance(shoulder_curve, (int, float)) or not 0 <= shoulder_curve <= 1:
        raise ValueError("invalid shoulderCurvature")

    closure = spec.get("closure")
    if not isinstance(closure, dict) or closure.get("type") != "dropper":
        raise ValueError("invalid closure")
    if not _COLOR.fullmatch(str(closure.get("colorHex", ""))):
        raise ValueError("invalid closure colorHex")

    liquid = spec.get("liquid")
    if not isinstance(liquid, dict):
        raise ValueError("liquid must be an object")
    fill = liquid.get("fillPercent")
    if not isinstance(fill, (int, float)) or not 0 <= fill <= 100:
        raise ValueError("fillPercent must be between 0 and 100")
    if not liquid.get("enabled") and float(fill) != 0:
        raise ValueError("disabled liquid must have zero fill")
    if not _COLOR.fullmatch(str(liquid.get("colorHex", ""))):
        raise ValueError("invalid liquid colorHex")

    label = spec.get("label")
    if not isinstance(label, dict) or label.get("placement") != "front-decal":
        raise ValueError("invalid label placement")
    for key, lower, upper in (
        ("widthRatio", 0, 0.95),
        ("heightRatio", 0, 0.8),
        ("verticalCenterRatio", 0.15, 0.85),
    ):
        value = label.get(key)
        if not isinstance(value, (int, float)) or not lower < value <= upper:
            raise ValueError(f"invalid {key}")

    render = spec.get("render")
    if not isinstance(render, dict) or render.get("preset") != "clean-studio":
        raise ValueError("invalid render preset")
    resolution = render.get("resolution")
    if not isinstance(resolution, int) or not 512 <= resolution <= 4096:
        raise ValueError("render resolution must be an integer from 512 to 4096")
    return spec
