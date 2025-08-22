#!/bin/bash

# Update and install system dependencies
echo "Updating package lists..."
apt-get update -qq

echo "Installing build dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-venv \
    swig \
    wget \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install lxml dependencies
echo "Installing lxml dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install other system dependencies
echo "Installing other system dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1-mesa-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Clean up
echo "Cleaning up..."
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "System dependencies installation complete!"
