# syntax=docker/dockerfile:1
#
# Single image: the React build is served by the FastAPI app on one port.
#   docker build -t stockbrief .                 # production image (last stage)
#   docker build --target dev -t stockbrief:dev . # used by compose.yaml

# --- Frontend build -----------------------------------------------------------
FROM node:22-slim AS frontend-build
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Python dependencies (cached until pyproject.toml changes) ----------------
FROM python:3.12-slim AS backend-base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY backend/pyproject.toml ./
RUN python -c "import tomllib; d = tomllib.load(open('pyproject.toml', 'rb')); \
open('requirements.txt', 'w').write('\n'.join(d['project']['dependencies']))" \
 && pip install -r requirements.txt

# --- Dev: code is bind-mounted by compose.yaml, uvicorn reloads on change -----
FROM backend-base AS dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Runtime -----------------------------------------------------------------
FROM backend-base AS runtime
COPY backend/app ./app
COPY data/ ./data/
COPY --from=frontend-build /fe/dist ./static
# config.py defaults to <repo root>/data, which doesn't exist in this layout.
ENV PORTFOLIO_DATA_PATH=/app/data/sample_portfolio.json
RUN useradd --system --uid 10001 --no-create-home appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
