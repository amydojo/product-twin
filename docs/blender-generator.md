# Blender generator

## Authoritative command

```bash
blender --background \
  --python apps/worker/product_twin/blender/generate.py \
  -- \
  --spec /work/spec.json \
  --label /work/label.png \
  --output /work/output
```

The worker constructs this as an argument list. Requests cannot replace the script or provide shell syntax.

## Geometry strategy

`round_dropper.py` creates the bottle from a 64-segment rotational profile. The profile contains a short base transition, cylindrical body, editable shoulder transition, and neck. A Solidify modifier applies the requested wall thickness and a restrained bevel softens manufactured edges. Geometry is deterministic and bounded rather than sampled from a generative mesh model.

Stable object names:

- `BODY`: visible outer rotational shell
- `BODY_INNER`: hidden inner reference shell
- `NECK`: separate neck cylinder
- `CLOSURE`: beveled closure cylinder
- `DROPPER_BULB`: smooth dropper bulb
- `PIPETTE`: separate inner tube
- `LIQUID`: independent inner fill volume when enabled
- `LABEL`: front artwork plane offset from the surface
- `GROUND`: studio contact surface
- `CAM_FRONT`, `CAM_THREE_QUARTER`, `CAM_ECOM`: fixed render cameras

The GLB export applies transforms, excludes cameras, lights, ground, and the hidden reference shell, exports valid normals and materials, and targets less than 10 MB for the fixture.

## Materials

Reusable Principled BSDF presets cover clear glass, frosted glass, glossy plastic, matte plastic, and metal closures. User values are clamped to physically meaningful ranges for roughness, transmission, IOR, metallic weight, coat, and alpha. Materials remain separate from mesh topology so the same geometry can be restyled.

## Label mapping

Uploaded artwork becomes an image texture on `LABEL`. Color and alpha outputs connect to the Principled shader, transparent pixels remain transparent, image aspect ratio is preserved by the supplied label ratios, and the plane sits 0.22 mm beyond the nominal body radius to prevent z-fighting.

## Cameras and lighting

- `CAM_FRONT`: centered evidence view
- `CAM_THREE_QUARTER`: controlled dimensional view
- `CAM_ECOM`: centered marketplace view

Three large area lights act as key, fill, and rim softboxes. The ground supplies a subtle contact shadow where the output contract permits it. Transparent views hide the ground and enable film transparency. Ecommerce renders the lit product with alpha and composites that Blender output over literal white, which makes every background corner exactly `(255,255,255)` without altering product pixels. The scene avoids neon, dramatic colored light, and unbounded reflections.

## Outputs

- `front.png`: transparent front view
- `three-quarter.png`: transparent dimensional view
- `ecommerce.png`: fully opaque white-background view
- `product.glb`: reusable model for Three.js
- `manifest.json`: schema version, Blender version, render engine, resolution, object names, logical output filenames, per-stage durations, warnings, file sizes, source Git commit, and input filenames (never absolute worker paths)

`scripts/check_render_outputs.py` performs structural and targeted visual assertions. It verifies files are nonempty, images are square and nonblank, transparent views contain both transparent and visible pixels, ecommerce is fully opaque with four literal-white corners, manifest filenames and sizes are accurate, the GLB parses with required named nodes, and the fixture stays below 10 MB. It reports the actual alpha range, corner pixels, dimensions, luminance variance, GLB nodes, and file sizes without relying on a brittle whole-image snapshot.
