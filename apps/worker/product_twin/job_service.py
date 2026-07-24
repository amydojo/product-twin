from __future__ import annotations

import json
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

import logging

from .models import PackagingSpec
from .providers import BiRefNetProvider, DeterministicFixtureProvider, NoOpProvider
from .service import render_fixture
from .settings import Settings
from .supabase_gateway import AssetRecord, SupabaseGateway

logger = logging.getLogger("product_twin.worker")


def log_event(level: int, event: str, **fields) -> None:
    logger.log(level, json.dumps({"event": event, **fields}, sort_keys=True))

_OUTPUTS = {
    "front.png": ("render_front", "image/png"),
    "three-quarter.png": ("render_three_quarter", "image/png"),
    "ecommerce.png": ("render_ecommerce", "image/png"),
    "product.glb": ("model_glb", "model/gltf-binary"),
    "manifest.json": ("debug_manifest", "application/json"),
}


class JobProcessingError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _provider(settings: Settings):
    name = settings.product_twin_background_provider
    if name == "birefnet":
        return BiRefNetProvider(
            settings.birefnet_model_id,
            settings.birefnet_model_revision,
            Path(settings.hf_home),
        )
    if name == "noop":
        return NoOpProvider()
    if name == "deterministic-fixture":
        return DeterministicFixtureProvider()
    raise JobProcessingError("invalid_provider", f"Unknown background provider: {name}")


def _source_asset(assets: list[AssetRecord], kind: str) -> AssetRecord | None:
    return next((asset for asset in assets if asset.kind == kind), None)


def _isolate_source(
    source_path: Path,
    analysis_dir: Path,
    settings: Settings,
) -> tuple[Path, Path | None, dict]:
    provider = _provider(settings)
    warnings: list[str] = []
    try:
        result = provider.remove_background(source_path, analysis_dir)
    except Exception as error:
        warnings.append(f"{settings.product_twin_background_provider} failed: {error}")
        fallback = NoOpProvider().remove_background(source_path, analysis_dir)
        result = fallback.model_copy(update={"warnings": [*fallback.warnings, *warnings]})
    return Path(result.image_path), Path(result.mask_path) if result.mask_path else None, {
        "provider": result.provider,
        "fallbackUsed": result.fallback_used,
        "warnings": result.warnings,
    }


def _record_local_asset(
    gateway: SupabaseGateway,
    job,
    source: Path,
    kind: str,
    filename: str,
    mime_type: str,
    metadata: dict | None = None,
) -> None:
    object_path = f"{job.user_id}/{job.project_id}/{job.id}/{filename}"
    gateway.validate_owned_path(job.user_id, object_path)
    gateway.upload_asset("product-outputs", object_path, source, mime_type)
    gateway.upsert_asset_record(
        {
            "project_id": job.project_id,
            "user_id": job.user_id,
            "kind": kind,
            "bucket": "product-outputs",
            "object_path": object_path,
            "mime_type": mime_type,
            "byte_size": source.stat().st_size,
            "metadata": metadata or {},
        }
    )


def process_job(
    job_id: str,
    gateway: SupabaseGateway,
    settings: Settings,
    render: Callable[..., dict] = render_fixture,
) -> dict:
    try:
        uuid.UUID(job_id)
    except ValueError as error:
        raise JobProcessingError("invalid_job_id", "Job ID must be a UUID") from error

    job = gateway.claim_job(job_id, settings.product_twin_worker_id)
    gateway.update_project(job.project_id, {"status": "rendering"})
    temporary_root = Path(settings.product_twin_temp_root).resolve() if settings.product_twin_temp_root else None

    try:
        with tempfile.TemporaryDirectory(prefix=f"product-twin-{job.id}-", dir=temporary_root) as temporary:
            work = Path(temporary)
            inputs = work / "inputs"
            analysis_dir = work / "analysis"
            output = work / "output"
            inputs.mkdir()
            output.mkdir()

            gateway.update_job(job.id, {"current_step": "validating specification"})
            spec = PackagingSpec.model_validate(gateway.approved_spec(job.project_id))
            spec_path = inputs / "spec.json"
            spec_path.write_text(spec.model_dump_json(by_alias=True, indent=2))

            assets = gateway.project_assets(job.project_id)
            source_asset = _source_asset(assets, "source_front")
            if source_asset is None:
                raise JobProcessingError("source_missing", "The front source image is missing")
            source_path = inputs / f"source{Path(source_asset.object_path).suffix or '.img'}"
            gateway.download_asset(job.user_id, source_asset, source_path)

            gateway.update_job(job.id, {"current_step": "preparing geometry"})
            isolated_path, mask_path, analysis = _isolate_source(source_path, analysis_dir, settings)
            _record_local_asset(
                gateway,
                job,
                isolated_path,
                "isolated_product",
                "isolated-product.png",
                "image/png",
                analysis,
            )
            if mask_path is not None:
                _record_local_asset(
                    gateway,
                    job,
                    mask_path,
                    "alpha_mask",
                    "alpha-mask.png",
                    "image/png",
                    analysis,
                )

            label_asset = _source_asset(assets, "label_artwork")
            label_path: Path | None = None
            if label_asset is not None:
                label_path = inputs / f"label{Path(label_asset.object_path).suffix or '.png'}"
                gateway.download_asset(job.user_id, label_asset, label_path)

            gateway.update_job(job.id, {"current_step": "applying materials"})
            manifest = render(spec_path, output, label=label_path, allow_fallback=False)
            manifest["backgroundRemoval"] = analysis
            manifest["jobId"] = job.id
            manifest["projectId"] = job.project_id
            manifest["generationInputs"] = {
                "sourceAssetId": source_asset.id,
                "labelAssetId": label_asset.id if label_asset else None,
                "approvedSchemaVersion": spec.schema_version,
            }
            (output / "manifest.json").write_text(json.dumps(manifest, indent=2))

            for filename, (kind, mime_type) in _OUTPUTS.items():
                if filename.startswith("front") or filename.startswith("three") or filename.startswith("ecommerce"):
                    gateway.update_job(job.id, {"current_step": "rendering views"})
                elif filename == "product.glb":
                    gateway.update_job(job.id, {"current_step": "exporting model"})
                else:
                    gateway.update_job(job.id, {"current_step": "saving outputs"})
                _record_local_asset(gateway, job, output / filename, kind, filename, mime_type)

            completed_at = datetime.now(UTC).isoformat()
            gateway.update_job(
                job.id,
                {
                    "status": "complete",
                    "current_step": "saving outputs",
                    "completed_at": completed_at,
                    "locked_at": None,
                    "locked_by": None,
                },
            )
            gateway.update_project(job.project_id, {"status": "complete"})
            log_event(logging.INFO, "render_job_complete", job_id=job.id, project_id=job.project_id)
            return manifest
    except Exception as error:
        code = error.code if isinstance(error, JobProcessingError) else "render_failed"
        message = str(error)[:1000]
        try:
            gateway.update_job(
                job.id,
                {
                    "status": "failed",
                    "current_step": "failed",
                    "error_code": code,
                    "error_message": message,
                    "completed_at": datetime.now(UTC).isoformat(),
                    "locked_at": None,
                    "locked_by": None,
                },
            )
            gateway.update_project(job.project_id, {"status": "failed"})
        except Exception as update_error:
            log_event(logging.ERROR, "render_job_failure_update_failed", job_id=job.id, error=str(update_error))
        log_event(logging.ERROR, "render_job_failed", job_id=job.id, error_code=code, error=message)
        raise
