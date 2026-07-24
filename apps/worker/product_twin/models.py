from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
Color=str
class Dimensions(BaseModel):
    model_config=ConfigDict(extra='forbid',populate_by_name=True)
    height_mm: float=Field(alias='heightMm',gt=20,le=400)
    body_diameter_mm: float=Field(alias='bodyDiameterMm',gt=5,le=200)
    neck_diameter_mm: float=Field(alias='neckDiameterMm',gt=3,le=80)
    cap_height_mm: float=Field(alias='capHeightMm',gt=5,le=120)
    wall_thickness_mm: float=Field(alias='wallThicknessMm',gt=.2,le=8)
    @model_validator(mode='after')
    def physical(self):
        if self.neck_diameter_mm >= self.body_diameter_mm: raise ValueError('neck must be narrower than body')
        if self.wall_thickness_mm*2 >= self.body_diameter_mm: raise ValueError('wall thickness leaves no inner volume')
        if self.cap_height_mm >= self.height_mm*.7: raise ValueError('cap is implausibly tall')
        return self
class Body(BaseModel):
    model_config=ConfigDict(extra='forbid',populate_by_name=True)
    shoulder_start_ratio: float=Field(alias='shoulderStartRatio',ge=.45,le=.95)
    shoulder_curvature: float=Field(alias='shoulderCurvature',ge=0,le=1)
    material: Literal['clear-glass','frosted-glass','glossy-plastic','matte-plastic']
    color_hex: Color=Field(alias='colorHex')
    roughness: float=Field(ge=0,le=1)
    transmission: float=Field(ge=0,le=1)
    ior: float=Field(ge=1,le=2.5)
class Closure(BaseModel):
    model_config=ConfigDict(extra='forbid',populate_by_name=True)
    type: Literal['dropper']; material: Literal['glossy-plastic','matte-plastic','metal']
    color_hex: Color=Field(alias='colorHex'); roughness: float=Field(ge=0,le=1)
class Liquid(BaseModel):
    model_config=ConfigDict(extra='forbid',populate_by_name=True)
    enabled: bool; fill_percent: float=Field(alias='fillPercent',ge=0,le=100)
    color_hex: Color=Field(alias='colorHex'); opacity: float=Field(ge=0,le=1)
class Label(BaseModel):
    model_config=ConfigDict(extra='forbid',populate_by_name=True)
    mode: Literal['uploaded-artwork','none']; placement: Literal['front-decal']; artwork_asset_id: str|None=Field(alias='artworkAssetId')
    width_ratio: float=Field(alias='widthRatio',gt=0,le=.95); height_ratio: float=Field(alias='heightRatio',gt=0,le=.8); vertical_center_ratio: float=Field(alias='verticalCenterRatio',ge=.15,le=.85)
class Render(BaseModel):
    model_config=ConfigDict(extra='forbid',populate_by_name=True)
    preset: Literal['clean-studio']; resolution: int=Field(ge=512,le=4096); transparent_background: bool=Field(alias='transparentBackground')
class Provenance(BaseModel):
    model_config=ConfigDict(extra='forbid',populate_by_name=True)
    inferred_from_asset_ids: list[str]=Field(alias='inferredFromAssetIds'); analysis_provider: Literal['manual','birefnet','deterministic-fixture','noop']=Field(alias='analysisProvider'); confidence: float|None=Field(default=None,ge=0,le=1)
class PackagingSpec(BaseModel):
    model_config=ConfigDict(extra='forbid',populate_by_name=True)
    schema_version: Literal['1.0.0']=Field(default='1.0.0',alias='schemaVersion')
    archetype: Literal['round-dropper']; dimensions: Dimensions; body: Body; closure: Closure; liquid: Liquid; label: Label; render: Render; provenance: Provenance
    @field_validator('body','closure','liquid')
    @classmethod
    def colors(cls,v):
        import re
        data=v.model_dump(by_alias=True)
        for k,val in data.items():
            if k=='colorHex' and not re.fullmatch(r'#[0-9A-Fa-f]{6}',val): raise ValueError('invalid color')
        return v
    @model_validator(mode='after')
    def liquid_consistency(self):
        if not self.liquid.enabled and self.liquid.fill_percent != 0: raise ValueError('disabled liquid must have zero fill')
        return self
class BackgroundRemovalResult(BaseModel):
    provider: str; image_path: str; mask_path: str|None=None; fallback_used: bool=False; warnings: list[str] = Field(default_factory=list)
