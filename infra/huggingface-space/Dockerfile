FROM ubuntu:24.04

ARG PRODUCT_TWIN_REF=main
ENV DEBIAN_FRONTEND=noninteractive \
    HF_HOME=/data/.huggingface \
    PYTHONUNBUFFERED=1 \
    PRODUCT_TWIN_FIXTURE_MODE=true \
    PRODUCT_TWIN_BACKGROUND_PROVIDER=deterministic-fixture

RUN apt-get update \
    && apt-get install -y --no-install-recommends blender libegl1 libgl1 ca-certificates git python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN git init /opt/product-twin \
    && git -C /opt/product-twin remote add origin https://github.com/amydojo/product-twin.git \
    && git -C /opt/product-twin fetch --depth 1 origin "${PRODUCT_TWIN_REF}" \
    && git -C /opt/product-twin checkout --detach FETCH_HEAD

WORKDIR /opt/product-twin/apps/worker
RUN python3 -m pip install --break-system-packages --no-cache-dir \
    -r requirements.lock.txt \
    && useradd --create-home --uid 1000 producttwin \
    && mkdir -p /data \
    && chown -R producttwin:producttwin /opt/product-twin /data

EXPOSE 7860
USER producttwin
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/health', timeout=3)"
CMD ["python3", "-m", "uvicorn", "product_twin.api:app", "--host", "0.0.0.0", "--port", "7860"]
