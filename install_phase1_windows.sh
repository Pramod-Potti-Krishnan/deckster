#!/bin/bash
# install_phase1_windows.sh - Installation script for Windows (Git Bash/MinGW)

echo "🚀 Phase 1 Installation for Windows"
echo "==================================="

# Check if we're in the right directory
if [ ! -f "requirements-phase1.txt" ]; then
    echo "❌ Error: requirements-phase1.txt not found!"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment (Windows path)
echo "🔧 Activating virtual environment..."
source venv/Scripts/activate

# Upgrade pip to latest version
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

# Install packages in groups to isolate any issues
echo -e "\n📦 Installing core framework packages..."
pip install fastapi uvicorn websockets

echo -e "\n📦 Installing Pydantic packages..."
pip install pydantic pydantic-settings

echo -e "\n📦 Installing database packages..."
pip install supabase redis asyncpg pgvector

echo -e "\n📦 Installing authentication packages..."
pip install python-jose[cryptography] passlib[bcrypt] python-multipart slowapi

echo -e "\n📦 Installing AI/ML packages..."
pip install openai anthropic numpy

echo -e "\n📦 Installing utility packages..."
pip install python-dotenv httpx aiofiles

echo -e "\n📦 Installing testing packages..."
pip install pytest pytest-asyncio pytest-cov

echo -e "\n📦 Installing LangChain packages..."
pip install langchain langgraph langchain-openai langchain-anthropic || echo "⚠️  Some LangChain packages failed, continuing..."

echo -e "\n📦 Installing optional packages..."
pip install logfire || echo "⚠️  LogFire failed, continuing without it"

echo -e "\n✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and fill in your credentials"
echo "2. Run: python scripts/setup_db.py"
echo "3. Run: python -m uvicorn src.api.main:app --reload"
echo ""
echo "To verify installation:"
echo "  python -c \"import fastapi; print('FastAPI version:', fastapi.__version__)\""