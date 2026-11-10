# Multi-Stage Build: AI Learning Workbench
# Stage 1: Build React 19 Frontend SPA
FROM node:22-alpine AS frontend-builder
WORKDIR /build/app/frontend

COPY app/frontend/package*.json ./
RUN npm install --silent

COPY app/frontend/ ./
RUN npm run build

# Stage 2: Production Python Backend & SPA Server
FROM python:3.12-slim
WORKDIR /workspace

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir fastapi uvicorn websockets pydantic requests

COPY bin/ ./bin/
COPY learning_engine/ ./learning_engine/
COPY app/backend/ ./app/backend/
COPY topics/ ./topics/

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder /build/app/frontend/dist ./app/frontend/dist

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
