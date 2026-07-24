---
title: Product Twin Worker
emoji: 🧴
colorFrom: gray
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Product Twin Worker

CPU Docker Space for Product Twin's private FastAPI and Blender worker.

## Required Space secrets

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `PRODUCT_TWIN_INTERNAL_SECRET`

## Recommended variables

- `PRODUCT_TWIN_WORKER_ID=product-twin-hf-space`
- `PRODUCT_TWIN_FIXTURE_MODE=false` after Supabase is connected
- `PRODUCT_TWIN_BACKGROUND_PROVIDER=deterministic-fixture` for the free baseline
- `HF_HOME=/data/.huggingface`

The image clones the exact Product Twin feature branch during build, installs pinned worker dependencies, installs Blender, and exposes `/health`, `/ready`, and the HMAC-protected job endpoint on port 7860. Model weights are never baked into Git. Free CPU rendering works without a GPU but can be slow. BiRefNet is intentionally not installed in the baseline image because its repository does not declare an explicit license; enablement requires a separate license decision and model-enabled dependency layer.

Local smoke test:

```bash
docker build -f infra/huggingface-space/Dockerfile -t product-twin-space .
docker run --rm -p 7860:7860 product-twin-space
curl http://localhost:7860/health
```
