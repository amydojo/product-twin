FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends blender python3.11 python3-pip curl ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY apps/worker/requirements.lock.txt /tmp/requirements.txt
RUN python3 -m pip install --break-system-packages --no-cache-dir -r /tmp/requirements.txt
COPY apps/worker /app
COPY packages /packages
EXPOSE 7860
CMD ["python3","-m","uvicorn","product_twin.api:app","--host","0.0.0.0","--port","7860"]
