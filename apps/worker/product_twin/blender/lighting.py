from __future__ import annotations

from product_twin.blender.cameras import look_at


def _area(bpy, name: str, location, energy: float, size: float, target) -> None:
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    look_at(light, target)


def add_studio_lighting(bpy, height: float) -> None:
    target = (0, 0, height * 0.48)
    _area(bpy, "SOFTBOX_KEY", (-height * 0.9, -height * 0.75, height * 1.25), 1050, height * 0.95, target)
    _area(bpy, "SOFTBOX_FILL", (height * 0.8, -height * 0.35, height * 0.82), 520, height * 0.72, target)
    _area(bpy, "SOFTBOX_RIM", (0, height * 0.72, height * 1.03), 760, height * 0.68, target)
