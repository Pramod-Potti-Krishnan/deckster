# Base Model Architecture - Phase 1

## Overview

This document describes the base model architecture implemented in Phase 1 of Deckster. These models form the foundation of the data structures used throughout the application, enabling type-safe communication between components, state management, and data persistence.

## Architecture Philosophy

The Phase 1 models were designed with several key principles:

1. **Type Safety**: All models use Pydantic for runtime validation and type checking
2. **State-Driven Design**: Models support the five-state workflow (PROVIDE_GREETING → ASK_CLARIFYING_QUESTIONS → CREATE_CONFIRMATION_PLAN → GENERATE_STRAWMAN → REFINE_STRAWMAN)
3. **Separation of Concerns**: Different model files handle different aspects (agents, sessions, websocket communication)
4. **Future Flexibility**: Models use open-ended fields to accommodate future enhancements without breaking changes

## Model Categories

### 1. Agent Models (`src/models/agents.py`)

These models support the agent-based architecture and state machine workflow.

#### UserIntent

**Purpose**: Represents the classified intention of a user message, enabling intelligent state transitions.

```python
class UserIntent(BaseModel):
    intent_type: Literal[
        "Submit_Initial_Topic",
        "Submit_Clarification_Answers", 
        "Accept_Plan",
        "Reject_Plan",
        "Accept_Strawman",
        "Submit_Refinement_Request",
        "Change_Topic",
        "Change_Parameter",
        "Ask_Help_Or_Question"
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_info: Optional[str] = None
```

**Why it exists**: The intent classification system allows the Director agent to understand user messages and determine the appropriate next action without hardcoded rules.

**Used by**:
- `IntentRouter`: Creates UserIntent objects from user messages
- `WebSocketHandler`: Uses intent to determine state transitions
- `DirectorAgent`: Receives intent as part of context for decision making

#### StateContext

**Purpose**: Provides complete context for agent processing, maintaining conversation state and history.

```python
class StateContext(BaseModel):
    current_state: Literal[
        "PROVIDE_GREETING",
        "ASK_CLARIFYING_QUESTIONS",
        "CREATE_CONFIRMATION_PLAN",
        "GENERATE_STRAWMAN",
        "REFINE_STRAWMAN"
    ]
    user_intent: Optional[UserIntent] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    session_data: Dict[str, Any] = Field(default_factory=dict)
```

**Why it exists**: Agents need context to make informed decisions. This model provides a consistent interface for passing state and history to agents.

**Used by**:
- `DirectorAgent`: Primary consumer for state-based processing
- `ContextBuilder`: Creates optimized contexts for each state
- `WebSocketHandler`: Builds context from session data

#### ClarifyingQuestions

**Purpose**: Structured output for the ASK_CLARIFYING_QUESTIONS state.

```python
class ClarifyingQuestions(BaseModel):
    questions: List[str] = Field(min_length=3, max_length=5)
```

**Why it exists**: Ensures the Director always asks an appropriate number of questions (3-5) to gather necessary information without overwhelming the user.

**Used by**:
- `DirectorAgent`: Produces this as output for state 2
- `StreamlinedMessagePackager`: Converts to chat messages with list items

#### ConfirmationPlan

**Purpose**: Structured presentation plan for user confirmation.

```python
class ConfirmationPlan(BaseModel):
    summary_of_user_request: str
    key_assumptions: List[str] = Field(min_length=1)
    proposed_slide_count: int = Field(ge=2, le=30)
```

**Why it exists**: Provides a clear contract between the user and system before investing time in content generation. Allows users to verify assumptions and scope.

**Used by**:
- `DirectorAgent`: Produces this as output for state 3
- `StreamlinedMessagePackager`: Converts to chat message + action request

#### Slide

**Purpose**: Represents an individual slide with flexible content guidance.

```python
class Slide(BaseModel):
    slide_number: int = Field(ge=1)
    slide_id: str
    slide_type: Literal[
        "title_slide", "section_divider", "content_heavy",
        "visual_heavy", "data_driven", "diagram_focused",
        "mixed_content", "conclusion_slide"
    ]
    title: str
    narrative: str
    key_points: List[str] = Field(max_length=5)
    analytics_needed: Optional[str] = None
    visuals_needed: Optional[str] = None
    diagrams_needed: Optional[str] = None
    structure_preference: Optional[str] = None
    speaker_notes: Optional[str] = None
```

**Why it exists**: Provides a flexible, content-focused representation of slides that can be interpreted by different agents and rendering systems. The optional "guidance" fields allow for rich descriptions without rigid structure.

**Design Decision**: Instead of rigid data structures for visuals/charts, we use descriptive text fields that follow patterns like "**Goal:** ... **Content:** ... **Style:** ...". This allows maximum flexibility for future agents.

**Used by**:
- `DirectorAgent`: Creates slides as part of PresentationStrawman
- `StreamlinedMessagePackager`: Converts to slide_update messages
- Future agents will interpret and enhance these slides

#### PresentationStrawman

**Purpose**: Complete presentation structure with metadata.

```python
class PresentationStrawman(BaseModel):
    main_title: str
    overall_theme: str
    design_suggestions: Optional[str] = None
    target_audience: Optional[str] = None
    presentation_duration: Optional[int] = None  # minutes
    slides: List[Slide]
```

**Why it exists**: Encapsulates an entire presentation plan that can be refined, enhanced, and eventually rendered. Provides metadata that influences all slides.

**Used by**:
- `DirectorAgent`: Main output for state 4 (GENERATE_STRAWMAN)
- `StreamlinedMessagePackager`: Converts to complete slide_update message
- `SessionManager`: Stored in session for persistence

### 2. Session Model (`src/models/session.py`)

#### Session

**Purpose**: Persistent session state that mirrors the Supabase database schema.

```python
class Session(BaseModel):
    id: str
    user_id: str
    current_state: Literal[
        "PROVIDE_GREETING",
        "ASK_CLARIFYING_QUESTIONS", 
        "CREATE_CONFIRMATION_PLAN",
        "GENERATE_STRAWMAN",
        "REFINE_STRAWMAN"
    ]
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    user_initial_request: Optional[str] = None
    clarifying_answers: Optional[Dict[str, Any]] = None
    confirmation_plan: Optional[Dict[str, Any]] = None
    presentation_strawman: Optional[Dict[str, Any]] = None
    refinement_feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

**Why it exists**: Provides durable storage for conversation state, allowing users to disconnect and reconnect without losing progress. The structure directly maps to Supabase columns for efficient persistence.

**Design Decisions**:
- Uses Dict[str, Any] for complex nested data to match JSONB columns
- Timestamps for audit trail and session management
- All agent outputs stored for full conversation reconstruction

**Used by**:
- `SessionManager`: CRUD operations and caching
- `WebSocketHandler`: Session lifecycle management
- `SupabaseOperations`: Database persistence

### 3. WebSocket Message Models (`src/models/websocket_messages.py`)

These models implement the streamlined WebSocket protocol for efficient frontend communication.

#### Base Message Structure

**BaseMessage**: Common envelope for all messages
```python
class BaseMessage(BaseModel):
    message_id: str
    session_id: str
    timestamp: str
    type: MessageType
```

#### Message Types

**ChatMessage**: Conversational content
```python
class ChatMessageData(BaseModel):
    text: str
    sub_title: Optional[str] = None
    list_items: Optional[List[str]] = None
    format: Literal["markdown", "plain"] = "markdown"
```

**ActionRequest**: Interactive buttons
```python
class ActionRequestData(BaseModel):
    prompt_text: str
    actions: List[Action]

class Action(BaseModel):
    label: str
    value: str
    primary: bool = False
    requires_input: bool = False
```

**SlideUpdate**: Presentation updates
```python
class SlideUpdateData(BaseModel):
    operation: Literal["full_update", "partial_update"]
    metadata: SlideMetadata
    slides: List[SlideData]
    affected_slides: Optional[List[str]] = None
```

**StatusUpdate**: Progress indicators
```python
class StatusUpdateData(BaseModel):
    status: StatusLevel
    text: str
    progress: Optional[int] = Field(None, ge=0, le=100)
    estimated_time: Optional[int] = None  # seconds
```

**Why these exist**: The streamlined protocol was designed to map directly to frontend UI components, reducing complexity and improving performance. Each message type has a single responsibility.

**Used by**:
- `StreamlinedMessagePackager`: Creates these messages from agent outputs
- `WebSocketHandler`: Sends messages to frontend
- `MessageAdapter`: Converts between legacy and streamlined formats

## Model Relationships

### Data Flow Through Models

```
User Input → IntentRouter → UserIntent
                ↓
         StateContext ← SessionManager ← Session (DB)
                ↓
          DirectorAgent
                ↓
    Agent Output Models (ClarifyingQuestions, ConfirmationPlan, etc.)
                ↓
    StreamlinedMessagePackager
                ↓
    WebSocket Messages → Frontend
```

### State Persistence

```
Session (Pydantic) ↔ Supabase (JSONB) ↔ SessionManager (Cache)
```

## Key Design Benefits

### 1. Type Safety
- Pydantic validation prevents invalid data
- IDE autocomplete and type checking
- Clear contracts between components

### 2. Flexibility
- Open-ended guidance fields in Slide model
- Optional fields for gradual enhancement
- JSONB storage for nested structures

### 3. Performance
- Efficient caching with Pydantic models
- Streamlined protocol reduces overhead
- Async-friendly design

### 4. Maintainability
- Clear separation of concerns
- Self-documenting with field descriptions
- Consistent patterns across models

## Future Extensibility

The Phase 1 models were designed to accommodate future enhancements:

1. **Agent Models**: Can add new output types for specialist agents
2. **Session Model**: JSONB fields can store new agent outputs
3. **WebSocket Models**: Protocol supports new message types
4. **Slide Model**: Guidance fields can be interpreted differently by new agents

This architecture provides a solid foundation for Phase 2's parallel agents and Phase 3's multi-agent collaboration while maintaining backward compatibility.