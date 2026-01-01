# Dream3D City GCP Deployment Script (PowerShell)

# 1. Load Environment Variables from .env
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^\s*([^#=]+)\s*=\s*(.*)") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
} else {
    Write-Host "Error: .env file not found. Please create one with PROJECT_ID and REGION." -ForegroundColor Red
    exit 1
}

$PROJECT_ID = $env:PROJECT_ID
$REGION = $env:REGION
$REPO_NAME = if ($env:REPO_NAME) { $env:REPO_NAME } else { "dream3d-repo" }
$SERVICE_NAME = if ($env:SERVICE_NAME) { $env:SERVICE_NAME } else { "dream3d-service" }
$IMAGE_NAME = "dream3d-api"

if (-not $PROJECT_ID) {
    Write-Host "Error: PROJECT_ID not set in .env file." -ForegroundColor Red
    exit 1
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "DEPLOYING DREAM3DCITY TO GOOGLE CLOUD" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Region : $REGION"
Write-Host "Repo   : $REPO_NAME"
Write-Host "Service: $SERVICE_NAME"
Write-Host "==================================================" -ForegroundColor Cyan

# 2. Enable APIs
Write-Host "[1/4] Enabling required APIs..." -ForegroundColor Yellow
cmd /c "gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com storage-component.googleapis.com --project $PROJECT_ID"

# 3. Check/Create Artifact Registry
Write-Host "[2/4] Checking Artifact Registry..." -ForegroundColor Yellow
$repoExists = cmd /c "gcloud artifacts repositories describe $REPO_NAME --location=$REGION --project=$PROJECT_ID 2>&1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating repository '$REPO_NAME'..."
    cmd /c "gcloud artifacts repositories create $REPO_NAME --repository-format=docker --location=$REGION --description='DREAM3DCITY Docker Repository' --project=$PROJECT_ID"
} else {
    Write-Host "Repository '$REPO_NAME' already exists."
}

# 4. Build & Push Image
$IMAGE_TAG = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME`:@latest"
$IMAGE_TAG_PURE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME`:latest"

Write-Host "[3/4] Building and Pushing Docker Image to: $IMAGE_TAG_PURE" -ForegroundColor Yellow
# Note: PowerShell parsing of specific chars in gcloud args can be tricky, using cmd /c for robust gcloud execution
cmd /c "gcloud builds submit --tag $IMAGE_TAG_PURE --project $PROJECT_ID"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Build failed." -ForegroundColor Red
    exit 1
}

# 5. Deploy to Cloud Run
Write-Host "[4/4] Deploying to Cloud Run..." -ForegroundColor Yellow
# Note: For long running jobs, Cloud Run Jobs is better, but user asked for Service-like deployment in script.
# We will use 'gcloud run deploy' as requested.
# Increase timeout to max (60m) for heavy processing if needed.

$BUCKET_NAME = if ($env:BUCKET_NAME) { $env:BUCKET_NAME } else { "dream3d-data-$PROJECT_ID" }

cmd /c "gcloud run deploy $SERVICE_NAME --image $IMAGE_TAG_PURE --platform managed --region $REGION --allow-unauthenticated --memory 4Gi --cpu 2 --timeout=3600 --project $PROJECT_ID --set-env-vars GCP_BUCKET_NAME=$BUCKET_NAME"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Deployment failed." -ForegroundColor Red
    exit 1
}

Write-Host "==================================================" -ForegroundColor Green
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
$SERVICE_URL = cmd /c "gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --project $PROJECT_ID --format 'value(status.url)'"
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor White
Write-Host ""
Write-Host "API Documentation: $SERVICE_URL/docs"
Write-Host "==================================================" -ForegroundColor Green
