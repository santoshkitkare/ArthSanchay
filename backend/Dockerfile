# Multi-stage build: Node builds the React SPA, then the Python runtime image serves both the
# API and the built frontend from one process (PRD.md §10.3).

FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
# vite.config.ts's outDir points at ../backend/app/static for local `npm run build` convenience,
# but that sibling directory doesn't exist inside this isolated build stage, so pin the output
# to ./dist here and copy it explicitly into the runtime image below.
RUN npm run build -- --outDir dist --emptyOutDir

FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=production

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /frontend/dist ./app/static

RUN mkdir -p /app/data
VOLUME ["/app/data"]

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
