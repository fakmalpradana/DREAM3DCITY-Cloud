FROM mambaorg/micromamba:1.5.3

# Switch to root to install system build tools
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Switch back to mamba user
USER $MAMBA_USER

# Install Core dependencies via Conda
# We install python, compilers, and the heavy C++ libs here
RUN micromamba install -y -n base -c conda-forge \
    python=3.10 \
    gdal \
    proj \
    cgal-cpp \
    eigen \
    boost-cpp \
    cmake \
    make \
    go \
    pip \
    numpy \
    cython \
    nlohmann_json \
    shapely \
    geos \
    fiona \
    pyproj \
    rasterio \
    && micromamba clean --all --yes

# Activate the environment
ENV LD_LIBRARY_PATH="/opt/conda/lib:/usr/local/lib:$LD_LIBRARY_PATH" \
    LIBRARY_PATH="/opt/conda/lib:/usr/local/lib:$LIBRARY_PATH" \
    CPATH="/opt/conda/include:/usr/local/include:$CPATH" \
    PATH="/opt/conda/bin:$PATH"

# Switch to root for build/install steps (needs access to /usr/local)
USER root

WORKDIR /app

# Clone and Build LAStools (lightweight enough to build from source)
RUN git clone https://github.com/LAStools/LAStools.git /tmp/LAStools && \
    cd /tmp/LAStools && \
    mkdir build && cd build && \
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local && \
    make -j$(nproc) && \
    make install && \
    cd / && rm -rf /tmp/LAStools

# Build Val3dity (required for gfp-val3dity)
RUN git clone https://github.com/tudelft3d/val3dity.git /tmp/val3dity && \
    cd /tmp/val3dity && \
    mkdir build && cd build && \
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local && \
    make -j$(nproc) && \
    make install && \
    cd / && rm -rf /tmp/val3dity

# Clone and Build Geoflow Bundle
# We rely on Conda's CMAKE_PREFIX_PATH to find libs (Conda env is in /opt/conda)
RUN git clone --recursive https://github.com/geoflow3d/geoflow-bundle.git /tmp/geoflow-bundle && \
    cd /tmp/geoflow-bundle && \
    sed -i 's/# add_subdirectory(plugins\/gfp-las)/add_subdirectory(plugins\/gfp-las)/' CMakeLists.txt && \
    sed -i 's/# add_subdirectory(plugins\/gfp-val3dity)/add_subdirectory(plugins\/gfp-val3dity)/' CMakeLists.txt && \
    sed -i 's/.*cmake_minimum_required.*/cmake_minimum_required(VERSION 3.5)/' plugins/gfp-val3dity/thirdparty/val3dity/CMakeLists.txt && \
    mkdir build && cd build && \
    cmake .. \
        -DGF_BUILD_GUI=OFF \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_PREFIX_PATH="/opt/conda;/usr/local" \
        -DCMAKE_SHARED_LINKER_FLAGS="-L/opt/conda/lib -L/usr/local/lib" \
        -DCMAKE_EXE_LINKER_FLAGS="-L/opt/conda/lib -L/usr/local/lib" && \
    make -j$(nproc) && \
    make install && \
    cd / && rm -rf /tmp/geoflow-bundle

# Install remaining Python dependencies
COPY requirements.txt .

# Remove binary deps that we already installed via Conda to prevent pip from recompiling/breaking them
RUN sed -i '/GDAL/d' requirements.txt && \
    sed -i '/rasterio/d' requirements.txt && \
    sed -i '/fiona/d' requirements.txt && \
    sed -i '/pyproj/d' requirements.txt && \
    sed -i '/shapely/d' requirements.txt && \
    sed -i '/numpy/d' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Copy Project Code
COPY . .

# Set entrypoint
ENTRYPOINT ["python", "cli.py"]
CMD ["--help"]
