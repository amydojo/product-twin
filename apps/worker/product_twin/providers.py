from __future__ import annotations
from pathlib import Path
from typing import Protocol
from PIL import Image, ImageChops
from .models import BackgroundRemovalResult
class BackgroundRemovalProvider(Protocol):
    def remove_background(self,image_path:Path,output_dir:Path)->BackgroundRemovalResult: ...
class DeterministicFixtureProvider:
    def remove_background(self,image_path:Path,output_dir:Path)->BackgroundRemovalResult:
        output_dir.mkdir(parents=True,exist_ok=True)
        image=Image.open(image_path).convert('RGBA')
        bg=Image.new('RGBA',image.size,(250,249,246,255))
        diff=ImageChops.difference(image,bg).convert('L').point(lambda p:255 if p>18 else 0)
        isolated=image.copy(); isolated.putalpha(diff)
        out=output_dir/'isolated.png'; mask=output_dir/'mask.png'; isolated.save(out); diff.save(mask)
        return BackgroundRemovalResult(provider='deterministic-fixture',image_path=str(out),mask_path=str(mask))
class NoOpProvider:
    def remove_background(self,image_path:Path,output_dir:Path)->BackgroundRemovalResult:
        output_dir.mkdir(parents=True,exist_ok=True); out=output_dir/'isolated.png'; Image.open(image_path).convert('RGBA').save(out)
        return BackgroundRemovalResult(provider='noop',image_path=str(out),fallback_used=True,warnings=['background removal disabled'])
class BiRefNetProvider:
    def __init__(self,model_id:str,revision:str,cache_dir:Path): self.model_id=model_id; self.revision=revision; self.cache_dir=cache_dir; self._model=None
    def _load(self):
        try:
            import torch
            from transformers import AutoModelForImageSegmentation
        except ImportError as exc: raise RuntimeError('Install worker model extras: uv sync --extra models') from exc
        try:
            self._model=AutoModelForImageSegmentation.from_pretrained(self.model_id,revision=self.revision,trust_remote_code=True,cache_dir=self.cache_dir)
            self._model.eval()
        except Exception as exc: raise RuntimeError(f'BiRefNet load failed for pinned revision {self.revision}: {exc}') from exc
        return self._model
    def remove_background(self,image_path:Path,output_dir:Path)->BackgroundRemovalResult:
        model=self._model or self._load()
        try:
            import torch
            from torchvision import transforms
            image=Image.open(image_path).convert('RGB'); size=image.size
            tensor=transforms.Compose([transforms.Resize((1024,1024)),transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])(image).unsqueeze(0)
            with torch.inference_mode(): pred=model(tensor)[-1].sigmoid().cpu()[0].squeeze()
            mask=transforms.ToPILImage()(pred).resize(size)
            output_dir.mkdir(parents=True,exist_ok=True); isolated=image.convert('RGBA'); isolated.putalpha(mask)
            out=output_dir/'isolated.png'; mask_path=output_dir/'mask.png'; isolated.save(out); mask.save(mask_path)
            return BackgroundRemovalResult(provider='birefnet',image_path=str(out),mask_path=str(mask_path))
        except MemoryError as exc: raise RuntimeError('BiRefNet ran out of memory; use fixture or no-op mode on CPU') from exc
        except Exception as exc: raise RuntimeError(f'BiRefNet inference failed: {exc}') from exc
