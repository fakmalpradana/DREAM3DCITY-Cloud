import os
import shutil
import logging
import zipfile
import uuid
import asyncio
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google.cloud import storage

from src.core.reconstruction import ReconstructionManager
from src.core.obj2gml import Obj2GMLManager

# --- Configuration ---
app = FastAPI(
    title="DREAM3DCITY Cloud API",
    description="API for 3D City Reconstruction and OBJ to GML Conversion",
    version="1.0.0"
)

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dream3d_api")

# GCP Bucket Name (Environment Variable)
BUCKET_NAME = os.getenv("GCP_BUCKET_NAME", "dream3d-data-bucket") # Fallback for local test

# Temporary Local Storage
TEMP_DIR = "/tmp/dream3d_processing"
os.makedirs(TEMP_DIR, exist_ok=True)

# In-Memory Job Store (For demo purposes; use Firestore for production)
jobs_db = {} 

class JobStatus(BaseModel):
    job_id: str
    status: str # QUEUED, PROCESSING, COMPLETED, FAILED
    message: str
    download_url: Optional[str] = None

# --- Helper Functions ---

def get_gcs_client():
    return storage.Client()

def smart_detect_files(extract_dir: str, mode: str):
    """
    Intelligently finds required files in a directory based on extensions.
    mode: 'reconstruct' or 'obj2gml'
    """
    found_files = {
        "footprint": None,
        "pointcloud": None,
        "obj_dir": None
    }
    
    if mode == 'reconstruct':
        for root, dirs, files in os.walk(extract_dir):
            # Skip hidden directories like __MACOSX
            dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('__')]
            
            for f in files:
                if f.startswith('.'): continue # Skip hidden files like ._test.gpkg

                if f.lower().endswith(('.gpkg', '.shp')):
                    if found_files["footprint"]:
                         print(f"Warning: Multiple footprints found. Keeping {found_files['footprint']}, ignoring {f}")
                         continue
                    found_files["footprint"] = os.path.join(root, f)
                elif f.lower().endswith(('.las', '.laz')):
                    if found_files["pointcloud"]:
                         print(f"Warning: Multiple point clouds found. Keeping {found_files['pointcloud']}, ignoring {f}")
                         continue
                    found_files["pointcloud"] = os.path.join(root, f)
        
        if not found_files["footprint"]:
            raise Exception("No footprint file (.gpkg/.shp) found in ZIP.")
        if not found_files["pointcloud"]:
            raise Exception("No point cloud file (.las/.laz) found in ZIP.")
            
        return found_files

    elif mode == 'obj2gml':
        # For obj2gml, we just need the directory that contains the data.
        # We assume the user zipped a folder.
        return {"obj_dir": extract_dir} 

def upload_folder_to_gcs(local_folder: str, destination_blob_prefix: str):
    """Uploads a folder to GCS (as a ZIP if needed for single link, or individual files).
    For simplicity, we zip the output folder and upload one ZIP file."""
    
    shutil.make_archive(local_folder, 'zip', local_folder)
    zip_path = local_folder + ".zip"
    
    storage_client = get_gcs_client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_prefix)
    
    blob.upload_from_filename(zip_path)
    
    # Use Public URL (Requires bucket to be public)
    # This is a quick fix to avoid managing Service Account Keys for signing
    return blob.public_url

# --- Background Processor ---

def process_reconstruction_job(job_id: str, zip_path: str):
    work_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(work_dir, exist_ok=True)
    extract_dir = os.path.join(work_dir, "input")
    output_dir = os.path.join(work_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    try:
        jobs_db[job_id]["status"] = "PROCESSING"
        jobs_db[job_id]["message"] = "Extracting input files..."

        # 1. Unzip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # 2. Smart Detect
        jobs_db[job_id]["message"] = "Detecting input files..."
        files = smart_detect_files(extract_dir, 'reconstruct')
        
        # 3. Run Reconstruction
        jobs_db[job_id]["message"] = "Running 3D Reconstruction..."
        manager = ReconstructionManager()
        # Default advanced params for now
        success = manager.run_reconstruction(
            files["footprint"], 
            files["pointcloud"], 
            output_dir
        )

        if success:
            # 4. Upload Result
            jobs_db[job_id]["message"] = "Uploading results..."
            download_url = upload_folder_to_gcs(output_dir, f"outputs/{job_id}.zip")
            
            jobs_db[job_id]["status"] = "COMPLETED"
            jobs_db[job_id]["message"] = "Process finished successfully."
            jobs_db[job_id]["download_url"] = download_url
        else:
            jobs_db[job_id]["status"] = "FAILED"
            jobs_db[job_id]["message"] = "Reconstruction process failed internally."

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        jobs_db[job_id]["status"] = "FAILED"
        jobs_db[job_id]["message"] = str(e)

    finally:
        # Cleanup
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        if os.path.exists(zip_path):
            os.remove(zip_path)

def process_obj2gml_job(job_id: str, zip_path: str):
    work_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(work_dir, exist_ok=True)
    extract_dir = os.path.join(work_dir, "input")
    # obj2gml modifies files in-place or creates subfolders.
    # We will treat extract_dir as the input_dir.

    try:
        jobs_db[job_id]["status"] = "PROCESSING"
        jobs_db[job_id]["message"] = "Extracting input files..."

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        jobs_db[job_id]["message"] = "Running OBJ to GML Conversion..."
        manager = Obj2GMLManager()
        success = manager.run_conversion(extract_dir)

        if success:
            jobs_db[job_id]["message"] = "Uploading results..."
            # The tool puts output in the same dir structure usually.
            # We zip the entire extract_dir.
            download_url = upload_folder_to_gcs(extract_dir, f"outputs/{job_id}.zip")
            
            jobs_db[job_id]["status"] = "COMPLETED"
            jobs_db[job_id]["message"] = "Process finished successfully."
            jobs_db[job_id]["download_url"] = download_url
        else:
            jobs_db[job_id]["status"] = "FAILED"
            jobs_db[job_id]["message"] = "Conversion process failed."

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        jobs_db[job_id]["status"] = "FAILED"
        jobs_db[job_id]["message"] = str(e)
    
    finally:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        if os.path.exists(zip_path):
            os.remove(zip_path)

# --- API Endpoints ---

@app.post("/reconstruct", response_model=JobStatus, status_code=202)
async def create_reconstruction_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a ZIP file containing:
    - 1 Building Footprint (.gpkg or .shp)
    - 1 Point Cloud (.las or .laz)
    """
    job_id = str(uuid.uuid4())
    zip_path = os.path.join(TEMP_DIR, f"{job_id}.zip")
    
    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not save uploaded file")

    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "QUEUED",
        "message": "Job queued for processing",
        "download_url": None
    }

    background_tasks.add_task(process_reconstruction_job, job_id, zip_path)

    return jobs_db[job_id]

@app.post("/obj2gml", response_model=JobStatus, status_code=202)
async def create_obj2gml_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a ZIP file containing existing OBJ files and metadata to convert to GML.
    """
    job_id = str(uuid.uuid4())
    zip_path = os.path.join(TEMP_DIR, f"{job_id}.zip")
    
    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not save uploaded file")

    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "QUEUED",
        "message": "Job queued for processing",
        "download_url": None
    }

    background_tasks.add_task(process_obj2gml_job, job_id, zip_path)

    return jobs_db[job_id]

@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_db[job_id]

@app.get("/health")
async def health_check():
    return {"status": "ok"}
