# Deployment & Usage Guide for DREAM3DCITY

This guide explains how to deploy the DREAM3DCITY API to Google Cloud Run and how to use it once deployed.

## 1. The Deployment Script (`deploy_gcp.ps1`)

The `deploy_gcp.ps1` script is an automated PowerShell tool designed to simplify the deployment process on Windows. Here is what it does, step-by-step:

1.  **Load Configuration**: It reads your credentials (`PROJECT_ID`, `REGION`, `BUCKET_NAME`) from the `.env` file.
2.  **Enable APIs**: It activates necessary Google Cloud services (Cloud Run, Artifact Registry, Cloud Build, Cloud Storage).
3.  **Setup Repository**: It checks if the Docker repository (`dream3d-repo`) exists in Artifact Registry. If not, it creates it.
4.  **Build & Push**: It zips your local source code and sends it to **Google Cloud Build**. The Docker image is built in the cloud (saving your local bandwidth/CPU) and stored in Artifact Registry.
5.  **Deploy Service**: It deploys the Docker image to **Cloud Run**. It configures the service with:
    *   **Public Access**: (`--allow-unauthenticated`) so you can access it easily.
    *   **Resources**: 2 CPUs and 4GB RAM to handle 3D processing.
    *   **Timeout**: 60 minutes (3600s) to allow for long-running jobs.
    *   **Bucket**: Connects it to your specified Cloud Storage bucket.

## 2. Usage Guide (Post-Deployment)

Once the script completes, it will output a **Service URL** (e.g., `https://dream3d-service-xyz.a.run.app`).

### A. Accessing the Interface (Swagger UI)

The easiest way to test the API is via the interactive documentation.
1.  Open your browser.
2.  Navigate to: `[YOUR_SERVICE_URL]/docs`
3.  You will see the **Swagger UI** where you can manually upload files and test endpoints.

### B. API Endpoints

The API is asynchronous. You submit a job, get an ID, and check its status later.

#### 1. Submit Reconstruction Job
**Endpoint**: `POST /reconstruct`
**Input**: A **ZIP file** containing:
*   1 Building Footprint file (`.gpkg` or `.shp` + sidecars)
*   1 Point Cloud file (`.las` or `.laz`)

**Response**:
```json
{
  "job_id": "uuid-string",
  "status": "QUEUED",
  "message": "Job queued for processing"
}
```

#### 2. Submit OBJ2GML Job
**Endpoint**: `POST /obj2gml`
**Input**: A **ZIP file** containing your OBJ files and metadata folder structure.
**Response**: Similar to reconstruction (Job ID).

#### 3. Check Job Status
**Endpoint**: `GET /jobs/{job_id}`
**Response**:
```json
{
  "job_id": "uuid-string",
  "status": "COMPLETED",  // or PROCESSING, FAILED
  "message": "Process finished successfully.",
  "download_url": "https://storage.googleapis.com/..." // Valid for 1 hour
}
```

### C. Example Workflow (cURL)

**1. Submit Job**
```bash
curl -X POST "https://your-service-url/reconstruct" \
     -F "file=@./my_data.zip"
# Returns: {"job_id": "12345..."}
```

**2. Poll Status**
```bash
curl "https://your-service-url/jobs/12345..."
# Returns: {"status": "PROCESSING", ...}
```

**3. Download Result**
Once status is `COMPLETED`, open the `download_url` in your browser to get the processed ZIP file.
