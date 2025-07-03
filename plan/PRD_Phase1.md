# PRD Phase 1: API Communication with Director (Inbound) Agent

## References
- [PRD v4.0](./PRD_v4.0.md) - Main product requirements document
- [Communication Protocols](./comms_protocol.md) - Detailed JSON message templates and protocols
- [Technology Stack](./tech_stack.md) - Framework specifications and implementation guidelines
- [Security Requirements](./security.md) - MVP security implementation guidelines
- [Folder Structure](./folder_structure.md) - Project organization and file placement guide

## FEATURE:
WebSocket-based API enabling front-end applications to communicate presentation requirements to the Director (Inbound) Agent, with intelligent clarification gathering and initial structure generation.

## EXAMPLES:
- Client connects via WebSocket
- Client sends: `{"type": "new_presentation", "data": {"topic": "B2B SaaS pitch deck"}}`
- Director responds: `{"type": "clarification", "questions": [{"id": "q1", "text": "What's your target audience?"}]}`
- Client answers questions
- Director generates initial structure: `{"type": "structure", "sections": [...], "slides": [...]}`

## DOCUMENTATION:
- **Agent Framework**: Pydantic AI Agent Module for multi-LLM access
- **Agent Orchestration**: LangGraph for agent chaining and workflow
- **Data Validation**: Pydantic BaseModel for standardized agent outputs
- **Logging**: Pydantic LogFire for comprehensive logging
- **MCP Server**: Leverage pre-built capabilities and tools
- **Communication Protocol**: JSON with HTML-embedded visual content

## KEY COMPONENTS:

### 1. WebSocket API Layer
- **Connection Management**:
  - JWT authentication
  - Session initialization with unique IDs
  - Heartbeat mechanism for connection health
  - Auto-reconnection with session recovery
- **Message Protocol** (Pydantic Models):
  ```python
  from pydantic import BaseModel
  
  class WSMessage(BaseModel):
      id: str
      type: Literal['request', 'clarification', 'answer', 'structure', 'error']
      timestamp: datetime
      session_id: str
      data: Dict[str, Any]
  ```

### 2. Director (Inbound) Agent
- **Agent Definition** (Pydantic AI):
  ```python
  from pydantic_ai import Agent
  
  class DirectorInboundAgent(Agent):
      name = "director_inbound"
      description = "Manages initial user interaction and requirements gathering"
      
      async def process_request(self, request: PresentationRequest) -> ClarificationRound:
          # Multi-LLM access for optimal performance
          # Generate contextual questions
          # Return standardized Pydantic model
  ```
- **Core Capabilities**:
  - Parse presentation requests
  - Generate dynamic clarification questions
  - Validate requirement completeness
  - Create initial presentation structure

### 3. Data Models (Pydantic BaseModel)
```python
class PresentationRequest(BaseModel):
    session_id: str
    user_id: str
    topic: str
    presentation_type: str
    initial_context: Dict[str, Any]
    
class ClarificationQuestion(BaseModel):
    id: str
    question: str
    response_type: Literal['text', 'choice', 'multiselect']
    options: Optional[List[str]]
    required: bool
    
class PresentationStructure(BaseModel):
    title: str
    sections: List[Section]
    slides: List[SlideOutline]
    metadata: Dict[str, Any]
    html_preview: Optional[str]  # HTML string for visual preview
```

### 4. LangGraph Workflow
```python
from langgraph import Graph

director_workflow = Graph()
director_workflow.add_node("receive_request", receive_request_handler)
director_workflow.add_node("analyze_completeness", analyze_handler)
director_workflow.add_node("generate_questions", question_generator)
director_workflow.add_node("validate_answers", answer_validator)
director_workflow.add_node("create_structure", structure_creator)
```

## OTHER CONSIDERATIONS:

### Technical Architecture
- **Logging Strategy** (LogFire):
  - Request/response tracking
  - LLM call monitoring
  - Performance metrics
  - Error tracking with context
- **MCP Server Integration**:
  - Utilize document parsing tools
  - Leverage template libraries
  - Access knowledge base tools

### Agent Communication
- **JSON Protocol Structure**:
  ```json
  {
    "agent_id": "director_inbound",
    "message_type": "structure_output",
    "payload": {
      "slides": [
        {
          "id": "slide_1",
          "content": {
            "text": "...",
            "html": "<div class='slide'>...</div>"
          }
        }
      ]
    }
  }
  ```

### Memory Management

#### Short-term Memory (Contextual)
- **Session Storage**: Supabase (PostgreSQL) with Redis caching
  ```python
  class SessionMemory(BaseModel):
      session_id: str
      conversation_history: List[ConversationTurn]
      current_requirements: Dict[str, Any]
      clarification_state: ClarificationState
      created_at: datetime
      updated_at: datetime
  ```
- **Dual-Layer Architecture**:
  - **Redis**: Hot sessions cache (last 30 mins activity)
  - **Supabase**: Persistent session storage with RLS
  - Automatic sync between layers
- **Context Management**:
  - Sliding window in Redis (last 10 turns)
  - Full history in Supabase
  - Smart context retrieval based on relevance

#### Long-term Memory (Tools & Knowledge)
- **Supabase Vector Storage** (pgvector):
  ```python
  class KnowledgeStore:
      async def store_presentation_pattern(self, structure: PresentationStructure):
          # Store in Supabase with vector embeddings
          embedding = await generate_embedding(structure)
          await supabase.table('presentation_patterns').insert({
              'embedding': embedding,
              'structure': structure.dict(),
              'metadata': {...}
          })
          
      async def find_similar_presentations(self, request: PresentationRequest) -> List[StructureExample]:
          # Vector similarity search in Supabase
          query_embedding = await generate_embedding(request)
          return await supabase.rpc('match_presentations', {
              'query_embedding': query_embedding,
              'match_threshold': 0.8,
              'match_count': 5
          })
  ```
- **MCP Server Integration**:
  - Document templates in Supabase Storage
  - Industry knowledge base with vector search
  - Design patterns indexed by use case
- **Learning System**:
  - Store successful Q&A patterns
  - Track presentation outcomes
  - Build domain expertise over time

### Performance Requirements
- WebSocket latency: <100ms
- Question generation: <2s (via Pydantic AI's optimized LLM routing)
- Structure creation: <5s
- Concurrent sessions: 1000+

### Development Priorities
1. Setup Pydantic AI agents with multi-LLM configuration
2. Implement WebSocket server with Pydantic model validation
3. Create LangGraph workflow for Director (Inbound)
4. Integrate LogFire for comprehensive logging
5. Connect to MCP server for enhanced capabilities
6. Build session management with Redis
7. Create comprehensive test suite

### Success Metrics
- Average clarification rounds: 3-5
- Structure generation accuracy: >90%
- Session completion rate: >85%
- API response time (p95): <3s