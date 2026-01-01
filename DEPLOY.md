# Deployment Guide for DREAM3DCITY

This guide explains how to deploy the DREAM3DCITY API to Google Cloud Run.

## Prerequisites

1.  **Google Cloud CLI (gcloud)** installed and authenticated.
2.  **Docker** installed (optional if using Cloud Build, but recommended for local testing).
3.  A **Google Cloud Project** with billing enabled.

## 1. Setup Environment

Open your terminal (PowerShell or Bash) and login to verify:

```bash
gcloud auth login
gcloud config set project [YOUR_PROJECT_ID]
```

## 2. Deploy using Script

We have provided a script `deploy_gcp.sh` (or `deploy_gcp.ps1` equivalent instructions) to automate the process.

**Run the script:**

```bash
# Usage: ./deploy_gcp.sh [PROJECT_ID] [REGION]
./deploy_gcp.sh my-dream3d-project asia-southeast2
```

**What the script does:**
1.  Enables necessary Google Cloud APIs (Cloud Run, Artifact Registry, Cloud Build).
2.  Creates a Docker repository in Artifact Registry (if not exists).
3.  Builds the Docker image using Cloud Build (so you don't need to upload the huge image manually).
4.  Deploys the image to Cloud Run.

## 3. Manual Deployment Steps

If you prefer to run commands manually:

```bash
# Variables
export PROJECT_ID="your-project-id"
export REGION="asia-southeast2"
export REPO="dream3d-repo"
export IMAGE="dream3d-api"

# 1. Create Repository
gcloud artifacts repositories create $REPO --repository-format=docker --location=$REGION

# 2. Build & Push (Cloud Build)
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE:latest"

# 3. Deploy
gcloud run deploy dream3d-service \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE:latest" \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2
```

## 4. Testing the Production API

Once deployed, you will get a URL (e.g., `https://dream3d-service-xyz.a.run.app`).

- **API Docs**: Visit `https://dream3d-service-xyz.a.run.app/docs` to see the Swagger UI.
- **Reconstruct**: Use the `/reconstruct` endpoint (Note: Processing large files via HTTP might timeout; for production, consider using Cloud Storage triggers).
