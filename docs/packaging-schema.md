# Packaging specification 1.0.0

The canonical contract is `packages/packaging-schema/packaging-spec.schema.json`. Zod validates the same values in the browser and Next.js boundary. Pydantic validates them in the worker. Blender performs an additional dependency-free validation before loading scene data. CI fails if the implementations drift.

## Root fields

| Field | Type | Meaning and validation |
|---|---|---|
| `schemaVersion` | literal `1.0.0` | Contract version consumed by every runtime. |
| `archetype` | literal `round-dropper` | Only supported geometry family in v0.1. |
| `dimensions` | object | External dimensions in millimeters. |
| `body` | object | Bottle profile and PBR body material. |
| `closure` | object | Dropper closure material. |
| `liquid` | object | Optional inner liquid volume. |
| `label` | object | Front decal source and placement. |
| `render` | object | Deterministic camera and output preset. |
| `provenance` | object | Which assets and provider produced the draft. |

## `dimensions`

| Field | Unit | Constraint | Meaning |
|---|---:|---:|---|
| `heightMm` | mm | `> 20`, `<= 400` | Total external height including closure. |
| `bodyDiameterMm` | mm | `> 5`, `<= 200` | Maximum round body diameter. |
| `neckDiameterMm` | mm | `> 3`, `< bodyDiameterMm`, `<= 80` | Diameter beneath the closure. |
| `capHeightMm` | mm | `> 5`, `<= 120`, `< 70% of heightMm` | Full closure and bulb allocation. |
| `wallThicknessMm` | mm | `> 0.2`, `<= 8`, less than half the body diameter | Physically plausible wall thickness used by the inner shell and liquid inset. |

## `body`

| Field | Type or unit | Constraint | Meaning |
|---|---|---|---|
| `shoulderStartRatio` | ratio | `0.45` to `0.95` | Point along non-closure body height where the cylindrical wall begins tapering. |
| `shoulderCurvature` | ratio | `0` to `1` | Controls the interpolation of the rotational shoulder profile. |
| `material` | enum | `clear-glass`, `frosted-glass`, `glossy-plastic`, `matte-plastic` | Reusable PBR preset, not baked geometry. |
| `colorHex` | sRGB hex | `#RRGGBB` | Base tint. |
| `roughness` | ratio | `0` to `1` | Principled BSDF roughness. |
| `transmission` | ratio | `0` to `1` | Light transmission for glass-like bodies. |
| `ior` | index | `1` to `2.5` | Index of refraction. |

## `closure`

| Field | Type | Constraint | Meaning |
|---|---|---|---|
| `type` | literal | `dropper` | v0.1 closure family. |
| `material` | enum | `glossy-plastic`, `matte-plastic`, `metal` | Closure PBR preset. |
| `colorHex` | sRGB hex | `#RRGGBB` | Closure tint. |
| `roughness` | ratio | `0` to `1` | Closure surface roughness. Metal also sets metallic weight to one. |

## `liquid`

| Field | Type or unit | Constraint | Meaning |
|---|---|---|---|
| `enabled` | boolean | required | Whether a separate inner liquid object is generated. |
| `fillPercent` | percent | `0` to `100`; must be `0` when disabled | Fraction of the safe inner fill height, not total external height. |
| `colorHex` | sRGB hex | `#RRGGBB` | Liquid tint. |
| `opacity` | ratio | `0` to `1` | Liquid alpha/transmission presentation. |

## `label`

| Field | Type | Constraint | Meaning |
|---|---|---|---|
| `mode` | enum | `uploaded-artwork` or `none` | Whether an uploaded image texture should be applied. |
| `placement` | literal | `front-decal` | v0.1 mapping strategy. |
| `artworkAssetId` | UUID or `null` | valid UUID when present | Owned `label_artwork` asset. |
| `widthRatio` | ratio | `> 0`, `<= 0.95` | Label width divided by body diameter. |
| `heightRatio` | ratio | `> 0`, `<= 0.8` | Label height divided by non-closure body height. |
| `verticalCenterRatio` | ratio | `0.15` to `0.85` | Label center measured from the body base over non-closure height. |

Uploaded PNG transparency and aspect ratio are preserved. The decal plane is offset from the body to prevent coplanar flicker.

## `render`

| Field | Type or unit | Constraint | Meaning |
|---|---|---|---|
| `preset` | literal | `clean-studio` | Fixed neutral lighting and camera family. |
| `resolution` | pixels | integer `512` to `4096` | Width and height of each square render. |
| `transparentBackground` | boolean | required | Requested transparent output behavior; ecommerce remains white by contract. |

## `provenance`

| Field | Type | Constraint | Meaning |
|---|---|---|---|
| `inferredFromAssetIds` | UUID array | each value is a UUID | Source assets used to create the draft. |
| `analysisProvider` | enum | `manual`, `birefnet`, `deterministic-fixture`, `noop` | Adapter that produced the draft or fallback. |
| `confidence` | ratio or `null` | `0` to `1` | Optional provider confidence. It is not shown as fake certainty in the interface. |

## Explicit non-inferences

A single front image does not justify inventing side artwork, embossed geometry, exact thread pitch, hidden back labels, or an unseen asymmetric profile. Product Twin stores those limitations instead of hallucinating them.
