# CLAUDE.md - Deckster.xyz Development Guide

## Project Overview

Deckster.xyz is an AI-powered presentation generation platform that leverages a multi-agent architecture to intelligently create compelling and visually appealing presentations based on user inputs. The system streamlines the presentation creation process from initial concept to final output by automating content research, data analysis, visual design, and layout.

## Key Architecture Components

### Multi-Agent System
The platform uses specialized AI agents orchestrated by a Director agent:

1. **Director (Inbound)** - Primary user interface, requirement gathering, and orchestration
2. **Director (Outbound)** - Assembles outputs, quality validation, and user delivery
3. **UX Architect** - Theme design and slide layout structure
4. **Researcher** - Content generation and information gathering
5. **Data Analyst** - Chart creation and data visualization
6. **Visual Designer** - Image, GIF, icon, and video generation
7. **UX Analyst** - Diagram creation and visual representation of concepts

### Technology Stack

#### Core Framework
- **Pydantic BaseModel** - Data validation and standardization for all agent outputs
- **Pydantic AI** - Agent development framework with multi-LLM support
- **LangGraph** - Agent orchestration and workflow management
- **FastAPI** - High-performance API and WebSocket communication
- **MCP (Model Context Protocol)** - Pre-built tool integration

#### Storage & Data
- **PostgreSQL with pgvector** - Main database with vector similarity search
- **Supabase** - Managed PostgreSQL instance with auth and storage
- **Redis** - In-memory cache and real-time pub/sub communication

#### Communication
- **WebSocket** - Real-time bidirectional communication
- **JSON** - Primary protocol with HTML-embedded visual content
- **JWT** - Authentication and session management

#### Deployment & Monitoring
- **Railway** - Cloud deployment platform
- **Pydantic LogFire** - Structured logging and observability
- **Python 3.11.9** - Runtime environment (3.13 support in progress)

## Project Structure

```
deckster/
├── config/                 # Configuration files
│   ├── settings.py        # Main settings
│   └── prompts/           # Agent prompts
├── src/                   # Source code
│   ├── agents/           # AI agents
│   │   ├── base.py      # Base agent class
│   │   └── director_in.py # Director Inbound agent
│   ├── api/              # API layer
│   │   ├── main.py      # FastAPI app
│   │   ├── middleware.py # CORS and auth
│   │   └── websocket.py # WebSocket handlers
│   ├── models/          # Pydantic models
│   │   ├── agents.py    # Agent-related models
│   │   ├── messages.py  # Communication models
│   │   └── presentation.py # Presentation structures
│   ├── storage/         # Data storage
│   │   ├── redis_cache.py # Redis operations
│   │   └── supabase.py  # Database operations
│   ├── utils/           # Utilities
│   │   ├── auth.py      # JWT authentication
│   │   ├── logger.py    # Logging setup
│   │   └── validators.py # Input validation
│   └── workflows/       # LangGraph workflows
├── docs/                # Documentation
├── tests/              # Test suites
└── presentation-generator/ # Frontend service

```

## Current Development Status

### Phase 1 Implementation (As of 2025-07-04)
- ✅ WebSocket API with JWT authentication implemented
- ✅ Director (Inbound) agent with Pydantic AI integration
- ✅ Basic message handling and session management
- ✅ Railway deployment configured and live
- ✅ CORS configuration with multiple origin support
- ✅ Successfully completed Round 11.1 urgent fixes (July 4, 2025)
- 🔧 Backend stable, frontend completing WebSocket state management fixes

### Deployment Progress
- **Rounds 1-9**: Progressive fixes for CORS, environment variables, and JSON parsing
- **Round 10**: Frontend WebSocket authentication integration issues ✅ RESOLVED
- **Round 11**: LangGraph StateGraph initialization errors ✅ RESOLVED  
- **Round 11.1**: Supabase RLS policy violations and session creation ✅ RESOLVED

### Remaining Frontend Work
1. **Frontend WebSocket State Management**
   - Frontend needs to fix infinite "WebSocket client not initialized" loop
   - Implement proper connection state management as detailed in Round 11 docs
   - Backend is fully operational and ready for frontend connections

### Important Environment Notes
- **CORS_ORIGINS** is intentionally NOT an environment variable (removed in Round 9)
- All CORS origins are hardcoded in application for reliability
- "NOT SET" messages in logs are expected behavior

### Known Limitations
- Python 3.13 compatibility (using 3.11.9 for stability)
- Windows installation complexity
- Production uses `/api/auth/demo` endpoint (available in all environments)

## Development Guidelines

### Code Organization
- **Maximum file size**: 1000 lines (hard limit)
- **Recommended file size**: 700 lines or less
- **Refactoring**: Split files approaching 700 lines into logical modules

### File Patterns
```python
# Module-level docstring (required)
"""
Module description and purpose.

Key functionality:
- Feature 1
- Feature 2
"""

# Comprehensive class documentation
class AgentName(BaseAgent):
    """
    Agent purpose and responsibilities.
    
    Attributes:
        attr1: Description
        attr2: Description
    """
    
    # Method documentation with examples
    async def method_name(self, param: Type) -> ReturnType:
        """
        Method description.
        
        Args:
            param: Parameter description
            
        Returns:
            Return value description
            
        Raises:
            ExceptionType: When this happens
        """
```

### API Communication Patterns

#### WebSocket Message Format
```python
{
    "id": "unique-message-id",
    "type": "message_type",  # request, response, error, etc.
    "timestamp": "2024-01-01T00:00:00Z",
    "session_id": "session-uuid",
    "data": {
        # Message-specific payload
    }
}
```

#### Message Types
- `new_presentation` - Start new presentation
- `clarification` - Director asks questions
- `answer` - User provides answers
- `structure` - Initial presentation structure
- `progress` - Processing updates
- `error` - Error notifications

### Environment Variables

#### Required for Development
```bash
# App Settings
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Security
JWT_SECRET_KEY=dev-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Redis
REDIS_URL=redis://localhost:6379

# AI Services
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...  # Optional fallback

# Logging
LOGFIRE_TOKEN=your-token
```

#### Railway Deployment
- Add all above variables to Railway dashboard
- `PORT` is auto-set by Railway
- Use `production` for `APP_ENV`

### Testing Strategy

#### Unit Tests
```bash
pytest tests/unit -v
```

#### Integration Tests
```bash
pytest tests/integration -v --asyncio-mode=auto
```

#### WebSocket Testing
```python
# Example WebSocket test client
import asyncio
import websockets
import json

async def test_websocket():
    # Get auth token
    token = await get_dev_token()
    
    # Connect to WebSocket
    uri = f"ws://localhost:8000/ws?token={token}"
    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "type": "new_presentation",
            "data": {"topic": "AI Technology"}
        }))
        
        # Receive response
        response = await websocket.recv()
        print(json.loads(response))
```

## Quick Start Commands

### Deployment Status Check
```bash
# Check backend health
curl https://deckster-production.up.railway.app/health

# Test token endpoint (development mode only)
curl -X POST https://deckster-production.up.railway.app/api/dev/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'

# Test WebSocket connection (in browser console)
# See Troubleshooting section for complete test script
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn src.api.main:app --reload --port 8000

# Run with debug logging
python main_debug.py
```

### Testing
```bash
# Health check
curl http://localhost:8000/health

# Get dev token
curl -X POST http://localhost:8000/api/dev/token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'

# WebSocket test (with wscat)
wscat -c "ws://localhost:8000/ws?token=YOUR_TOKEN"
```

### Deployment
```bash
# Deploy to Railway
git push origin main

# View logs
railway logs

# Check deployment
curl https://your-app.railway.app/health
```

## Best Practices

### Agent Development
1. Use Pydantic models for all data structures
2. Implement comprehensive error handling
3. Log all LLM interactions with LogFire
4. Use type hints consistently
5. Document complex logic with inline comments

### API Development
1. Validate all inputs with Pydantic
2. Use proper HTTP status codes
3. Include request IDs for tracing
4. Implement rate limiting for production
5. Handle WebSocket disconnections gracefully

### Security
1. Never commit secrets to git
2. Use environment variables for sensitive data
3. Implement proper JWT validation
4. Sanitize user inputs
5. Use HTTPS in production

## Troubleshooting

### Common Issues

1. **WebSocket Connection Rejected (1008)**
   - Ensure JWT token is included in connection URL
   - Check token validity and expiration
   - Frontend must acquire token BEFORE connecting:
   ```javascript
   // Get token first
   const tokenRes = await fetch('https://deckster-production.up.railway.app/api/dev/token', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ user_id: 'test_user' })
   });
   const { access_token } = await tokenRes.json();
   // Then connect with token
   const ws = new WebSocket(`wss://deckster-production.up.railway.app/ws?token=${access_token}`);
   ```

2. **CORS Errors**
   - Verify frontend URL in CORS configuration
   - Check Railway environment variables
   - Railway format: `CORS_ORIGINS=https://www.deckster.xyz,https://deckster.xyz,https://*.vercel.app`
   - Known issue: Railway may add semicolons - backend cleans these automatically

3. **Import Errors**
   - Run `python check_all_imports.py` to diagnose
   - Ensure all dependencies are in requirements.txt
   - Logfire package may not load in Railway - falls back to standard logging

4. **Railway Deployment Fails**
   - Check Python version (use 3.11.9)
   - Verify all environment variables are set
   - Review deployment logs for specific errors
   - Current deployment is Round 10 of progressive fixes

5. **Frontend "No authentication token available" Error**
   - Frontend is trying to connect without getting a token first
   - Must call `/api/dev/token` endpoint before WebSocket connection
   - See `/docs/frontend-comms/frontend-integration-guide.md` for complete flow

## Important Files Reference

- `/docs/plan/PRD_v4.0.md` - Complete product requirements
- `/docs/plan/tech_stack.md` - Detailed technology documentation
- `/docs/plan/PRD_Phase1.md` - Current phase implementation
- `/docs/frontend-comms/frontend-integration-guide.md` - Frontend integration
- `/RAILWAY_DEPLOYMENT.md` - Deployment instructions
- `/tests/phase1_test_SOP.md` - Testing procedures

## Contact & Support

For questions or issues:
1. Check existing documentation in `/docs`
2. Review test files for usage examples
3. Check deployment logs for runtime issues
4. Consult the PRD documents for product decisions