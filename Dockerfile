# Menggunakan versi 3.9-slim-bullseye (Debian 11) untuk kompatibilitas C++ (CGAL 5.2) dan Python Legacy (Rasterio 1.2)
FROM python:3.11

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Update apt and install ALL system dependencies first
# This ensures gdal-config, cmake, etc. are available for both pip and geoflow build
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    cmake \
    libboost-all-dev \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    proj-bin \
    libcgal-dev \
    libeigen3-dev \
    nlohmann-json3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set PROJ_DIR to help pyproj find the installed library
ENV PROJ_DIR=/usr

# Install Go (versi terbaru stabil)
ENV GO_VERSION=1.21.6
RUN curl -OL https://golang.org/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    rm go${GO_VERSION}.linux-amd64.tar.gz

# Add Go to PATH
ENV PATH=$PATH:/usr/local/go/bin

# Set Working Directory
WORKDIR /app

# Copy Requirements first (caching layer)
COPY requirements.txt .

# Install Python Dependencies
# Pre-install legacy Cython and Numpy (required for rasterio/pyproj build)
# We disable build isolation to force usage of our pinned Cython
RUN pip install "Cython<3" "numpy<2.0.0" wheel setuptools && \
    sed -i '/GDAL/d' requirements.txt && \
    pip install --no-cache-dir --no-build-isolation -r requirements.txt && \
    pip install GDAL==$(gdal-config --version)

# --- INSTALL LAStools (Required by Geoflow) ---
RUN git clone https://github.com/LAStools/LAStools.git /tmp/LAStools && \
    cd /tmp/LAStools && \
    mkdir build && cd build && \
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local && \
    make -j$(nproc) && \
    make install && \
    cd / && rm -rf /tmp/LAStools

# --- INSTALL GEOFLOW (Build from Source) ---
# Clone and Build Geoflow Bundle
RUN git clone --recursive https://github.com/geoflow3d/geoflow-bundle.git /tmp/geoflow-bundle && \
    cd /tmp/geoflow-bundle && \
    mkdir build && cd build && \
    cmake .. \
        -DGF_BUILD_GUI=OFF \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DCMAKE_BUILD_TYPE=Release && \
    make && \
    make install && \
    # Cleanup to keep image small
    cd / && rm -rf /tmp/geoflow-bundle

# Copy Main Application Code
COPY . .

# Create 'output' directory for temp processing
RUN mkdir -p output

# Expose port (untuk API nanti)
EXPOSE 8080

# Command default: Jalankan API Web Service
CMD ["uvicorn", "src.cloud.api:app", "--host", "0.0.0.0", "--port", "8080"]
