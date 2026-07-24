from pathlib import Path
from PIL import Image
from .models import PackagingSpec

def visible_bbox(mask_path:Path)->tuple[int,int,int,int]:
    image=Image.open(mask_path).convert('L'); box=image.getbbox()
    if box is None: raise ValueError('mask contains no visible product')
    return box

def infer_round_dropper(total_height_mm:float,mask_path:Path)->dict[str,float]:
    x0,y0,x1,y1=visible_bbox(mask_path); ratio=(x1-x0)/max(1,(y1-y0))
    diameter=max(12,min(total_height_mm*.62,total_height_mm*ratio))
    return {'bodyDiameterMm':round(diameter,2),'neckDiameterMm':round(diameter*.43,2),'capHeightMm':round(total_height_mm*.28,2),'shoulderStartRatio':.78,'shoulderCurvature':.45}
