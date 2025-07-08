#!/bin/bash
# Start script for Railway deployment

# Railway provides PORT as an environment variable
# Default to 8000 if not set (for local development)
PORT=${PORT:-8000}

echo "Starting Deckster on port $PORT..."
python -m uvicorn main:app --host 0.0.0.0 --port $PORT