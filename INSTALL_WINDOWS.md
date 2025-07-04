# Windows Installation Guide for Phase 1

This guide is specifically for Windows users using Git Bash or Command Prompt.

## Prerequisites

1. **Python 3.10 or 3.11** (3.12+ may have compatibility issues)
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **Git Bash** (recommended) or Command Prompt
   - Download from [git-scm.com](https://git-scm.com/download/win)

## Step-by-Step Installation

### 1. Open Terminal

Open Git Bash and navigate to the project directory:
```bash
cd "/c/Users/pramo/OneDrive/Documents/Vibe Deck/deckster.xyz-ver-4"
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it (Git Bash)
source venv/Scripts/activate

# Or for Command Prompt:
# venv\Scripts\activate.bat
```

You should see `(venv)` in your prompt.

### 3. Upgrade pip

```bash
python -m pip install --upgrade pip setuptools wheel
```

### 4. Install Phase 1 Requirements

We have a special requirements file without problematic packages:

```bash
# Install from the Windows-compatible requirements
pip install -r requirements-phase1.txt
```

If you get errors, install packages in groups:

```bash
# Core packages
pip install fastapi uvicorn websockets pydantic pydantic-settings

# Database packages
pip install supabase redis asyncpg pgvector

# Auth packages
pip install python-jose[cryptography] passlib[bcrypt] python-multipart slowapi

# AI packages
pip install openai anthropic numpy

# Utilities
pip install python-dotenv httpx aiofiles

# Testing
pip install pytest pytest-asyncio pytest-cov

# LangChain (may have issues)
pip install langchain langgraph langchain-openai langchain-anthropic pydantic-ai
```

### 5. Verify Installation

Run the test script:
```bash
python test_imports.py
```

You should see mostly green checkmarks. Some optional packages (tiktoken, logfire) may show warnings - this is fine.

### 6. Set Up Environment Variables

Create `.env` file:
```bash
# Copy the example
cp .env.example .env

# Or create new one
touch .env
```

Edit `.env` with your credentials:
```env
# Mandatory
JWT_SECRET_KEY=your-secret-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
REDIS_URL=redis://default:password@redis-host.com:port
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional
OPENAI_API_KEY=sk-...
```

### 7. Run Database Setup

```bash
python scripts/setup_db.py
```

### 8. Start the Application

```bash
# Development server with auto-reload
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Troubleshooting

### "Module not found" errors
- Make sure virtual environment is activated: `source venv/Scripts/activate`
- Check Python version: `python --version` (use 3.10 or 3.11)

### Redis connection errors
- Use Redis Cloud instead of local Redis
- Check your REDIS_URL includes password and port

### Package installation fails
- Upgrade pip: `python -m pip install --upgrade pip`
- Install problematic packages separately
- Use `--no-cache-dir` flag: `pip install --no-cache-dir package-name`

### Git Bash path issues
- Use forward slashes: `/c/Users/...` not `C:\Users\...`
- Quote paths with spaces: `cd "/c/Program Files/..."`

## Quick Commands Reference

```bash
# Activate virtual environment
source venv/Scripts/activate

# Install dependencies
pip install -r requirements-phase1.txt

# Run tests
python test_imports.py

# Start server
python -m uvicorn src.api.main:app --reload

# Deactivate virtual environment
deactivate
```

## Next Steps

1. Test the API health endpoint: `http://localhost:8000/health`
2. Check API documentation: `http://localhost:8000/docs`
3. Test WebSocket connection with the test script
4. Begin frontend integration

## Notes

- **tiktoken** is excluded (requires Rust compiler) - the app uses approximate token counting instead
- **logfire** is optional - standard logging is used if not available
- Some development tools (ruff, mypy) are excluded to avoid compilation issues
- Use Redis Cloud instead of local Redis for easier setup