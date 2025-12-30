#!/bin/bash

# Dream3D City GCP Deployment Script
# Usage: ./deploy_gcp.sh [PROJECT_ID] [REGION]

PROJECT_ID=$1
REGION=${2:-asia-southeast2}
REPO_NAME="dream3d-repo"
IMAGE_NAME="dream3d-api"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./deploy_gcp.sh [PROJECT_ID] [REGION]"
    echo "Please provide your Google Cloud Project ID."
    exit 1
fi

echo "=================================================="
echo "DEPLOYING DREAM3DCITY TO GOOGLE CLOUD"
echo "Project: $PROJECT_ID"
echo "Region : $REGION"
echo "=================================================="

# 1. Enable APIs (Just in case)
echo "[1/4] Enabling required APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com storage-component.googleapis.com --project "$PROJECT_ID"

# 2. Check/Create Artifact Registry
echo "[2/4] Checking Artifact Registry..."
if ! gcloud artifacts repositories describe $REPO_NAME --location="$REGION" --project="$PROJECT_ID" > /dev/null 2>&1; then
    echo "Creating repository '$REPO_NAME'..."
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location="$REGION" \
        --description="DREAM3DCITY Docker Repository" \
        --project="$PROJECT_ID"
else
    echo "Repository '$REPO_NAME' already exists."
fi

# 3. Build & Push Image
IMAGE_TAG="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:latest"
echo "[3/4] Building and Pushing Docker Image to: $IMAGE_TAG"
gcloud builds submit --tag "$IMAGE_TAG" --project "$PROJECT_ID"

# 4. Deploy to Cloud Run
SERVICE_NAME="dream3d-service"
echo "[4/4] Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image "$IMAGE_TAG" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --project "$PROJECT_ID" \
    --set-env-vars GCP_BUCKET_NAME="dream3d-data-$PROJECT_ID" # Assumption: Bucket created manually or follows pattern

echo "=================================================="
echo "DEPLOYMENT COMPLETE!"
echo "Service URL:"
gcloud run services describe $SERVICE_NAME --platform managed --region "$REGION" --project "$PROJECT_ID" --format 'value(status.url)'
echo ""
echo "API Documentation: [Service URL]/docs"
echo "=================================================="
