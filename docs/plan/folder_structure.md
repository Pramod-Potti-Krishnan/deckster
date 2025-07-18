# Project Folder Structure

## Overview
Current folder organization for the Deckster presentation generator project (Phase 1).

```
deckster/
│
├── 📁 .claude/                      # Claude AI configuration
│   ├── 📁 commands/                 # Claude command files (.md)
│   │   ├── 📄 README.md
│   │   ├── 📄 build-agent-architecture.md
│   │   ├── 📄 deploy-fixes.md
│   │   ├── 📄 execute-prp.md
│   │   └── 📄 generate-prp.md
│   └── 📄 settings.local.json       # Local Claude settings
│
├── 📁 .railway/                     # Railway deployment configuration
│   └── 📄 railway.toml             # Railway config file
│
├── 📁 config/                       # Application configuration
│   ├── 📄 __init__.py
│   ├── 📁 prompts/                  # Agent prompts
│   │   └── 📁 modular/              # Modular prompt system
│   │       ├── 📄 README.md         # Prompt system documentation
│   │       ├── 📄 base_prompt.md    # Base prompt template
│   │       ├── 📄 provide_greeting.md
│   │       ├── 📄 ask_clarifying_questions.md
│   │       ├── 📄 create_confirmation_plan.md
│   │       ├── 📄 generate_strawman.md
│   │       └── 📄 refine_strawman.md
│   └── 📄 settings.py              # Application settings
│
├── 📁 docs/                         # Documentation
│   ├── 📁 PRPs/                     # Product Requirement Prompts
│   │   ├── 📄 phase1-websocket-director-api.md
│   │   └── 📁 templates/
│   │       └── 📄 prp_base.md
│   ├── 📁 architecture/             # Architecture documentation
│   │   └── 📄 phase1-architecture.md
│   ├── 📁 archive/                  # Archived/historical docs
│   │   ├── 📁 context_memory/      # Memory management research
│   │   └── (various archived docs)
│   ├── 📁 clean_documents/          # Clean, current documentation
│   │   ├── 📄 Context_and_Memory_Management.md
│   │   ├── 📄 Frontend_Integration_Guide.md
│   │   ├── 📄 Modular_Prompt_Architecture.md
│   │   ├── 📄 WebSocket_Communication_Protocol.md
│   │   └── (other clean docs)
│   ├── 📁 learnings/               # Learning documentation
│   │   └── 📄 Environment_Phase_1_Configure.md
│   ├── 📁 plan/                    # Planning documents
│   │   ├── 📄 PRD_Phase1.md       # Phase 1 requirements
│   │   ├── 📄 PRD_Phase2.md       # Phase 2 requirements
│   │   ├── 📄 PRD_Phase3.md       # Phase 3 requirements
│   │   ├── 📄 PRD_Phase4.md       # Phase 4 requirements
│   │   ├── 📄 folder_structure.md  # This document
│   │   └── 📄 tech_stack.md       # Technology stack
│   └── 📄 example-product-concept.md
│
├── 📁 examples/                     # Example files
│   └── 📄 .gitkeep
│
├── 📁 migrations/                   # Database migrations
│   ├── 📄 add_user_id_simple.sql
│   └── 📄 add_user_id_to_sessions.sql
│
├── 📁 scripts/                      # Utility scripts
│   ├── 📄 setup_database.sql      # Database setup SQL
│   └── 📄 setup_db.py            # Database setup script
│
├── 📁 src/                         # Source code
│   ├── 📄 __init__.py
│   ├── 📁 agents/                  # AI agents
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py             # Base agent class
│   │   ├── 📄 director.py         # Director agent (main)
│   │   └── 📄 intent_router.py    # Intent classification
│   │
│   ├── 📁 handlers/                # Request handlers
│   │   ├── 📄 __init__.py
│   │   └── 📄 websocket.py        # WebSocket handler
│   │
│   ├── 📁 models/                  # Data models
│   │   ├── 📄 __init__.py
│   │   ├── 📄 agents.py           # Agent-specific models
│   │   ├── 📄 session.py          # Session management
│   │   └── 📄 websocket_messages.py # WebSocket protocol
│   │
│   ├── 📁 storage/                 # Database & storage
│   │   ├── 📄 __init__.py
│   │   └── 📄 supabase.py         # Supabase integration
│   │
│   ├── 📁 utils/                   # Utilities
│   │   ├── 📄 __init__.py
│   │   ├── 📄 ab_testing.py       # A/B testing utilities
│   │   ├── 📄 asset_formatter.py  # Asset formatting
│   │   ├── 📄 auth.py             # Authentication
│   │   ├── 📄 compat.py           # Compatibility layer
│   │   ├── 📄 context_builder.py  # Context management
│   │   ├── 📄 logfire_config.py   # Logfire setup
│   │   ├── 📄 logger.py           # Logging setup
│   │   ├── 📄 message_adapter.py  # Message adaptation
│   │   ├── 📄 message_packager.py # Legacy packager
│   │   ├── 📄 prompt_manager.py   # Prompt management
│   │   ├── 📄 session_manager.py  # Session handling
│   │   ├── 📄 streamlined_packager.py # Streamlined protocol
│   │   ├── 📄 token_tracker.py    # Token usage tracking
│   │   └── 📄 validators.py       # Input validation
│   │
│   └── 📁 workflows/               # Workflow definitions
│       ├── 📄 __init__.py
│       └── 📄 state_machine.py    # State management
│
├── 📁 test/                        # Test files
│   ├── 📄 README.md               # Test documentation
│   ├── 📄 test_director_e2e.py    # End-to-end tests
│   ├── 📄 test_modular_prompts.py # Prompt tests
│   ├── 📄 test_scenarios.json     # Test scenarios
│   ├── 📄 test_token_tracking.py  # Token tracking tests
│   └── 📄 test_utils.py           # Test utilities
│
├── 📄 .env.example                 # Environment template
├── 📄 .gitignore                   # Git ignore rules
├── 📄 check_supabase_schema.py     # Schema verification
├── 📄 debug_modular_prompts.py     # Prompt debugging
├── 📄 main.py                      # Application entry point
├── 📄 Procfile                     # Heroku/deployment
├── 📄 railway.json                 # Railway configuration
├── 📄 README.md                    # Project README
├── 📄 requirements.txt             # Python dependencies
├── 📄 setup_env.py                 # Environment setup
├── 📄 start.sh                     # Startup script
└── 📄 test_supabase_connection.py  # Connection testing
```

## Key Principles

### 1. Flat is Better Than Nested
- Maximum 3 levels deep
- Each folder has a clear, single purpose
- Easy to navigate and find files

### 2. Clear Naming
- **Descriptive names**: `intent_router.py` not `ir.py`
- **Consistent style**: Use underscores for Python files
- **No abbreviations**: `websocket_messages.py` not `ws_msgs.py`

### 3. Logical Grouping
- **By function**: All agents together, all handlers together
- **Not by phase**: Don't create phase1/, phase2/ folders
- **Keep related files close**: Models near the code that uses them

### 4. Documentation First
- All docs in one place (`docs/`)
- README at the root explains everything
- Organized subdirectories for different doc types

## Quick Start Files

### Root README.md
```markdown
# Deckster - AI Presentation Generator

AI-powered presentation generation system with WebSocket API.

## Quick Start
1. Clone the repo
2. Copy `.env.example` to `.env`
3. Run `pip install -r requirements.txt`
4. Run `python main.py`
5. Connect via WebSocket to ws://localhost:8000/ws

## Documentation
- [Architecture](docs/architecture/phase1-architecture.md)
- [Phase 1 Requirements](docs/plan/PRD_Phase1.md)
- [WebSocket Protocol](docs/clean_documents/WebSocket_Communication_Protocol.md)
- [Technology Stack](docs/plan/tech_stack.md)

## Development
See [docs/](docs/) for detailed documentation.
```

### .env.example
```bash
# Core Database
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key

# AI Services (at least one required)
GOOGLE_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Observability (optional)
LOGFIRE_TOKEN=your-logfire-token

# Environment
PORT=8000
DEBUG=false
```

## Development Workflow

### 1. Starting a New Feature
```bash
# 1. Create feature branch
git checkout -b feature/feature-name

# 2. Add/modify relevant files
# For agents: src/agents/
# For handlers: src/handlers/
# For models: src/models/

# 3. Add tests
touch test/test_feature.py

# 4. Update documentation
# Update relevant docs in docs/
```

### 2. Running the Project
```bash
# Development
python main.py

# With environment variables
python setup_env.py
python main.py

# Tests
pytest test/

# Specific test
pytest test/test_director_e2e.py -v
```

## File Size Guidelines

- **Keep files under 700 lines**
- If a file grows too large, split by functionality
- Use clear module boundaries

## What Goes Where?

| What | Where | Example |
|------|-------|---------|
| New agent | `src/agents/` | `src/agents/researcher.py` |
| WebSocket handler | `src/handlers/` | Update `websocket.py` |
| Data model | `src/models/` | `src/models/presentation.py` |
| Database query | `src/storage/` | Update `supabase.py` |
| Shared utility | `src/utils/` | `src/utils/formatter.py` |
| Configuration | `config/` | Update `settings.py` |
| Documentation | `docs/` | `docs/feature.md` |
| Tests | `test/` | `test/test_feature.py` |
| Prompts | `config/prompts/modular/` | `new_state.md` |

## Common Operations

### Adding a New Agent
1. Create agent file: `src/agents/my_agent.py`
2. Define agent class inheriting from `BaseAgent`
3. Add to director workflow if needed
4. Create tests: `test/test_my_agent.py`

### Adding a New State
1. Add state to workflow: `src/workflows/state_machine.py`
2. Create prompt: `config/prompts/modular/new_state.md`
3. Update director: `src/agents/director.py`
4. Update intent router: `src/agents/intent_router.py`
5. Add tests

### Modifying WebSocket Protocol
1. Update models: `src/models/websocket_messages.py`
2. Update packager: `src/utils/streamlined_packager.py`
3. Update handler: `src/handlers/websocket.py`
4. Update docs: `docs/clean_documents/WebSocket_Communication_Protocol.md`
5. Run all tests

## Current Implementation Status

### ✅ Implemented (Phase 1)
- WebSocket API with intent-based routing
- Director agent with modular prompts
- Session management with Supabase
- Streamlined WebSocket protocol
- State machine workflow
- A/B testing framework
- Token usage tracking

### 🚧 Not Yet Implemented
- Specialist agents (researcher, designer, etc.)
- Redis caching layer
- Docker containerization
- Multiple workflow types
- Vector search capabilities
- Real-time collaboration

## Benefits of This Structure

✅ **Easy to Navigate** - Clear organization by function  
✅ **Easy to Scale** - Add new features without restructuring  
✅ **Easy to Test** - Flat test structure, clear boundaries  
✅ **Easy to Deploy** - Railway/Heroku ready  
✅ **Easy to Understand** - Logical grouping and naming  

## Remember

- **Follow the patterns** - Consistency is key
- **Document changes** - Update relevant docs
- **Write tests** - Every feature needs tests
- **Keep it clean** - Remove unused code