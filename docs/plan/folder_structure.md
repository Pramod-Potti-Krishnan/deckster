# Project Folder Structure

## Overview
Simple, intuitive folder organization for the presentation generator project.

```
deckster.xyz-ver-4/
│
├── 📁 .claude/                   # claude commands folder
|    └── 📁 commands/             # Claude commands stored as .md files in this folder
│
├── 📁 examples/                   # Any examples or reference files stored here
|
├── 📁 docs/                   # All documentation
│   ├── 📁 plan/               # All planing documentation               
│   |   ├── 📄 README.md           # Project overview & getting started
│   |   ├── 📄 PRD_Phase1.md       # Phase 1 requirements
│   |   ├── 📄 PRD_Phase2.md       # Phase 2 requirements
│   |   ├── 📄 PRD_Phase3.md       # Phase 3 requirements
│   |   ├── 📄 PRD_Phase4.md       # Phase 4 requirements
│   |   ├── 📄 comms_protocol.md   # Communication templates
│   |   ├── 📄 tech_stack.md       # Technology guide
│   |   └── 📄 security.md         # Security requirements
│   ├── 📁 PRPs/                   # Product Requirement Prompts               
│   |   ├── 📁 templates/          # PRP templates folder 
|   |   |    └──📄 prp_base.md     # PRP base template document
│   |   └── 📄 phase1-websocket-director-api.md/  # PRP for phase 1 of development  
|   └── 📁 Learnings/              # Folder to document learnings in the future      
|      
├── 📁 src/                     # Source code
│   ├── 📁 agents/             # AI agents
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py         # Base agent class
│   │   ├── 📄 director_in.py  # Director (Inbound)
│   │   ├── 📄 director_out.py # Director (Outbound)
│   │   ├── 📄 ux_architect.py # Layout specialist
│   │   ├── 📄 researcher.py   # Content researcher
│   │   ├── 📄 visual_designer.py # Image creator
│   │   ├── 📄 data_analyst.py # Chart creator
│   │   └── 📄 ux_analyst.py   # Diagram creator
│   │
│   ├── 📁 api/                # API endpoints
│   │   ├── 📄 __init__.py
│   │   ├── 📄 websocket.py    # WebSocket handlers
│   │   ├── 📄 routes.py       # REST endpoints
│   │   └── 📄 middleware.py   # Auth & security
│   │
│   ├── 📁 models/             # Data models
│   │   ├── 📄 __init__.py
│   │   ├── 📄 messages.py     # Communication models
│   │   ├── 📄 presentation.py # Presentation structure
│   │   └── 📄 agents.py       # Agent-specific models
│   │
│   ├── 📁 workflows/          # LangGraph workflows
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main.py         # Main generation flow
│   │   └── 📄 iteration.py    # Feedback flow
│   │
│   ├── 📁 storage/            # Database & storage
│   │   ├── 📄 __init__.py
│   │   ├── 📄 supabase.py     # Database operations
│   │   └── 📄 redis_cache.py  # Caching layer
│   │
│   └── 📁 utils/              # Utilities
│       ├── 📄 __init__.py
│       ├── 📄 auth.py         # JWT authentication
│       ├── 📄 validators.py   # Input validation
│       └── 📄 logger.py       # Logging setup
│
├── 📁 tests/                   # All tests
│   ├── 📁 unit/              # Unit tests
│   ├── 📁 integration/       # Integration tests
│   └── 📄 conftest.py        # Test configuration
│
├── 📁 config/                  # Configuration
│   ├── 📄 settings.py        # App settings
│   └── 📁 prompts/           # Agent prompts
│       ├── 📄 director.txt
│       ├── 📄 researcher.txt
│       └── 📄 designer.txt
│
├── 📁 scripts/                 # Utility scripts
│   ├── 📄 setup_db.py        # Database setup
│   └── 📄 generate_keys.py   # Key generation
│
├── 📄 .env.example            # Environment template
├── 📄 requirements.txt        # Python dependencies
├── 📄 docker-compose.yml      # Docker setup
├── 📄 Dockerfile              # Container definition
└── 📄 .gitignore             # Git ignore rules
```

## Key Principles

### 1. Flat is Better Than Nested
- Maximum 3 levels deep
- Each folder has a clear, single purpose
- Easy to navigate and find files

### 2. Clear Naming
- **Descriptive names**: `director_in.py` not `di.py`
- **Consistent style**: Use underscores for Python files
- **No abbreviations**: `presentation.py` not `pres.py`

### 3. Logical Grouping
- **By function**: All agents together, all API code together
- **Not by phase**: Don't create phase1/, phase2/ folders
- **Keep related files close**: Models near the code that uses them

### 4. Documentation First
- All docs in one place (`docs/`)
- README at the root explains everything
- Each folder can have its own README if needed

## Quick Start Files

### Root README.md
```markdown
# Presentation Generator

AI-powered presentation generation system.

## Quick Start
1. Clone the repo
2. Copy `.env.example` to `.env`
3. Run `docker-compose up`
4. Open http://localhost:8000

## Documentation
- [Phase 1 Requirements](docs/PRD_Phase1.md)
- [Communication Protocol](docs/comms_protocol.md)
- [Technology Stack](docs/tech_stack.md)
- [Security](docs/security.md)

## Development
See [docs/](docs/) for detailed documentation.
```

### .env.example
```bash
# Core
JWT_SECRET_KEY=generate-random-key-here
SUPABASE_URL=your-project-url
SUPABASE_ANON_KEY=your-anon-key

# AI Services
OPENAI_API_KEY=your-key

# Redis
REDIS_URL=redis://localhost:6379

# Environment
NODE_ENV=development
```

## Development Workflow

### 1. Starting a New Feature
```bash
# 1. Create feature branch
git checkout -b feature/agent-name

# 2. Add agent file
touch src/agents/new_agent.py

# 3. Add tests
touch tests/unit/test_new_agent.py

# 4. Update models if needed
# edit src/models/agents.py
```

### 2. Running the Project
```bash
# Development
python -m uvicorn src.api.websocket:app --reload

# Tests
pytest tests/

# Docker
docker-compose up
```

## File Size Guidelines

- **Keep files under 700 lines**
- If a file grows too large, split by functionality:
  ```
  # Instead of one large director.py:
  agents/
  ├── director/
  │   ├── __init__.py      # Main Director class
  │   ├── clarifications.py # Question logic
  │   ├── structure.py     # Structure building
  │   └── utils.py         # Helper functions
  ```

## What Goes Where?

| What | Where | Example |
|------|-------|---------|
| New agent | `src/agents/` | `src/agents/translator.py` |
| API endpoint | `src/api/routes.py` | Add new route function |
| Data model | `src/models/` | `src/models/messages.py` |
| Database query | `src/storage/` | `src/storage/supabase.py` |
| Shared utility | `src/utils/` | `src/utils/validators.py` |
| Configuration | `config/` | `config/settings.py` |
| Documentation | `docs/` | `docs/new_feature.md` |
| Tests | `tests/` | `tests/unit/test_feature.py` |

## Common Operations

### Adding a New Agent
1. Create agent file: `src/agents/my_agent.py`
2. Define agent class inheriting from `BaseAgent`
3. Add agent to workflow: `src/workflows/main.py`
4. Create tests: `tests/unit/test_my_agent.py`

### Adding an API Endpoint
1. Add route to: `src/api/routes.py`
2. Add request/response models: `src/models/messages.py`
3. Add validation: `src/utils/validators.py`
4. Add tests: `tests/integration/test_api.py`

### Modifying Communication Protocol
1. Update models: `src/models/messages.py`
2. Update docs: `docs/comms_protocol.md`
3. Update affected agents
4. Run all tests

## Benefits of This Structure

✅ **Easy to Navigate** - Know exactly where to find things  
✅ **Easy to Scale** - Add new agents/features without restructuring  
✅ **Easy to Test** - Clear separation of concerns  
✅ **Easy to Deploy** - Docker-friendly structure  
✅ **Easy to Understand** - New developers can jump in quickly  

## Remember

- **Don't overthink it** - Simple is better
- **Be consistent** - Follow the patterns
- **Document changes** - Update README when adding major features
- **Keep it clean** - Delete unused files