from __future__ import annotations

from pathlib import Path

_EXCLUDED = {
    "BODY_INNER",
    "GROUND",
    "CAM_FRONT",
    "CAM_THREE_QUARTER",
    "CAM_ECOM",
    "SOFTBOX_KEY",
    "SOFTBOX_FILL",
    "SOFTBOX_RIM",
}


def _apply_mesh_transforms(bpy) -> None:
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.name in _EXCLUDED:
            continue
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        obj.select_set(False)


def export_glb(bpy, path: Path) -> None:
    _apply_mesh_transforms(bpy)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.name not in _EXCLUDED:
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
    )
