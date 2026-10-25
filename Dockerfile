# Stage 1: build frontend
FROM node:22-alpine AS web-builder
WORKDIR /build/web
COPY web/package.json web/package-lock.json* ./
RUN npm ci --prefer-offline
COPY web/ ./
RUN npm run build

# Stage 2: build/install API deps
FROM python:3.11-slim AS api-builder
WORKDIR /build/api
RUN pip install uv --no-cache-dir
COPY api/pyproject.toml ./
RUN uv pip install --system --no-cache fastapi "uvicorn[standard]" pydantic

# Stage 3: runtime
FROM python:3.11-slim AS runtime

# Non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=api-builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=api-builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy API source
COPY api/app ./app

# Copy built frontend
COPY --from=web-builder /build/web/dist ./static

ENV FORZA_DB_PATH=/data/forza_tuning.db
ENV STATIC_DIR=/app/static

# tmpfs for /tmp only; root FS is read-only at runtime via compose
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
