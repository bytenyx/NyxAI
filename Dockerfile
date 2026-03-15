# NyxAI Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM docker.xuanyuan.me/python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
# Note: We install the package in editable mode to get all dependencies
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir prometheus-fastapi-instrumentator

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM docker.xuanyuan.me/python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app \
    PORT=8000

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR ${APP_HOME}

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY src/ ${APP_HOME}/src/
COPY pyproject.toml ${APP_HOME}/

# Install the application (without dependencies, they are already in venv)
RUN pip install --no-deps -e .

# Create non-root user
RUN groupadd -r nyxai && useradd -r -g nyxai nyxai && \
    chown -R nyxai:nyxai ${APP_HOME}

# Switch to non-root user
USER nyxai

# Expose port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start application
CMD ["uvicorn", "nyxai.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# =============================================================================
# Stage 3: Development (optional, includes dev dependencies)
# =============================================================================
FROM builder AS development

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

# Install additional dev dependencies
RUN pip install --no-cache-dir -e ".[dev]"

WORKDIR ${APP_HOME}

# Copy application code
COPY . ${APP_HOME}/

# Install the application
RUN pip install --no-deps -e .

EXPOSE 8000

CMD ["uvicorn", "nyxai.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
