# Base image: Python 3.11 (Official Debian-based slim image)
# Menggunakan versi 3.11 sesuai request user
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install System Dependencies & Go
# Kita perlu:
# 1. curl/wget untuk download Go
# 2. git untuk go get (opsional)
# 3. library C++ standar jika geof membutuhkannya
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

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
# Note: Menghapus PyQt5 dari requirements untuk versi headless/cloud agar lebih ringan
# atau kita gunakan teknik sed untuk menghapusnya sementara saat build
RUN sed -i '/PyQt5/d' requirements.txt && \
    sed -i '/pyvistaqt/d' requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# --- INSTALL GEOFLOW (Assuming 'geof' binary needs to be present) ---
# Jika 'geof' adalah binary pre-compiled Linux, kita copy ke /usr/local/bin
# Jika 'geof' tidak ada di repo (user punya lokal), user harus menyediakannya di folder ini.
# UNTUK SAAT INI: Saya asumsikan user akan menaruh binary 'geof' linux di root project
# COPY geof /usr/local/bin/geof
# RUN chmod +x /usr/local/bin/geof
# (Saya comment dulu karena saya tidak melihat binary 'geof' di list file awal, 
#  tapi user menyebutkan geoflow. User nanti perlu memastikan binary ini ada).

# Copy Source Code
COPY . .

# Build Go modules (jika ada go.mod, kalau tidak ada, go run akan handle on-the-fly, 
# tapi sebaiknya di-build dulu untuk efisiensi)
# Karena file .go ada di folder go/, kita tidak perlu build binary tunggal dulu 
# jika script python memanggil 'go run'. 
# TAPI, best practicenya adalah compile 'go run' menjadi binary.
# Namun agar tidak merubah logic Python yang memanggil 'go run', kita biarkan dulu.
# Kita hanya pastikan environment go siap.

# Create 'output' directory for temp processing
RUN mkdir -p output

# Expose port (untuk API nanti)
EXPOSE 8080

# Command default: Jalankan API Web Service
CMD ["uvicorn", "src.cloud.api:app", "--host", "0.0.0.0", "--port", "8080"]
