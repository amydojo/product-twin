from __future__ import annotations


def reset_scene(bpy) -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def configure_scene(bpy, resolution: int):
    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = True
    scene.render.use_file_extension = True
    scene.render.image_settings.compression = 18

    # A neutral white world lights transmitted materials even when film transparency hides it.
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    background.inputs["Strength"].default_value = 0.85
    scene.world.color = (1.0, 1.0, 1.0)
    scene.view_settings.view_transform = "Standard"

    bpy.ops.mesh.primitive_plane_add(size=1000, location=(0, 0, -0.15))
    ground = bpy.context.object
    ground.name = "GROUND"
    ground.is_shadow_catcher = getattr(ground, "is_shadow_catcher", False)
    return ground
