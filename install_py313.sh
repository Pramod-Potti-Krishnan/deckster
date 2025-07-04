#!/bin/bash
# Installation script for Python 3.13 on Windows

echo "🚀 Python 3.13 Installation Script"
echo "=================================="
echo ""

# Check Python version
python --version
echo ""

# Clean up
echo "Cleaning previous attempts..."
pip cache purge

# Upgrade pip first
echo "Upgrading pip to latest version..."
python -m pip install --upgrade pip setuptools wheel

# Try the safe requirements first
echo -e "\nInstalling safe requirements..."
pip install -r requirements-py313-safe.txt

# Check if core packages installed
echo -e "\nVerifying core installations..."
python -c "
import sys
print('Testing core imports...')
try:
    import fastapi
    print('✅ FastAPI:', fastapi.__version__)
except ImportError as e:
    print('❌ FastAPI:', e)

try:
    import pydantic
    print('✅ Pydantic:', pydantic.__version__)
except ImportError as e:
    print('❌ Pydantic:', e)

try:
    import uvicorn
    print('✅ Uvicorn: installed')
except ImportError as e:
    print('❌ Uvicorn:', e)
"

# Try optional packages one by one
echo -e "\nAttempting optional packages..."

# Pydantic AI
echo "Installing pydantic-ai..."
pip install pydantic-ai==0.0.13 || echo "⚠️  pydantic-ai failed"

# LangChain packages
echo "Installing langchain packages..."
pip install langchain==0.3.18 || echo "⚠️  langchain failed"
pip install langgraph==0.2.61 || echo "⚠️  langgraph failed"
pip install langchain-openai==0.2.18 || echo "⚠️  langchain-openai failed"
pip install langchain-anthropic==0.3.7 || echo "⚠️  langchain-anthropic failed"

# AsyncPG
echo "Installing asyncpg..."
pip install asyncpg==0.30.0 || echo "⚠️  asyncpg failed"

# NumPy
echo "Installing numpy..."
pip install numpy==2.2.2 || echo "⚠️  numpy failed"

# Tiktoken
echo "Installing tiktoken..."
pip install tiktoken==0.8.0 || echo "⚠️  tiktoken failed"

# LogFire
echo "Installing logfire..."
pip install logfire==2.14.0 || echo "⚠️  logfire failed"

# Development tools
echo "Installing development tools..."
pip install ruff==0.9.2 || echo "⚠️  ruff failed"
pip install mypy==1.14.2 || echo "⚠️  mypy failed"

echo -e "\n✅ Installation complete!"
echo ""
echo "Running full test..."
python test_imports.py