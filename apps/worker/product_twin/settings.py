from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    product_twin_internal_secret: str = "development-only-change-me-32-bytes"
    product_twin_fixture_mode: bool = True
    product_twin_worker_id: str = "product-twin-worker"
    product_twin_background_provider: str = "deterministic-fixture"
    product_twin_temp_root: str | None = None
    hf_home: str = ".model-cache"
    birefnet_model_id: str = "ZhengPeng7/BiRefNet_lite"
    birefnet_model_revision: str = "7838f1c3472f827cd8ce13ab5ccc2ce48077360f"

    @property
    def connected_ready(self) -> bool:
        return bool(
            self.supabase_url
            and self.supabase_service_role_key
            and self.product_twin_internal_secret
            and self.product_twin_internal_secret != "development-only-change-me-32-bytes"
        )


settings = Settings()
