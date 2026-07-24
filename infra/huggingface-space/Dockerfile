FROM ubuntu:24.04

ARG PRODUCT_TWIN_REF=agent/product-twin-v0-1
ENV DEBIAN_FRONTEND=noninteractive \
    HF_HOME=/data/.huggingface \
    PYTHONUNBUFFERED=1 \
    PRODUCT_TWIN_FIXTURE_MODE=true \
    PRODUCT_TWIN_BACKGROUND_PROVIDER=deterministic-fixture

RUN apt-get update \
    && apt-get install -y --no-install-recommends blender ca-certificates git python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch "${PRODUCT_TWIN_REF}" \
    https://github.com/amydojo/product-twin.git /opt/product-twin

WORKDIR /opt/product-twin/apps/worker
RUN python3 -m pip install --break-system-packages --no-cache-dir \
    -r requirements.lock.txt

EXPOSE 7860
CMD ["python3", "-m", "uvicorn", "product_twin.api:app", "--host", "0.0.0.0", "--port", "7860"]
