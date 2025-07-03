# PRP: Phase 1 - WebSocket API with Director (Inbound) Agent

## FEATURE: WebSocket-based API with Director (Inbound) Agent

Implement a WebSocket API that enables front-end applications to communicate presentation requirements to the Director (Inbound) Agent, with intelligent clarification gathering and initial structure generation.

## EXAMPLES:

The system should handle these interaction flows:
- Client connects via WebSocket with JWT authentication
- Client sends: `{"type": "user_input", "data": {"text": "Create a B2B SaaS pitch deck"}}`
- Director analyzes and responds with clarification questions
- Client provides answers
- Director generates initial presentation structure

## DOCUMENTATION:

### Core Technology References
- **Pydantic AI Documentation**: https://ai.pydantic.dev/
- **Pydantic AI Agents**: https://ai.pydantic.dev/agents/
- **Pydantic AI Models**: https://ai.pydantic.dev/models/
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **LangGraph Workflows**: https://langchain-ai.github.io/langgraph/tutorials/workflows/
- **FastAPI WebSockets**: https://fastapi.tiangolo.com/advanced/websockets/
- **FastAPI JWT Auth WebSocket**: https://indominusbyte.github.io/fastapi-jwt-auth/advanced-usage/websocket/
- **Supabase pgvector**: https://supabase.com/docs/guides/database/extensions/pgvector
- **Supabase Vector Columns**: https://supabase.com/docs/guides/ai/vector-columns

### Internal Documentation References
- Communication Protocol: `/plan/comms_protocol.md` (sections 5.1 and 5.2)
- Technology Stack: `/plan/tech_stack.md`
- Security Requirements: `/plan/security.md`
- Folder Structure: `/plan/folder_structure.md`

## OTHER CONSIDERATIONS:

### Critical Implementation Notes
1. **WebSocket JWT Authentication**: JWT should be passed in request headers or as first message
2. **Pydantic AI Multi-LLM**: Use FallbackModel for automatic failover between models
3. **LangGraph State Management**: Use TypedDict for state definition with proper annotations
4. **Supabase Setup**: Must enable pgvector extension and create RPC functions for similarity search
5. **Error Handling**: Use WebSocketException instead of HTTPException for WebSocket errors
6. **File Size Limits**: Keep all files under 700 lines, refactor if larger

### Security Requirements (MVP)
- JWT with 24-hour expiry
- WSS for secure WebSocket connections
- Input validation with Pydantic models (max 5000 chars)
- Rate limiting: 10 requests per minute
- Basic prompt injection protection

## IMPLEMENTATION BLUEPRINT:

### Phase 1 Architecture Overview
```
Client <--WSS--> WebSocket Handler <--> Director Agent <--> LangGraph Workflow
                        |                      |                    |
                        v                      v                    v
                  JWT Auth/Session        Pydantic AI          State Management
                        |                      |                    |
                        v                      v                    v
                  Redis Cache            Supabase DB         Session Memory
```

### Implementation Approach (Pseudocode)
```python
# 1. WebSocket connection with JWT auth
async def websocket_endpoint(websocket: WebSocket):
    # Validate JWT from headers or first message
    token = await get_jwt_token(websocket)
    if not validate_jwt(token):
        raise WebSocketException("Unauthorized")
    
    # Initialize session
    session = await create_or_restore_session(token)
    
    # Main message loop
    async for message in websocket.iter_json():
        # Validate input with Pydantic
        user_input = UserInput.model_validate(message)
        
        # Process through Director Agent
        response = await director_agent.process(user_input, session)
        
        # Send response back
        await websocket.send_json(response.model_dump())

# 2. Director Agent with LangGraph workflow
director_workflow = StateGraph()
director_workflow.add_node("analyze", analyze_request)
director_workflow.add_node("clarify", generate_questions)
director_workflow.add_node("structure", create_structure)

# 3. Supabase vector search for similar presentations
async def find_similar_presentations(request):
    embedding = await generate_embedding(request)
    results = await supabase.rpc('match_presentations', {
        'query_embedding': embedding,
        'match_threshold': 0.8
    })
    return results
```

## TASK LIST (Implementation Order):

### 1. Project Setup and Configuration
- [ ] Create project structure following `/plan/folder_structure.md`
- [ ] Set up virtual environment and install dependencies
- [ ] Create `.env` file with required environment variables
- [ ] Initialize git repository with `.gitignore`

### 2. Database Setup (Supabase)
- [ ] Enable pgvector extension in Supabase
- [ ] Create sessions table with RLS policies
- [ ] Create presentations table with vector column
- [ ] Create `match_presentations` RPC function
- [ ] Create database migration scripts

### 3. Core Models Implementation (`src/models/`)
- [ ] Create `messages.py` with WebSocket message models
- [ ] Create `presentation.py` with presentation structure models
- [ ] Create `agents.py` with agent-specific models
- [ ] Add validation rules and examples

### 4. Authentication and Security (`src/utils/`)
- [ ] Implement JWT authentication in `auth.py`
- [ ] Create input validators in `validators.py`
- [ ] Set up logging with LogFire in `logger.py`
- [ ] Add rate limiting middleware

### 5. Storage Layer (`src/storage/`)
- [ ] Implement Supabase client in `supabase.py`
- [ ] Create Redis cache layer in `redis_cache.py`
- [ ] Add session management functions
- [ ] Implement vector storage operations

### 6. Director Agent Implementation (`src/agents/`)
- [ ] Create base agent class in `base.py`
- [ ] Implement Director (Inbound) in `director_in.py`
- [ ] Add clarification question generation logic
- [ ] Add structure creation capabilities

### 7. LangGraph Workflow (`src/workflows/`)
- [ ] Define workflow state structure
- [ ] Create main workflow in `main.py`
- [ ] Add nodes for each processing step
- [ ] Implement conditional routing logic

### 8. WebSocket API (`src/api/`)
- [ ] Create WebSocket handler in `websocket.py`
- [ ] Implement JWT validation for WebSocket
- [ ] Add message processing loop
- [ ] Create error handling middleware

### 9. Configuration and Prompts
- [ ] Create app settings in `config/settings.py`
- [ ] Add Director agent prompts in `config/prompts/`
- [ ] Set up environment-specific configurations

### 10. Testing
- [ ] Write unit tests for models
- [ ] Create integration tests for WebSocket
- [ ] Test Director agent responses
- [ ] Add end-to-end workflow tests

### 11. Documentation and Deployment
- [ ] Create API documentation
- [ ] Write deployment instructions
- [ ] Set up Docker configuration
- [ ] Create health check endpoints

## VALIDATION GATES:

```bash
# 1. Code Quality Checks
ruff check --fix src/ tests/
mypy src/ --strict

# 2. Unit Tests
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# 3. Integration Tests
pytest tests/integration/ -v

# 4. Security Scan
bandit -r src/ -f json -o bandit-report.json
safety check

# 5. WebSocket Connection Test
python -m pytest tests/integration/test_websocket.py::test_jwt_authentication -v

# 6. Director Agent Test
python -m pytest tests/integration/test_director.py::test_clarification_flow -v

# 7. Full Workflow Test
python -m pytest tests/e2e/test_phase1_flow.py -v
```

## CODE EXAMPLES:

### WebSocket Handler with JWT Auth (`src/api/websocket.py`)
```python
from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState
import jwt
from typing import Optional
from src.models.messages import UserInput, DirectorMessage
from src.agents.director_in import DirectorInboundAgent
from src.utils.auth import validate_jwt_token
from src.storage.redis_cache import RedisCache

async def get_jwt_from_websocket(websocket: WebSocket) -> Optional[str]:
    """Extract JWT from headers or first message"""
    # Check headers first
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    
    # Wait for first message with token
    first_message = await websocket.receive_json()
    return first_message.get("token")

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    redis: RedisCache = Depends(get_redis),
    supabase = Depends(get_supabase)
):
    await websocket.accept()
    
    try:
        # Authenticate
        token = await get_jwt_from_websocket(websocket)
        user_data = validate_jwt_token(token)
        if not user_data:
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        # Initialize session
        session_id = f"session_{user_data['user_id']}_{int(time.time())}"
        session = await create_or_restore_session(session_id, redis, supabase)
        
        # Initialize Director Agent
        director = DirectorInboundAgent()
        
        # Message processing loop
        while websocket.client_state == WebSocketState.CONNECTED:
            # Receive and validate message
            raw_message = await websocket.receive_json()
            user_input = UserInput.model_validate(raw_message)
            
            # Process through Director
            async for response in director.process_stream(user_input, session):
                # Send response
                director_message = DirectorMessage(
                    message_id=generate_message_id(),
                    timestamp=datetime.utcnow(),
                    session_id=session_id,
                    type="director_message",
                    source="director_inbound",
                    data=response
                )
                await websocket.send_json(director_message.model_dump())
                
    except WebSocketDisconnect:
        await cleanup_session(session_id, redis)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal error")
```

### Director Agent Implementation (`src/agents/director_in.py`)
```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import FallbackModel
from typing import AsyncGenerator
from src.models.presentation import PresentationRequest, ClarificationRound, PresentationStructure

class DirectorInboundAgent(Agent):
    """Director agent for handling user interactions and orchestration"""
    
    def __init__(self):
        # Multi-LLM setup with fallback
        models = FallbackModel(
            "openai:gpt-4",
            "openai:gpt-3.5-turbo",
            "anthropic:claude-3-sonnet"
        )
        
        super().__init__(
            name="director_inbound",
            model=models,
            system_prompt=self._load_system_prompt(),
            result_type=PresentationStructure,
            retries=3
        )
        
    async def process_stream(
        self,
        user_input: UserInput,
        session: SessionMemory
    ) -> AsyncGenerator[DirectorResponse, None]:
        """Process user input and yield responses"""
        
        # Update session context
        session.add_turn(user_input)
        
        # Check if responding to clarification
        if user_input.response_to:
            session.update_clarification_answer(
                user_input.response_to,
                user_input.text
            )
        
        # Analyze completeness
        if await self._needs_clarification(user_input, session):
            questions = await self._generate_questions(user_input, session)
            yield DirectorResponse(
                slide_data=None,
                chat_data=ChatData(
                    type="question",
                    content=questions,
                    actions=None,
                    progress=None
                )
            )
        else:
            # Generate structure
            structure = await self._create_structure(session)
            yield DirectorResponse(
                slide_data=structure,
                chat_data=ChatData(
                    type="summary",
                    content={"message": "I've created your presentation structure!"},
                    actions=[{
                        "action_id": "accept_structure",
                        "type": "accept_changes",
                        "label": "Looks good!",
                        "primary": True
                    }],
                    progress=None
                )
            )
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file"""
        with open("config/prompts/director.txt", "r") as f:
            return f.read()
```

### LangGraph Workflow (`src/workflows/main.py`)
```python
from typing import TypedDict, List, Annotated
from langgraph import StateGraph
from langgraph.graph import END
import operator

class DirectorWorkflowState(TypedDict):
    """State for Director workflow"""
    user_input: UserInput
    session_context: dict
    clarifications_needed: bool
    clarification_questions: List[ClarificationQuestion]
    user_answers: dict
    presentation_structure: Optional[PresentationStructure]
    similar_presentations: List[dict]
    error: Optional[str]

# Create workflow
workflow = StateGraph(DirectorWorkflowState)

# Define nodes
async def analyze_request(state: DirectorWorkflowState) -> DirectorWorkflowState:
    """Analyze user request for completeness"""
    # Implementation
    return state

async def find_similar(state: DirectorWorkflowState) -> DirectorWorkflowState:
    """Find similar presentations using vector search"""
    # Implementation
    return state

async def generate_questions(state: DirectorWorkflowState) -> DirectorWorkflowState:
    """Generate clarification questions"""
    # Implementation
    return state

async def create_structure(state: DirectorWorkflowState) -> DirectorWorkflowState:
    """Create presentation structure"""
    # Implementation
    return state

# Add nodes
workflow.add_node("analyze", analyze_request)
workflow.add_node("find_similar", find_similar) 
workflow.add_node("clarify", generate_questions)
workflow.add_node("structure", create_structure)

# Define routing
def route_after_analysis(state: DirectorWorkflowState) -> str:
    if state["clarifications_needed"]:
        return "clarify"
    return "structure"

# Add edges
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "find_similar")
workflow.add_conditional_edges(
    "find_similar",
    route_after_analysis,
    {
        "clarify": "clarify",
        "structure": "structure"
    }
)
workflow.add_edge("clarify", END)
workflow.add_edge("structure", END)

# Compile
director_workflow = workflow.compile()
```

## SUCCESS CRITERIA:

1. WebSocket connection accepts JWT authentication
2. Director Agent generates relevant clarification questions
3. Session state persists across reconnections
4. Vector search finds similar presentations
5. Complete presentation structure generated within 5 seconds
6. All validation gates pass
7. 90%+ test coverage

## CONFIDENCE SCORE: 8.5/10

High confidence due to:
- Comprehensive documentation references
- Clear implementation examples
- Well-defined folder structure
- Specific validation gates
- Detailed task breakdown

Minor risks:
- Pydantic AI is relatively new (but well-documented)
- Multi-agent coordination complexity
- WebSocket state management edge cases