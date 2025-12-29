# Rencana Anggaran (Budget Plan) - Google Cloud Platform

Estimasi ini dibuat dengan asumsi penggunaan **"On-Demand"** (Serverless), dimana Anda hanya membayar saat aplikasi memproses data.

## 1. Komponen Biaya Utama

### A. Compute (Google Cloud Run)
Cloud Run menagih berdasarkan vCPU dan Memory per detik saat container berjalan.
*Asumsi: Setiap Job 3D Reconstruction memakan waktu rata-rata 10 menit (600 detik).*
*Spek mesin: 2 vCPU + 4GB RAM.*

- **Biaya per detik (Tier 1)**:
  - vCPU: ~$0.00002400 / vCPU-detik
  - Memory: ~$0.00000250 / GB-detik
- **Biaya per Job (10 menit)**:
  - vCPU: 2 * 600 * $0.00002400 = $0.0288
  - RAM: 4 * 600 * $0.00000250 = $0.0060
  - **Total per Job: ~$0.035 (Sekitar Rp 550 per job).**

*Jika dalam sebulan ada 100 job:* **$3.50 (Rp 55.000)**.
*Free Tier:* Cloud Run memberikan 180,000 vCPU-seconds gratis per bulan. Jadi untuk 100 job pertama mungkin **GRATIS**.

### B. Storage (Google Cloud Storage)
Untuk menyimpan file input (LAS/SHP) dan output (GML/CityJSON).

- **Standard Storage**: $0.020 per GB / bulan.
- **Operations (Class A - Upload/List)**: $0.05 per 10,000 operasi.
- **Operations (Class B - Download)**: $0.004 per 10,000 operasi.

*Skenario Auto-Delete 24 Jam:*
Data tidak menumpuk. Jika rata-rata data harian 10GB.
- Biaya Storage: 10GB * $0.02 = **$0.20 per bulan (Rp 3.000)**.

### C. Container Registry (Artifact Registry)
Untuk menyimpan Docker Image.
- Storage: $0.10 per GB / bulan.
- Image size container Python+Go mungkin sekitar 500MB - 1GB.
- **Biaya: ~$0.10 per bulan (Rp 1.500)**.

---

## 2. Total Estimasi Bulanan

| Komponen | Penggunaan Rendah (50 Job/bln) | Penggunaan Sedang (500 Job/bln) |
| :--- | :--- | :--- |
| **Cloud Run** | $0 (Masuk Free Tier) | ~$17.50 |
| **Cloud Storage** | ~$0.10 | ~$1.00 |
| **Artifact Registry**| ~$0.10 | ~$0.10 |
| **TOTAL** | **~$0.20 (Rp 3.000)** | **~$18.60 (Rp 300.000)** |

*Catatan: Harga belum termasuk PPN 11% di Indonesia.*

---

## 3. Strategi Penghematan (Lifecycle Policy)

Agar biaya storage tidak bengkak, kita **WAJIB** memasang **Lifecycle Rule** pada Bucket GCS:
1.  **Rule**: "Delete object"
2.  **Condition**: "Age > 1 day"

Dengan ini, file input user dan hasil output akan otomatis dihapus oleh Google setiap hari. User harus mendownload hasilnya dalam waktu 24 jam.
