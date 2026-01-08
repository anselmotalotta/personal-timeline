
# Multi-stage Docker build with UV for faster installation
FROM python:3.10-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up environment
ENV PATH="/root/.local/bin:$PATH"
WORKDIR /app

# Copy project files for UV
COPY pyproject.toml uv.lock ./
COPY README.md .

# Install dependencies with UV (with pip fallback)
RUN uv sync --frozen || (echo "UV failed, falling back to pip" && \
    uv pip install --system -r src/requirements.txt)

# Runtime stage
FROM python:3.10-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create data directory (skip if already exists)
RUN mkdir -p /app/data || true

# Set environment variables
ENV APP_DATA_DIR=/app/data
ENV ingest_new_data=True
ENV incremental_geo_enrich=False
ENV incremental_image_enrich=False
ENV incremental_export=True
ENV enriched_data_to_json=True

# Expose ports
EXPOSE 8000

# Default command
CMD ["python", "-m", "src.ingest.workflow"]
