# Phase 1 Testing Standard Operating Procedure (SOP)

## Overview
This document provides comprehensive instructions for testing the Phase 1 implementation of the AI-powered presentation generation system. Since the code was developed in a WSL environment, this SOP guides you through setting up, running, and validating all tests.

## Prerequisites

### 1. Environment Setup
```bash
# Navigate to project directory
cd presentation-generator

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the project root with the following:
```env
# App Settings
APP_ENV=testing
DEBUG=true
LOG_LEVEL=DEBUG

# Security
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# LLM Configuration
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key  # Optional fallback

# Pydantic AI Settings
PYDANTIC_AI_LOG_LEVEL=INFO
PYDANTIC_AI_MAX_RETRIES=3

# LogFire Configuration (Optional)
LOGFIRE_TOKEN=your-logfire-token

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_WEBSOCKET_MESSAGES_PER_MINUTE=120

# Testing
TESTING=true
```

### 3. Database Setup
```bash
# Ensure PostgreSQL is running with pgvector extension
# Run the database setup script
python scripts/setup_db.py

# Verify tables were created by checking Supabase dashboard
```

### 4. Redis Setup
```bash
# Start Redis server (if not running)
redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

## Running Tests

### 1. Run All Tests
```bash
# Run all tests with coverage
pytest -v --cov=src --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

### 2. Run Unit Tests Only
```bash
# Run unit tests
pytest tests/unit/ -v -m unit

# Run specific test file
pytest tests/unit/test_models.py -v

# Run specific test class
pytest tests/unit/test_models.py::TestMessageModels -v
```

### 3. Run Integration Tests
```bash
# Run integration tests
pytest tests/integration/ -v -m integration

# Run WebSocket tests specifically
pytest tests/integration/test_websocket.py -v
```

### 4. Run Tests with Different Verbosity
```bash
# Minimal output
pytest -q

# Verbose output
pytest -vv

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

## Test Validation Checklist

### Unit Tests (tests/unit/test_models.py)

#### Message Models
- [ ] ✓ UserInput validates text length (max 5000 chars)
- [ ] ✓ DirectorMessage requires either slide_data or chat_data
- [ ] ✓ ClarificationQuestion validates question types
- [ ] ✓ ClarificationRound tracks round numbers correctly
- [ ] ✓ SlideContent validates slide_id format

#### Presentation Models
- [ ] ✓ Slide component limits per layout type
- [ ] ✓ Component position bounds (0-100)
- [ ] ✓ Text component content limits
- [ ] ✓ Presentation slide numbering is sequential
- [ ] ✓ Color palette hex validation

#### Agent Models
- [ ] ✓ RequirementAnalysis score validation (0-1)
- [ ] ✓ DirectorInboundOutput includes all required fields
- [ ] ✓ AgentOutput includes timestamp

### Integration Tests (tests/integration/test_websocket.py)

#### WebSocket Connection
- [ ] ✓ Connection fails without authentication
- [ ] ✓ Authentication via headers (document expected behavior)
- [ ] ✓ Authentication via query parameters
- [ ] ✓ Authentication via first message

#### Message Handling
- [ ] ✓ User input messages are processed
- [ ] ✓ Clarification flow works correctly
- [ ] ✓ Frontend action messages are handled
- [ ] ✓ Invalid messages return errors

#### Workflow Tests
- [ ] ✓ Complete presentation generation flow
- [ ] ✓ Clarification workflow with multiple rounds
- [ ] ✓ Error recovery and handling

#### Performance Tests
- [ ] ✓ Concurrent connection handling
- [ ] ✓ Message ordering is preserved
- [ ] ✓ Large message handling (within limits)

## Manual Testing

### 1. Start the Application
```bash
# Start the FastAPI server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Server should start at http://localhost:8000
```

### 2. Check Health Endpoints
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed
```

### 3. Test WebSocket Connection
Use a WebSocket client (like Postman or wscat):

```bash
# Install wscat if needed
npm install -g wscat

# Connect with token in query
wscat -c "ws://localhost:8000/ws?token=YOUR_JWT_TOKEN"

# Send a test message
{"type": "user_input", "session_id": "test_123", "data": {"text": "Create a presentation about AI"}}
```

### 4. Test Authentication
```bash
# Get a test token (implement a test endpoint or use the utility)
python -c "from src.utils.auth import create_test_token; print(create_test_token('test_user'))"

# Use the token in requests
```

## Common Issues and Solutions

### 1. Import Errors
**Issue**: `ModuleNotFoundError: No module named 'src'`
**Solution**: 
```bash
# Ensure you're in the project root
cd presentation-generator
# Add project to Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

### 2. Database Connection Errors
**Issue**: Cannot connect to Supabase
**Solution**: 
- Verify `.env` file has correct credentials
- Check Supabase project is active
- Ensure pgvector extension is enabled

### 3. Redis Connection Errors
**Issue**: `ConnectionRefusedError` for Redis
**Solution**:
```bash
# Start Redis
redis-server
# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

### 4. Test Fixtures Not Working
**Issue**: Mock fixtures not being applied
**Solution**:
- Ensure test function parameters match fixture names
- Check fixture scope (session vs function)
- Verify monkeypatch is applied correctly

## Performance Testing

### 1. Load Testing WebSocket
```python
# Create a simple load test script
import asyncio
import websockets
import json
import time

async def test_client(client_id):
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Send auth token
        await websocket.send(json.dumps({"token": "YOUR_TOKEN"}))
        
        # Send test message
        message = {
            "type": "user_input",
            "session_id": f"test_{client_id}",
            "data": {"text": f"Test message from client {client_id}"}
        }
        await websocket.send(json.dumps(message))
        
        # Wait for response
        response = await websocket.recv()
        print(f"Client {client_id}: {response}")

# Run multiple clients
async def load_test(num_clients=10):
    tasks = [test_client(i) for i in range(num_clients)]
    await asyncio.gather(*tasks)

# Execute: asyncio.run(load_test(50))
```

### 2. Memory Profiling
```bash
# Install memory profiler
pip install memory-profiler

# Run with memory profiling
mprof run pytest tests/
mprof plot
```

## Test Report Generation

### 1. Generate HTML Report
```bash
# Run tests with HTML report
pytest --html=report.html --self-contained-html

# Open report.html in browser
```

### 2. Generate JUnit XML (for CI/CD)
```bash
# Generate JUnit format report
pytest --junitxml=report.xml
```

### 3. Coverage Report
```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Check coverage thresholds
pytest --cov=src --cov-fail-under=80
```

## Continuous Integration Setup

### GitHub Actions Configuration
Create `.github/workflows/test.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        env:
          TESTING: true
          JWT_SECRET_KEY: test-key
        run: |
          pytest -v --cov=src
```

## Final Validation Steps

1. **All Tests Pass**: Ensure 100% of tests pass
2. **Coverage > 80%**: Aim for at least 80% code coverage
3. **No Linting Errors**: Run `ruff check src/`
4. **Type Checking**: Run `mypy src/` (if configured)
5. **Security Check**: Run `bandit -r src/`
6. **Documentation**: Verify all docstrings are present

## Debugging Tips

### 1. Enable Debug Logging
```python
# In tests, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Use pytest debugger
```bash
# Drop into debugger on failure
pytest --pdb

# Set breakpoint in code
import pdb; pdb.set_trace()
```

### 3. Print WebSocket Messages
```python
# In WebSocket handler, add:
logger.debug(f"Received: {message}")
logger.debug(f"Sending: {response}")
```

## Summary

This SOP provides comprehensive testing instructions for Phase 1. Follow these steps sequentially:

1. Set up environment and dependencies
2. Configure environment variables
3. Initialize database and Redis
4. Run unit tests
5. Run integration tests
6. Perform manual testing
7. Generate coverage reports
8. Address any failures

Remember to document any issues encountered and their solutions for future reference.

## Contact

For questions or issues with this testing procedure, please refer to:
- Project documentation in `/docs`
- GitHub issues for known problems
- Team communication channels