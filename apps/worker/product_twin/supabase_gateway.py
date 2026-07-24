from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import httpx


@dataclass(frozen=True)
class JobRecord:
    id: str
    project_id: str
    user_id: str
    status: str
    attempt_count: int


@dataclass(frozen=True)
class AssetRecord:
    id: str
    kind: str
    bucket: str
    object_path: str
    mime_type: str


class SupabaseGateway:
    """Narrow service-role boundary. The browser never receives this client."""

    def __init__(self, url: str, key: str, timeout_seconds: float = 30) -> None:
        if not url or not key:
            raise ValueError("Supabase service configuration is required")
        self.url = url.rstrip("/")
        self.key = key
        self.client = httpx.Client(timeout=timeout_seconds, headers=self._headers())

    def close(self) -> None:
        self.client.close()

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def claim_job(self, job_id: str, worker_id: str) -> JobRecord:
        response = self.client.post(
            f"{self.url}/rest/v1/rpc/claim_render_job",
            json={"p_job_id": job_id, "p_worker_id": worker_id},
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            raise LookupError("job is not claimable or retry limit was reached")
        row = rows[0]
        return JobRecord(
            id=row["id"],
            project_id=row["project_id"],
            user_id=row["user_id"],
            status=row["status"],
            attempt_count=row["attempt_count"],
        )

    def approved_spec(self, project_id: str) -> dict:
        response = self.client.get(
            f"{self.url}/rest/v1/packaging_specs",
            params={
                "select": "spec,version,schema_version",
                "project_id": f"eq.{project_id}",
                "is_approved": "eq.true",
                "order": "version.desc",
                "limit": "1",
            },
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            raise LookupError("approved packaging specification was not found")
        return rows[0]["spec"]

    def project_assets(self, project_id: str) -> list[AssetRecord]:
        response = self.client.get(
            f"{self.url}/rest/v1/assets",
            params={
                "select": "id,kind,bucket,object_path,mime_type",
                "project_id": f"eq.{project_id}",
                "order": "created_at.asc",
            },
        )
        response.raise_for_status()
        return [AssetRecord(**row) for row in response.json()]

    @staticmethod
    def validate_owned_path(user_id: str, object_path: str) -> None:
        if object_path.startswith("/") or ".." in Path(object_path).parts:
            raise ValueError("unsafe object path")
        if not object_path.startswith(f"{user_id}/"):
            raise PermissionError("object path is not owned by the job user")

    def download_asset(self, user_id: str, asset: AssetRecord, destination: Path) -> None:
        self.validate_owned_path(user_id, asset.object_path)
        encoded_path = quote(asset.object_path, safe="/")
        response = self.client.get(
            f"{self.url}/storage/v1/object/authenticated/{asset.bucket}/{encoded_path}",
            headers={"apikey": self.key, "Authorization": f"Bearer {self.key}"},
        )
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)

    def upload_asset(self, bucket: str, object_path: str, source: Path, mime_type: str) -> None:
        encoded_path = quote(object_path, safe="/")
        response = self.client.post(
            f"{self.url}/storage/v1/object/{bucket}/{encoded_path}",
            content=source.read_bytes(),
            headers={
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Content-Type": mime_type,
                "x-upsert": "true",
            },
        )
        response.raise_for_status()

    def upsert_asset_record(self, row: dict) -> None:
        response = self.client.post(
            f"{self.url}/rest/v1/assets",
            params={"on_conflict": "bucket,object_path"},
            json=row,
            headers=self._headers("resolution=merge-duplicates,return=minimal"),
        )
        response.raise_for_status()

    def update_job(self, job_id: str, values: dict) -> None:
        response = self.client.patch(
            f"{self.url}/rest/v1/render_jobs",
            params={"id": f"eq.{job_id}"},
            json=values,
            headers=self._headers("return=minimal"),
        )
        response.raise_for_status()

    def update_project(self, project_id: str, values: dict) -> None:
        response = self.client.patch(
            f"{self.url}/rest/v1/projects",
            params={"id": f"eq.{project_id}"},
            json=values,
            headers=self._headers("return=minimal"),
        )
        response.raise_for_status()
