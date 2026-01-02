@echo off
setlocal

REM Define image name
set IMAGE_NAME=dream3d-cli:latest

REM Get current directory
set CURRENT_DIR=%CD%

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Starting DREAM3DCITY processing in Docker...
echo Mounting directory: %CURRENT_DIR%

REM Run the container with current directory mounted to /app
REM We use the correct entry point found: cli.py
docker run --rm -v "%CURRENT_DIR%:/app" -w /app %IMAGE_NAME% %*

if %errorlevel% neq 0 (
    echo Processing failed.
    pause
    exit /b 1
)

echo Processing completed successfully.
pause
