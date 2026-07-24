from __future__ import annotations


def look_at(obj, target=(0.0, 0.0, 45.0)) -> None:
    direction = tuple(target[index] - obj.location[index] for index in range(3))
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_cameras(bpy, height: float, diameter: float):
    distance = max(height * 2.1, diameter * 5.5)
    configurations = {
        "CAM_FRONT": (0, -distance, height * 0.52),
        "CAM_THREE_QUARTER": (distance * 0.62, -distance * 0.82, height * 0.58),
        "CAM_ECOM": (0, -distance * 1.03, height * 0.52),
    }
    cameras = {}
    for name, location in configurations.items():
        data = bpy.data.cameras.new(name)
        camera = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(camera)
        camera.location = location
        data.lens = 72
        data.sensor_width = 36
        look_at(camera, (0, 0, height * 0.47))
        cameras[name] = camera
    return cameras
