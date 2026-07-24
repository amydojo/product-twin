from __future__ import annotations

import uuid

import json
import logging
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request, Response, status
from pydantic import BaseModel

from .job_service import process_job
from .security import ReplayGuard, verify
from .settings import settings
from .supabase_gateway import SupabaseGateway

logger = logging.getLogger("product_twin.api")


def log_event(level: int, event: str, **fields) -> None:
    logger.log(level, json.dumps({"event": event, **fields}, sort_keys=True))
app = FastAPI(title="Product Twin Worker", version="0.1.0")
replay_guard = ReplayGuard()


class StartResponse(BaseModel):
    job_id: str
    accepted: bool
    mode: str


def _run_job(job_id: str) -> None:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        log_event(logging.ERROR, "job_not_started", job_id=job_id, reason="Supabase service configuration missing")
        return
    gateway = SupabaseGateway(settings.supabase_url, settings.supabase_service_role_key)
    try:
        process_job(job_id, gateway, settings)
    except Exception as error:
        # process_job persists a stable failure code before re-raising.
        log_event(logging.ERROR, "background_job_failed", job_id=job_id, error=str(error))
    finally:
        gateway.close()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/ready")
def ready(response: Response) -> dict:
    ready_state = settings.product_twin_fixture_mode or settings.connected_ready
    if not ready_state:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ready" if ready_state else "not_ready",
        "fixtureMode": settings.product_twin_fixture_mode,
        "connectedModeConfigured": settings.connected_ready,
        "backgroundProvider": settings.product_twin_background_provider,
        "blenderRequiredForConnectedRendering": True,
    }


@app.post("/internal/jobs/{job_id}/start", response_model=StartResponse, status_code=202)
async def start(
    job_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    x_product_twin_nonce: str = Header(),
    x_product_twin_timestamp: str = Header(),
    x_product_twin_signature: str = Header(),
) -> StartResponse:
    body = await request.body()
    secret = settings.product_twin_internal_secret
    if not secret or len(secret) < 32:
        raise HTTPException(status_code=503, detail="worker authentication is not configured")
    if not verify(
        request.method,
        request.url.path,
        x_product_twin_timestamp,
        x_product_twin_nonce,
        body,
        x_product_twin_signature,
        secret,
    ):
        raise HTTPException(status_code=401, detail="invalid worker signature")
    if not replay_guard.accept(x_product_twin_nonce):
        raise HTTPException(status_code=409, detail="replayed worker request")
    if not settings.product_twin_fixture_mode and not settings.connected_ready:
        raise HTTPException(status_code=503, detail="worker service configuration is incomplete")
    if not settings.product_twin_fixture_mode:
        background_tasks.add_task(_run_job, str(job_id))
    return StartResponse(
        job_id=str(job_id),
        accepted=True,
        mode="fixture" if settings.product_twin_fixture_mode else "supabase",
    )
