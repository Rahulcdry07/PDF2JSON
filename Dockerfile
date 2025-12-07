# Multi-stage build for EstimateX - AI-Powered Construction Cost Estimation
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for PyMuPDF
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and pyproject.toml for package installation
COPY requirements.txt pyproject.toml ./
COPY src ./src

# Install Python dependencies and the estimatex package
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user -e .

# Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Make sure scripts are executable
RUN chmod +x scripts/*.py

# Create necessary directories
RUN mkdir -p uploads reference_files examples/input_files examples/output_reports

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH
ENV FLASK_APP=estimatex.web
ENV FLASK_ENV=production

# Expose ports
EXPOSE 8000 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command (can be overridden)
CMD ["python", "-m", "estimatex.web"]
