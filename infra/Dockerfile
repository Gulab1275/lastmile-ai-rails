# ==============================================================================
# Multi-stage Production Dockerfile for Rahbar API Gateway
# Target Platform: AWS EC2 Ubuntu 24.04 / t3.small
# Security: Non-root user, minimal image size, healthcheck configured
# ==============================================================================

# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Production Runtime ---
FROM python:3.11-slim AS runner

WORKDIR /app

# Install runtime dependencies & curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root application user first
RUN groupadd -g 1001 rahbar && \
    useradd -u 1001 -g rahbar -s /bin/bash -m rahbar

# Copy installed Python packages from builder into the rahbar user's home
COPY --from=builder --chown=rahbar:rahbar /root/.local /home/rahbar/.local
ENV PATH=/home/rahbar/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Copy application code
COPY --chown=rahbar:rahbar services/ /app/services/
COPY --chown=rahbar:rahbar mock/ /app/mock/

USER rahbar

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
