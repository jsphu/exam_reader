# Use a lightweight python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

# Install system dependencies, including chromium for Selenium
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    libgomp1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt /app/

# Install CPU-only PyTorch and torchvision to keep the image compact (saves ~4-5GB)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Filter out nvidia CUDA packages and torch/torchvision from requirements.txt,
# then install the remaining requirements.
RUN grep -v -E "^(nvidia-|torch|torchvision)" requirements.txt > requirements-docker.txt && \
    pip install --no-cache-dir -r requirements-docker.txt && \
    rm requirements-docker.txt

# Pre-download docling models to bake them into the image.
# This prevents downloading model files (~250MB) on the first API call at runtime.
RUN python -c "from docling.document_converter import DocumentConverter; DocumentConverter()"

# Copy the rest of the application files
COPY . /app/

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the FastAPI server
CMD ["python", "server.py"]
