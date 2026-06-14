# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm
RUN pnpm install
COPY frontend/ ./
RUN pnpm build

# Stage 2: Build Backend
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install curl (required for uv install script)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install uv
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod +x /install.sh && /install.sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy requirements
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Stage 3: Final
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=backend-builder /app/.venv /app/.venv

# Copy application code
COPY app /app/app
COPY generate_sample_dataset.py /app/generate_sample_dataset.py

# Copy built frontend from frontend-builder
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose port (Render expects this)
EXPOSE 8000

# Run migrations and start the server
CMD ["sh", "-c", "alembic -c /app/app/alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
