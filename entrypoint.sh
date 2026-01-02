#!/bin/bash
set -e

# If the first argument is "api" or empty/starts with "-", start API
if [ "$1" = "api" ] || [ -z "$1" ] || [[ "$1" == -* ]]; then
    echo "Starting Web API..."
    # Configured for Cloud Run which sets $PORT
    exec uvicorn src.cloud.api:app --host 0.0.0.0 --port ${PORT:-8080}
else
    # Otherwise, run as CLI
    echo "Running CLI command..."
    exec python cli.py "$@"
fi
