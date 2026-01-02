# Cloud Platform Setup Guide (Google Cloud)

Panduan langkah demi langkah untuk men-setup environment Google Cloud Platform (GCP) untuk DREAM3DCITY.

## Persiapan Lokal
Pastikan Anda sudah menginstall:
1.  **Google Cloud SDK** (`gcloud` CLI).
2.  **Docker Desktop**.

## Langkah 1: Setup Proyek GCP

1.  Buka [Google Cloud Console](https://console.cloud.google.com/).
2.  Buat **New Project** (misal: `dream3d-cloud`).
3.  Pastikan **Billing Account** sudah terhubung (perlu Kartu Kredit/Debit Jenius dll).

## Langkah 2: Aktifkan API

Jalankan perintah ini di terminal (atau via Console "APIs & Services"):

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage-component.googleapis.com
```

## Langkah 3: Buat Cloud Storage (Bucket)

Kita butuh "Folder" di cloud untuk terima file upload.

1.  Buka menu **Cloud Storage** > **Buckets**.
2.  Klik **Create**. Nama: `dream3d-data-[unik]`.
3.  **Region**: Pilih lokasi terdekat (misal `asia-southeast2` Jakarta).
4.  **Lifecycle Rule (PENTING)**:
    - Klik tab "Lifecycle".
    - "Add a rule".
    - Select action: **Delete object**.
    - Select condition: **Age** is **1 day**.
    - *Ini menjawab kebutuhan Anda agar file otomatis terhapus setelah 24 jam.*

## Langkah 4: Container Registry

Tempat parkir Docker Image.

```bash
gcloud artifacts repositories create dream3d-repo \
    --repository-format=docker \
    --location=asia-southeast2 \
    --description="DREAM3DCITY Docker Repository"
```

## Langkah 5: Deployment (Deploy ke Cloud Run)

Ini adalah proses mengubah code di laptop menjadi service online.

### 5.1 Build Image
Di terminal folder `DREAM3DCITY`:

```bash
# Ganti PROJECT_ID dengan ID project GCP Anda
gcloud builds submit --tag asia-southeast2-docker.pkg.dev/PROJECT_ID/dream3d-repo/dream3d-api:v1
```

*Note: Proses ini akan mengompres folder, upload, dan Google akan menjalankan perintah `docker build` di cloud.*

### 5.2 Deploy Service
Setelah build sukses:

```bash
gcloud run deploy dream3d-service \
    --image asia-southeast2-docker.pkg.dev/PROJECT_ID/dream3d-repo/dream3d-api:v1 \
    --platform managed \
    --region asia-southeast2 \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2
```

- `--memory 4Gi`: Penting untuk pemrosesan 3D.
- `--allow-unauthenticated`: Agar API bisa diakses publik (development). Untuk produksi, matikan ini dan gunakan Token.

---

## Spesifikasi API Lanjutan

Untuk menjawab pertanyaan teknis Anda:

### 1. Menangani "Banyak File Input" (Multi-file)
Untuk endpoints `/reconstruct` dan `/obj2gml` yang butuh banyak file:
- **Solusi**: Client (Frontend) harus men-**ZIP** file-file tersebut terlebih dahulu menjadi satu file `input.zip`.
- **Alur**:
  1. Upload `input.zip` ke Cloud Storage.
  2. Kirim path GCS `gs://bucket/input.zip` ke API.
  3. API akan mendownload dan `unzip` di dalam container sebelum memproses.

#### 1.1 Logika Deteksi File Otomatis (Smart Detection)
Agar program tidak bingung membedakan input (karena ada banyak file dalam ZIP), sistem akan menggunakan **Deteksi Ekstensi**:

- **Untuk Reconstruct**:
  - Sistem men-scan folder hasil unzip.
  - File dengan akhiran `.gpkg` atau `.shp` $\rightarrow$ Dianggap sebagai **Footprint**.
  - File dengan akhiran `.las` atau `.laz` $\rightarrow$ Dianggap sebagai **Point Cloud**.
  - *Validasi*: Jika sistem menemukan lebih dari 1 file sejenis (misal ada 2 file `.las`), sistem akan menolak dan meminta user memisahkan input.

- **Untuk Obj2GML**:
  - Sistem men-scan seluruh file `.obj`, `.txt`, dan `.geojson` dalam folder.
  - Semua file tersebut akan diproses sesuai hirarki folder yang ada dalam ZIP.

**Response JSON Structure:**
```json
{
  "job_id": "12345",
  "status": "RUNNING",    // "QUEUED", "RUNNING", "COMPLETED", "FAILED"
  "progress": 45,         // Integer 0-100 (Untuk Loading Bar)
  "current_step": "Step 3/6: MTL generation",
  "logs": [               // List string log history
    "[10:00:01] Job started",
    "[10:00:05] Building separation done",
    "[10:00:15] Object translation..."
  ],
  "download_url": null    // Akan berisi Signed URL jika status COMPLETED
}
```

### 3. Skenario Download
Jika status `COMPLETED`:
- Server meng-generate **Signed URL** (link download sementara yang valid misal 1 jam) yang mengarah ke output file ZIP di Cloud Storage.
- User klik link tersebut untuk download.

---

## Next Action
Jika Anda setuju dengan Setup ini, langkah coding selanjutnya adalah:
1. Membuat `api.py` (FastAPI) yang mengimplementasikan spec di atas.
2. Mengubah `src/core/obj2gml.py` dkk agar bisa membaca file dari ZIP dan menulis Log ke memori/database (bukan cuma `print`).
