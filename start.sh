#!/bin/bash
# Start script for Railway deployment

# Set Python path to include the app directory
export PYTHONPATH=/app:$PYTHONPATH

# Set default port if not provided
PORT=${PORT:-8000}

echo "Starting Deckster API on port $PORT..."
echo "Python path: $PYTHONPATH"
echo "Environment: ${APP_ENV:-production}"

# Start the application
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --workers 1