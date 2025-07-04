#!/bin/bash
# Run the application with minimal dependencies

echo "🚀 Starting Phase 1 with Minimal Dependencies"
echo "============================================"

# Activate virtual environment
source venv/Scripts/activate

# Set environment variables for testing
export PYTHONPATH="${PYTHONPATH}:${PWD}"
export APP_ENV=development
export DEBUG=true

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your credentials"
    exit 1
fi

# Run compatibility check
echo -e "\nChecking package compatibility..."
python -c "
from src.utils.compat import check_requirements
check_requirements()
"

echo -e "\nStarting the application..."
echo "Note: Some features may be limited due to missing packages"
echo ""

# Start the server
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000