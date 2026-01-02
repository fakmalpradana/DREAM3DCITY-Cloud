# DREAM3DCITY Deployment & Usage Documentation

This document enables you to deploy the **DREAM3DCITY** 3D reconstruction and conversion engine to Google Cloud Platform (GCP).

---

## 1. Technology Stack

This application utilizes a modern, cloud-native stack designed for high-performance geospatial processing:

*   **Language**: Python 3.10 (API & Orchestration)
*   **Web Framework**: FastAPI with Uvicorn (Asynchronous Server)
*   **Containerization**: Docker (Multi-stage build)
*   **3D Processing Engine**:
    *   **Geoflow**: C++ based engine for 3D city reconstruction (compiled from source).
    *   **LAStools**: Efficient LiDAR processing.
    *   **Val3dity**: Geometry validation tools.
*   **CLI Tools**: Go (Golang) compiled binaries for `obj2gml` conversion.
*   **Cloud Platform (GCP)**:
    *   **Cloud Run**: Serverless container execution (Auto-scaling).
    *   **Cloud Build**: CI/CD for building Docker images.
    *   **Artifact Registry**: Secure Docker image storage.
    *   **Cloud Storage**: Object storage for input/output data.

---

## 2. Prerequisites

Before starting, ensure you have:

1.  **Google Cloud Platform Account**: Active account with billing enabled.
2.  **Google Cloud SDK**: Installed and authenticated (`gcloud auth login`).
3.  **Project ID**: A created GCP project (e.g., `dream3d-482717`).

---

## 3. Deployment Steps

We have provided automated scripts for both Windows and Linux/Cloud Shell users.

### Step 1: Configure Environment
Create a file named `.env` in the project root with your details:

```ini
PROJECT_ID=your-project-id-here
REGION=asia-southeast2
BUCKET_NAME=dream3d-data-storage
```

### Step 2: Run Deployment Script

**For Windows (PowerShell):**
```powershell
.\deploy_gcp.ps1
```

**For Linux / Google Cloud Shell:**
```bash
chmod +x deploy_gcp.sh
./deploy_gcp.sh
```

**What the script does:**
1.  Enables required Google Cloud APIs.
2.  Checks/Creates a **Cloud Storage Bucket** for data.
3.  Checks/Creates an **Artifact Registry** repository.
4.  Builds the Docker image using **Cloud Build**.
5.  Deploys the service to **Cloud Run** (Public access, 2 vCPU, 4GB RAM).
    *   **Bucket**: Connects it to your specified Cloud Storage bucket.

---

## 4. CI/CD Setup (Automated Deployment)

To automate deployment (so changes deploy when you `git push`), follow these steps:

### Step 1: Push to Git
Push your code (including the new `cloudbuild.yaml` file) to a repository (GitHub, Bitbucket, or Cloud Source Repositories).

### Step 2: Create Build Trigger in GCP
1.  Go to the **Google Cloud Console** -> **Cloud Build** -> **Triggers**.
2.  Click **Create Trigger**.
3.  **Source**: Select your repository and branch (e.g., `main`).
4.  **Configuration**: Select **Cloud Build configuration file (yaml/json)**.
5.  **Location**: Ensure it points to `cloudbuild.yaml`.
6.  **Substitutions** (Optional): If you want to override defaults without changing the code, add variables like `_REGION` or `_BUCKET_NAME` here.
7.  Click **Create**.

Now, every time you push to your selected branch, Cloud Build will automatically:
1.  Build the new Docker image.
2.  Push it to Artifact Registry.
3.  Deploy the new version to Cloud Run.

### Note on Secrets (`.env`)
It is **correct and safe** to add `.env` to `.gitignore`. Cloud Build **does not** read your local `.env` file. Instead, it uses the variables defined in `cloudbuild.yaml`.

If you need to change these values for the automated build (e.g., different bucket name), do not edit the file. Instead, set them in the **Trigger Settings** under **Substitution variables** (e.g., `_BUCKET_NAME` = `my-prod-bucket`).

---

## 5. API Usage Guide

Once deployed, you will receive a **Service URL** (e.g., `https://dream3d-service-xyz.a.run.app`).

### A. Interactive Documentation (Swagger UI)
Visit `[YOUR_SERVICE_URL]/docs` to see the interactive API test page.

### B. Endpoints

#### 1. Reconstruct 3D Model (`POST /reconstruct`)
Converts 2D Footprints + LiDAR Point Cloud into a 3D Model.

*   **Input**: A ZIP file containing:
    *   1 Footprint file (`.gpkg` or `.shp`)
    *   1 Pointcloud file (`.las` or `.laz`)
*   **Returns**: `job_id`

#### 2. Convert OBJ to GML (`POST /obj2gml`)
Converts standard 3D OBJ files into CityGML format.

*   **Input**: A ZIP file containing your OBJ files and metadata.
*   **Returns**: `job_id`

#### 3. Check Status (`GET /jobs/{job_id}`)
Poll this endpoint to check progress.

*   **Status**: `QUEUED` -> `PROCESSING` -> `COMPLETED` (or `FAILED`)
*   **Result**: When `COMPLETED`, returns a `download_url` to your files.

---

## 5. Troubleshooting

*   **"Bucket does not exist"**: Re-run the deployment script to ensure the bucket creation step executes.
*   **"Processing hangs"**: Ensure the `--no-cpu-throttling` flag was used during deployment (the provided scripts include this).
*   **"Multiple files found"**: Ensure your ZIP file contains exactly one footprint and one pointcloud file. Hidden system files are now automatically ignored.
