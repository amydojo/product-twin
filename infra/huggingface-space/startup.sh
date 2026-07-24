#!/usr/bin/env bash
set -euo pipefail
exec python3 -m uvicorn product_twin.api:app --host 0.0.0.0 --port "${PORT:-7860}"
