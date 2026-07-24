from product_twin.blender.materials import principled_values


def test_presets_clamp() -> None:
    values = principled_values("frosted-glass", 2, -1, 9)
    assert values["roughness"] == 1
    assert values["transmission"] == 0
    assert values["ior"] == 2.5
    assert values["metallic"] == 0


def test_metal_preset_is_metallic() -> None:
    values = principled_values("metal", 0.2, 0, 1.46)
    assert values["metallic"] == 1
