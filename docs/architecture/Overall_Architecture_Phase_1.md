# Deckster Phase 1 Architecture

## Executive Summary

Deckster is a WebSocket-based AI presentation assistant built with FastAPI, featuring a state-driven architecture with intent-based routing. The system implements a streamlined WebSocket protocol for real-time communication and uses Supabase for persistent storage with PostgreSQL.

## System Architecture Overview

```
┌─────────────────┐     WebSocket      ┌──────────────────┐
│                 │ ◄──────────────────►│                  │
│   Web Client    │                     │   FastAPI App    │
│   (Frontend)    │     JSON Messages   │   (main.py)      │
│                 │                     │                  │
└─────────────────┘                     └────────┬─────────┘
                                                 │
                                                 ▼
                                    ┌────────────────────────┐
                                    │   WebSocket Handler    │
                                    │ (Intent-based routing) │
                                    └────────────┬───────────┘
                                                 │
                ┌────────────────────────────────┴────────────────────────────┐
                │                                                             │
                ▼                                                             ▼
    ┌─────────────────────┐                                      ┌──────────────────────┐
    │   Intent Router     │                                      │  Director Agent      │
    │ (Classification)    │                                      │ (State Processing)   │
    └─────────────────────┘                                      └──────────────────────┘
                │                                                             │
                └─────────────────────┬───────────────────────────────────────┘
                                      │
                ┌─────────────────────┴──────────────────────┐
                │                                            │
                ▼                                            ▼
    ┌─────────────────────┐                     ┌──────────────────────┐
    │  Session Manager    │                     │  Message Packager    │
    │  (State & Memory)   │                     │ (Protocol Handler)   │
    └──────────┬──────────┘                     └──────────────────────┘
               │
               ▼
    ┌─────────────────────┐
    │    Supabase DB      │
    │   (PostgreSQL)      │
    └─────────────────────┘
```

## Core Components

### 1. WebSocket Handler (`src/handlers/websocket.py`)

**Responsibility**: Manages WebSocket connections and message routing

**Key Features**:
- Handles connection lifecycle
- Routes messages based on intent classification
- Implements A/B testing for streamlined protocol
- Manages state transitions
- Error handling and recovery

**Key Methods**:
- `websocket_endpoint()`: Main WebSocket connection handler
- `process_user_message()`: Routes messages based on intent
- `determine_state_transition()`: Maps intents to state changes

### 2. Intent Router (`src/agents/intent_router.py`)

**Responsibility**: Classifies user messages into specific intents

**Intent Types**:
- `Submit_Initial_Topic` → ASK_CLARIFYING_QUESTIONS
- `Submit_Clarification_Answers` → CREATE_CONFIRMATION_PLAN
- `Accept_Plan` → GENERATE_STRAWMAN
- `Reject_Plan` → CREATE_CONFIRMATION_PLAN (loop)
- `Accept_Strawman` → END/Complete
- `Submit_Refinement_Request` → REFINE_STRAWMAN
- `Change_Topic` → ASK_CLARIFYING_QUESTIONS (reset)
- `Change_Parameter` → CREATE_CONFIRMATION_PLAN (regen)
- `Ask_Help_Or_Question` → No state change

**Technology**: Pydantic AI with Gemini/GPT-4/Claude models

### 3. Director Agent (`src/agents/director.py`)

**Responsibility**: Core business logic for each workflow state

**States Handled**:
- PROVIDE_GREETING
- ASK_CLARIFYING_QUESTIONS
- CREATE_CONFIRMATION_PLAN
- GENERATE_STRAWMAN
- REFINE_STRAWMAN

**Features**:
- Modular prompt system
- State-specific agents
- Context-aware processing
- Multi-model support (Google, OpenAI, Anthropic)

### 4. Session Manager (`src/utils/session_manager.py`)

**Responsibility**: Manages session state and persistence

**Features**:
- In-memory caching with Supabase backing
- State tracking and transitions
- Conversation history management
- Session data persistence
- User-scoped sessions

**Key Methods**:
- `get_session()`: Retrieves session with caching
- `update_session()`: Updates and persists session state
- `add_to_history()`: Appends to conversation history

### 5. Message Packagers

#### StreamlinedMessagePackager (`src/utils/streamlined_packager.py`)
- Converts agent outputs to structured WebSocket messages
- Message types: chat_message, action_request, slide_update, status_update
- Handles state-specific packaging logic

#### MessagePackager (`src/utils/message_packager.py`)
- Legacy protocol support
- Backward compatibility

## Data Models

### Session Model (`src/models/session.py`)

```python
Session:
  - id: str
  - user_id: str
  - current_state: Literal[states]
  - conversation_history: List[Dict]
  - user_initial_request: Optional[str]
  - clarifying_answers: Optional[Dict]
  - confirmation_plan: Optional[Dict]
  - presentation_strawman: Optional[Dict]
  - refinement_feedback: Optional[str]
  - created_at: datetime
  - updated_at: datetime
```

### WebSocket Message Protocol (`src/models/websocket_messages.py`)

#### StreamlinedMessage Types:

**1. ChatMessage**:
```json
{
  "type": "chat_message",
  "data": {
    "text": "string",
    "sub_title": "optional string",
    "list_items": ["optional", "list"],
    "format": "markdown | plain"
  }
}
```

**2. ActionRequest**:
```json
{
  "type": "action_request",
  "data": {
    "prompt_text": "string",
    "actions": [
      {
        "label": "string",
        "value": "string",
        "primary": true,
        "requires_input": false
      }
    ]
  }
}
```

**3. SlideUpdate**:
```json
{
  "type": "slide_update",
  "data": {
    "operation": "full_update | partial_update",
    "metadata": {
      "title": "string",
      "subtitle": "string",
      "current_slide": 1,
      "total_slides": 10
    },
    "slides": [
      {
        "id": "string",
        "title": "string",
        "content": "string",
        "speaker_notes": "string",
        "layout": "string",
        "position": 1
      }
    ],
    "affected_slides": ["optional", "slide", "ids"]
  }
}
```

**4. StatusUpdate**:
```json
{
  "type": "status_update",
  "data": {
    "status": "idle | thinking | generating | complete | error",
    "text": "string",
    "progress": 50,
    "estimated_time": 30
  }
}
```

## Data Flow

### 1. Connection Establishment
```
Client → WebSocket(/ws?session_id=X&user_id=Y) → WebSocketHandler
```

### 2. Message Processing Flow
```
User Message → Intent Classification → State Determination → 
Director Processing → Response Packaging → WebSocket Response
```

### 3. State Transitions
```
PROVIDE_GREETING → ASK_CLARIFYING_QUESTIONS → CREATE_CONFIRMATION_PLAN → 
GENERATE_STRAWMAN → REFINE_STRAWMAN (optional loop)
```

## Storage Layer

### Supabase Integration (`src/storage/supabase.py`)

**Database**: PostgreSQL (via Supabase)

**Tables**:
- `sessions`: Stores session state and history

**Features**:
- Real-time capabilities (not yet utilized)
- Row-level security ready
- JSON/JSONB for flexible data storage

**Schema**:
```sql
CREATE TABLE sessions (
  id UUID PRIMARY KEY,
  user_id TEXT NOT NULL,
  current_state TEXT NOT NULL,
  conversation_history JSONB,
  user_initial_request TEXT,
  clarifying_answers JSONB,
  confirmation_plan JSONB,
  presentation_strawman JSONB,
  refinement_feedback TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE
);
```

## Key Architectural Decisions

### 1. State-Driven Architecture
- Clear separation of concerns
- Predictable flow
- Easy to test and debug
- Supports complex workflows

### 2. Intent-Based Routing
- Natural conversation flow
- Flexible user interactions
- Clear mapping to state transitions
- Supports context switching

### 3. Modular Prompt System
- Base prompt + state-specific prompts
- Easy to maintain and update
- Consistent agent behavior
- Version control friendly

### 4. Streamlined WebSocket Protocol
- Structured message types
- Frontend-friendly format
- Supports real-time updates
- A/B testing capability

### 5. Multi-Model AI Support
- Fallback options
- Cost optimization
- Performance tuning
- Provider independence

## Technology Stack

- **Framework**: FastAPI (async Python)
- **WebSocket**: Native FastAPI WebSocket support
- **AI/LLM**: 
  - Pydantic AI for agent framework
  - Support for Google (Gemini), OpenAI, and Anthropic models
- **Database**: PostgreSQL via Supabase
- **Data Validation**: Pydantic models throughout
- **Logging**: Pydantic Logfire
- **Environment**: Python 3.9+

## Configuration

### Environment Variables (from `.env.example`)

**Required**:
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- At least one AI key: `GOOGLE_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`

**Optional**:
- `LOGFIRE_TOKEN`: For observability
- `PORT`: Server port (default 8000)
- `DEBUG`: Debug mode flag

### Settings Configuration (`config/settings.py`)
- Model preferences and fallbacks
- Feature flags (e.g., streamlined protocol)
- Prompt template paths
- Cache configuration

## API Endpoints

### 1. WebSocket: `/ws?session_id={session_id}&user_id={user_id}`
- Real-time bidirectional communication
- Intent-based message handling
- Streamlined protocol support

### 2. REST Endpoints:
- `GET /`: API information
- `GET /health`: Health check
- `GET /test-handler`: Handler initialization test

## Security Considerations

1. **Authentication**: User ID required for WebSocket connections
2. **Session Isolation**: Sessions are user-scoped
3. **CORS**: Configured for specific domains
4. **Input Validation**: Pydantic models validate all inputs
5. **SQL Injection**: Protected via Supabase client

## Performance Optimizations

1. **Session Caching**: In-memory cache reduces database hits
2. **Async Architecture**: Non-blocking I/O throughout
3. **Context Building**: Minimal context per state
4. **Streamlined Protocol**: Reduced message overhead
5. **Connection Pooling**: Via Supabase client

## Error Handling

1. **Connection Errors**: Graceful WebSocket disconnection
2. **AI Provider Failures**: Fallback to alternative models
3. **Database Errors**: Cached fallback when possible
4. **Invalid States**: Automatic state recovery
5. **Message Validation**: Pydantic validation with clear errors

## Monitoring and Observability

- **Logfire Integration**: Structured logging with traces
- **WebSocket Events**: Connection, message, and error tracking
- **Performance Metrics**: Response times and model usage
- **Error Tracking**: Detailed error context and stack traces

## Future Considerations (Phase 2+)

1. **Enhanced Workflow**: LangGraph integration for complex flows
2. **Vector Search**: pgvector for similarity matching
3. **Redis Integration**: For distributed caching
4. **MCP Servers**: Tool augmentation
5. **Multi-Agent System**: Specialized agents for different tasks
6. **Real-time Collaboration**: Multi-user sessions
7. **Template Library**: Pre-built presentation templates
8. **Export Options**: PowerPoint, PDF, Google Slides

## Deployment Architecture

```
┌─────────────┐
│   Railway   │  (or similar PaaS)
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  FastAPI    │────►│  Supabase   │
│  Container  │     │  (Managed)  │
└─────────────┘     └─────────────┘
```

### Deployment Considerations
- **Containerized**: Docker-ready for consistent deployments
- **Environment-based Config**: Easy staging/production separation
- **Horizontal Scaling**: Stateless design supports multiple instances
- **Health Checks**: Built-in endpoints for monitoring

## Development Workflow

1. **Local Development**: 
   - `.env` file for configuration
   - Hot reload with FastAPI
   - Local Supabase or cloud instance

2. **Testing**:
   - Unit tests for individual components
   - Integration tests for WebSocket flows
   - End-to-end tests with test scenarios

3. **Deployment**:
   - Git push triggers deployment
   - Environment variables in deployment platform
   - Automatic health checks post-deployment

## Conclusion

The Phase 1 architecture provides a solid foundation for an AI-powered presentation assistant with:
- Clear separation of concerns
- Scalable design patterns
- Modern technology stack
- Room for future enhancements

The state-driven approach with intent-based routing ensures predictable behavior while maintaining flexibility for natural conversations. The streamlined WebSocket protocol provides efficient real-time communication, and the modular design allows for easy maintenance and feature additions.