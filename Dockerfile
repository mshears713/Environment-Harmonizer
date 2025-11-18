# Environment Harmonizer - Docker Image
# Multi-stage build for optimal image size

# Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Copy only necessary files for installation
COPY setup.py README.md requirements.txt ./
COPY harmonizer/ ./harmonizer/

# Install the package
RUN pip install --no-cache-dir --user .

# Runtime stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

# Create working directory for projects to be scanned
WORKDIR /workspace

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy the harmonizer package
COPY harmonizer/ /usr/local/lib/python3.11/site-packages/harmonizer/

# Add labels for documentation
LABEL org.opencontainers.image.title="Environment Harmonizer"
LABEL org.opencontainers.image.description="A tool to detect and fix development environment inconsistencies"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.authors="Environment Harmonizer Team"

# Set the entrypoint to the harmonizer CLI
ENTRYPOINT ["harmonizer"]

# Default command - scan current directory
CMD ["."]
