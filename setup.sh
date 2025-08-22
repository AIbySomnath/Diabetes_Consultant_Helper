#!/bin/bash
set -e

# Set environment variables
export DEBIAN_FRONTEND=noninteractive
export PIP_NO_CACHE_DIR=off
export PYTHONUNBUFFERED=1

# Update package lists
echo "Updating package lists..."
apt-get update -qq

# Install system dependencies
echo "Installing system dependencies..."
apt-get install -y --no-install-recommends \
    build-essential \
    python3.11-dev \
    python3.11-venv \
    python3.11-distutils \
    python3-pip \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1-mesa-dev \
    libgomp1 \
    swig \
    wget \
    git \
    curl

# Create and activate virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv /app/venv
source /app/venv/bin/activate

# Upgrade pip and setuptools
echo "Upgrading pip and setuptools..."
python -m pip install --upgrade pip==23.3.1 setuptools==65.5.0 wheel==0.41.2

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir --use-pep517 -r requirements.txt

# Install lxml and faiss-cpu separately with verbose output
echo "Installing lxml..."
pip install --no-cache-dir --use-pep517 lxml==4.9.4 --verbose
echo "Installing faiss-cpu..."
pip install --no-cache-dir --use-pep517 faiss-cpu==1.7.4 --verbose

# Clean up
echo "Cleaning up..."
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "Setup completed successfully!"

# Verify installation
echo "Verifying installations..."
python --version
pip list
