# Technology Stack Documentation

## Core Framework Libraries

### 1. Pydantic BaseModel - Data Validation & Standardization

**Purpose**: Ensure all agent outputs and inter-agent communication are standardized and validated.

**Documentation**: https://docs.pydantic.dev/latest/

**Best Practice Implementation**:

```python
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal
from datetime import datetime

# Standard output model for all agents
class AgentOutput(BaseModel):
    """Base model for all agent outputs ensuring consistency"""
    agent_id: str = Field(..., description="Unique agent identifier")
    output_type: str = Field(..., description="Type of output produced")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    correlation_id: str
    status: Literal["completed", "partial", "failed"]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Specific agent output example
class VisualAssetOutput(AgentOutput):
    """Visual Designer agent output model"""
    output_type: Literal["image"] = "image"
    asset: Dict[str, Any] = Field(..., description="Asset details")
    
    @validator('asset')
    def validate_asset_structure(cls, v):
        required_keys = {'url', 'format', 'dimensions', 'metadata'}
        if not all(key in v for key in required_keys):
            raise ValueError(f"Asset must contain keys: {required_keys}")
        return v

# Slide structure model
class SlideStructure(BaseModel):
    slide_id: str = Field(..., pattern=r"^slide_\d+$")
    slide_number: int = Field(..., ge=1)
    title: str = Field(..., max_length=100)
    layout_type: Literal["hero", "content", "chart_focused", "comparison"]
    components: List[ComponentSpec]
    
    @validator('components')
    def validate_component_count(cls, v, values):
        layout_limits = {
            "hero": 3,
            "content": 5,
            "chart_focused": 2,
            "comparison": 4
        }
        max_components = layout_limits.get(values.get('layout_type'), 5)
        if len(v) > max_components:
            raise ValueError(f"Too many components for {values.get('layout_type')} layout")
        return v
```

**Key Benefits**:
- Automatic validation
- JSON schema generation
- Type hints for IDE support
- Serialization/deserialization
- Clear documentation

### 2. Pydantic AI - Agent Development Framework

**Purpose**: Simplify agent creation with multi-LLM support and standardized interfaces.

**Documentation**: https://ai.pydantic.dev/

**Best Practice Agent Implementation**:

```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import ModelRetry
from typing import AsyncGenerator

class DirectorInboundAgent(Agent):
    """Director agent for handling user interactions and orchestration"""
    
    def __init__(self):
        super().__init__(
            name="director_inbound",
            model="gpt-4",  # Primary model
            fallback_models=["gpt-3.5-turbo", "claude-3"],  # Fallbacks
            system_prompt="""You are the Director (Inbound) agent responsible for:
            1. Understanding user requirements
            2. Asking clarifying questions
            3. Creating presentation structure
            4. Orchestrating other agents
            
            Always output structured JSON according to the defined schemas.""",
            retries=3,
            result_type=PresentationStructure  # Pydantic model for output validation
        )
    
    async def process_request(
        self, 
        ctx: RunContext, 
        request: PresentationRequest
    ) -> PresentationStructure:
        """Process user request and generate structure"""
        
        # Access context and dependencies
        session_memory = ctx.deps.get("session_memory")
        knowledge_base = ctx.deps.get("knowledge_base")
        
        # Check if we need clarifications
        if await self._needs_clarification(request, session_memory):
            questions = await self._generate_questions(request)
            yield ClarificationRound(questions=questions)
        
        # Generate structure using LLM
        result = await self.run(
            user_prompt=f"Create presentation structure for: {request.topic}",
            context={
                "session_history": session_memory.get_history(),
                "similar_presentations": await knowledge_base.find_similar(request)
            }
        )
        
        return result

    async def _needs_clarification(
        self, 
        request: PresentationRequest, 
        memory: SessionMemory
    ) -> bool:
        """Determine if clarification is needed"""
        completeness_check = await self.run(
            "Analyze if this request has sufficient information",
            message_history=[
                {"role": "user", "content": request.model_dump_json()}
            ]
        )
        return completeness_check.needs_clarification

# Usage example
agent = DirectorInboundAgent()
result = await agent.process_request(
    ctx=RunContext(deps={"session_memory": memory, "knowledge_base": kb}),
    request=user_request
)
```

**Multi-LLM Configuration**:

```python
from pydantic_ai import Agent
from pydantic_ai.models import OpenAIModel, AnthropicModel, CohereModel

# Configure multi-model agent
multi_model_agent = Agent(
    name="flexible_agent",
    models=[
        OpenAIModel("gpt-4", temperature=0.7),
        AnthropicModel("claude-3-opus", max_tokens=4000),
        CohereModel("command-xlarge", temperature=0.5)
    ],
    model_selection_strategy="cost_optimized",  # or "performance_first"
    result_type=AgentOutput
)
```

### 3. MCP Server Integration

**Purpose**: Leverage pre-built tools and capabilities through Model Context Protocol.

**Documentation**: 
- MCP Specification: https://modelcontextprotocol.io/
- Pydantic AI MCP: https://ai.pydantic.dev/mcp/

**High-Quality MCP Servers**:

1. **Brave Search MCP** - Web search capabilities
   - Repository: https://github.com/modelcontextprotocol/servers/tree/main/brave-search
   - Use case: Research agent web searches

2. **Filesystem MCP** - File operations
   - Repository: https://github.com/modelcontextprotocol/servers/tree/main/filesystem
   - Use case: Reading reference documents, saving outputs

3. **PostgreSQL MCP** - Database operations
   - Repository: https://github.com/modelcontextprotocol/servers/tree/main/postgres
   - Use case: Storing/retrieving presentation data

4. **Puppeteer MCP** - Web scraping
   - Repository: https://github.com/modelcontextprotocol/servers/tree/main/puppeteer
   - Use case: Extracting data from websites

5. **GitHub MCP** - Repository operations
   - Repository: https://github.com/modelcontextprotocol/servers/tree/main/github
   - Use case: Accessing documentation, code examples

**MCP Server Discovery**:
- Official servers: https://github.com/modelcontextprotocol/servers
- Community servers: https://github.com/topics/mcp-server
- Awesome MCP: https://github.com/punkpeye/awesome-mcp

**Integration Example**:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPClient, Tool

# Initialize MCP client
mcp_client = MCPClient()

# Connect to MCP servers
await mcp_client.connect_to_server(
    "brave-search",
    server_params={"api_key": os.getenv("BRAVE_API_KEY")}
)

await mcp_client.connect_to_server(
    "filesystem",
    server_params={"allowed_directories": ["/data/presentations"]}
)

# Create agent with MCP tools
class ResearcherAgent(Agent):
    def __init__(self):
        super().__init__(
            name="researcher",
            model="gpt-4",
            tools=[
                Tool(
                    name="web_search",
                    description="Search the web for information",
                    mcp_server="brave-search",
                    mcp_tool="search"
                ),
                Tool(
                    name="read_file",
                    description="Read reference documents",
                    mcp_server="filesystem",
                    mcp_tool="read"
                )
            ],
            result_type=ResearchOutput
        )
    
    async def research_topic(self, topic: str) -> ResearchOutput:
        # Agent can now use web_search and read_file tools
        result = await self.run(
            f"Research the following topic: {topic}",
            tools_enabled=["web_search", "read_file"]
        )
        return result
```

### 4. LangGraph - Agent Orchestration

**Purpose**: Define and execute complex multi-agent workflows.

**Documentation**: https://python.langchain.com/docs/langgraph

**Best Practice Workflow Implementation**:

```python
from langgraph import StateGraph, State
from typing import TypedDict, List, Annotated
import operator

# Define workflow state
class PresentationState(TypedDict):
    request: PresentationRequest
    structure: Optional[PresentationStructure]
    clarifications: List[ClarificationRound]
    layouts: Optional[LayoutDesign]
    content: Optional[ResearchOutput]
    visuals: List[VisualAsset]
    final_presentation: Optional[Presentation]
    errors: List[str]

# Create workflow
workflow = StateGraph(PresentationState)

# Add nodes (agents)
workflow.add_node("director_inbound", director_inbound_agent.process)
workflow.add_node("ux_architect", ux_architect_agent.design_layouts)
workflow.add_node("researcher", researcher_agent.research_content)
workflow.add_node("visual_designer", visual_designer_agent.create_visuals)
workflow.add_node("data_analyst", data_analyst_agent.create_charts)
workflow.add_node("director_outbound", director_outbound_agent.assemble)

# Define conditional routing
def route_after_director(state: PresentationState) -> str:
    if state.get("clarifications") and not state["clarifications"][-1].answered:
        return "wait_for_user"
    return "parallel_processing"

workflow.add_conditional_edges(
    "director_inbound",
    route_after_director,
    {
        "wait_for_user": "user_input",
        "parallel_processing": ["ux_architect", "researcher"]
    }
)

# Parallel processing edges
workflow.add_edge("ux_architect", "visual_designer")
workflow.add_edge("researcher", "data_analyst")
workflow.add_edge(["visual_designer", "data_analyst"], "director_outbound")

# Set entry and exit points
workflow.set_entry_point("director_inbound")
workflow.set_finish_point("director_outbound")

# Compile and run
app = workflow.compile()

# Execute workflow
async def generate_presentation(request: PresentationRequest):
    initial_state = {
        "request": request,
        "structure": None,
        "clarifications": [],
        "errors": []
    }
    
    async for state in app.astream(initial_state):
        # Handle intermediate states (e.g., send updates to user)
        if "clarifications" in state and state["clarifications"]:
            await send_clarification_to_user(state["clarifications"][-1])
        
    return state["final_presentation"]
```

**Advanced Orchestration Patterns**:

```python
# Subgraph for iterative refinement
refinement_graph = StateGraph(RefinementState)

refinement_graph.add_node("feedback_analyzer", analyze_feedback)
refinement_graph.add_node("change_router", route_changes_to_agents)
refinement_graph.add_node("apply_changes", apply_changes)
refinement_graph.add_node("validate_coherence", validate_coherence)

# Error handling and retry logic
def add_error_handling(graph: StateGraph):
    def error_handler(state, error):
        state["errors"].append(str(error))
        if len(state["errors"]) < 3:  # Retry up to 3 times
            return "retry"
        return "fallback"
    
    graph.add_error_handler(error_handler)
    graph.add_node("retry", lambda s: s)  # Retry same operation
    graph.add_node("fallback", use_fallback_strategy)
```

### 5. Database Stack - PostgreSQL with pgvector

**Purpose**: Persistent storage with vector similarity search capabilities.

**Documentation**:
- PostgreSQL: https://www.postgresql.org/docs/
- pgvector: https://github.com/pgvector/pgvector
- Supabase: https://supabase.com/docs

**Supabase Setup with pgvector**:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Presentations table with vector embeddings
CREATE TABLE presentations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    title TEXT NOT NULL,
    structure JSONB NOT NULL,
    embedding vector(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Create index for vector similarity search
CREATE INDEX presentations_embedding_idx ON presentations 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Function for similarity search
CREATE OR REPLACE FUNCTION find_similar_presentations(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.8,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    structure JSONB,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.structure,
        1 - (p.embedding <=> query_embedding) as similarity
    FROM presentations p
    WHERE 1 - (p.embedding <=> query_embedding) > match_threshold
    ORDER BY p.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Visual assets table
CREATE TABLE visual_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_type TEXT NOT NULL,
    url TEXT NOT NULL,
    embedding vector(512),  -- CLIP embedding dimension
    tags TEXT[],
    metadata JSONB,
    usage_count INTEGER DEFAULT 0,
    quality_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Session management
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    conversation_history JSONB[],
    current_state JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);
```

**Python Integration**:

```python
from supabase import create_client, Client
import numpy as np
from typing import List, Dict

class SupabaseStore:
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
    
    async def store_presentation(
        self, 
        presentation: PresentationStructure,
        embedding: List[float]
    ) -> str:
        """Store presentation with vector embedding"""
        result = await self.client.table('presentations').insert({
            'session_id': presentation.session_id,
            'title': presentation.title,
            'structure': presentation.model_dump(),
            'embedding': embedding,
            'metadata': {
                'slide_count': len(presentation.slides),
                'presentation_type': presentation.type
            }
        }).execute()
        
        return result.data[0]['id']
    
    async def find_similar_presentations(
        self,
        query_embedding: List[float],
        threshold: float = 0.8,
        limit: int = 5
    ) -> List[Dict]:
        """Find similar presentations using vector search"""
        result = await self.client.rpc(
            'find_similar_presentations',
            {
                'query_embedding': query_embedding,
                'match_threshold': threshold,
                'match_count': limit
            }
        ).execute()
        
        return result.data
    
    async def get_session(self, session_id: str) -> Dict:
        """Retrieve session with conversation history"""
        result = await self.client.table('sessions')\
            .select('*')\
            .eq('id', session_id)\
            .single()\
            .execute()
        
        return result.data
```

### 6. Redis - In-Memory Cache & Real-time Communication

**Purpose**: High-performance caching and pub/sub for agent communication.

**Documentation**: https://redis.io/docs/

**Best Practice Implementation**:

```python
import redis.asyncio as redis
from typing import Optional, Dict, Any
import json

class RedisCache:
    def __init__(self, url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(url, decode_responses=True)
        self.pubsub = self.redis.pubsub()
    
    # Session management
    async def set_session(
        self, 
        session_id: str, 
        data: Dict[str, Any], 
        ttl: int = 3600
    ):
        """Store session data with TTL"""
        await self.redis.setex(
            f"session:{session_id}",
            ttl,
            json.dumps(data)
        )
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data"""
        data = await self.redis.get(f"session:{session_id}")
        return json.loads(data) if data else None
    
    # Agent communication
    async def publish_agent_message(
        self,
        channel: str,
        message: AgentMessage
    ):
        """Publish message to agent channel"""
        await self.redis.publish(
            f"agent:{channel}",
            message.model_dump_json()
        )
    
    async def subscribe_to_agent_channel(
        self,
        agent_id: str,
        callback: Callable
    ):
        """Subscribe to agent-specific channel"""
        await self.pubsub.subscribe(f"agent:{agent_id}")
        
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                await callback(json.loads(message['data']))
    
    # Task queue
    async def enqueue_task(
        self,
        queue: str,
        task: Dict[str, Any]
    ):
        """Add task to processing queue"""
        await self.redis.lpush(
            f"queue:{queue}",
            json.dumps(task)
        )
    
    async def dequeue_task(
        self,
        queue: str,
        timeout: int = 0
    ) -> Optional[Dict]:
        """Get task from queue (blocking)"""
        result = await self.redis.brpop(
            f"queue:{queue}",
            timeout=timeout
        )
        return json.loads(result[1]) if result else None
```

### 7. Logging - Pydantic LogFire

**Purpose**: Structured logging with observability features.

**Documentation**: https://logfire.pydantic.dev/

**Configuration**:

```python
from pydantic_logfire import LogFire, configure_logfire
import contextvars

# Configure LogFire
configure_logfire(
    service_name="presentation-generator",
    environment="production",
    send_to_logfire=True,
    console_log=True,
    log_level="INFO"
)

# Create logger instances
logfire = LogFire()

# Context management for tracing
request_id = contextvars.ContextVar('request_id')

class AgentLogger:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logfire.with_tags(agent=agent_name)
    
    async def log_request(self, request: BaseModel):
        """Log incoming request"""
        self.logger.info(
            "Agent request received",
            request_id=request_id.get(),
            request_type=request.__class__.__name__,
            data=request.model_dump()
        )
    
    async def log_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        tokens: Dict[str, int],
        duration_ms: float
    ):
        """Log LLM API calls"""
        self.logger.info(
            "LLM call completed",
            request_id=request_id.get(),
            model=model,
            prompt_preview=prompt[:100],
            response_preview=response[:100],
            tokens_used=tokens,
            duration_ms=duration_ms,
            cost_estimate=self._calculate_cost(model, tokens)
        )
    
    async def log_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ):
        """Log errors with context"""
        self.logger.error(
            "Agent error occurred",
            request_id=request_id.get(),
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            stack_trace=True
        )

# Usage in agents
class VisualDesignerAgent(Agent):
    def __init__(self):
        super().__init__(name="visual_designer")
        self.logger = AgentLogger("visual_designer")
    
    async def create_visual(self, request: VisualRequest):
        await self.logger.log_request(request)
        
        try:
            # Agent logic here
            result = await self._generate_image(request)
            
            await self.logger.log_llm_call(
                model="dall-e-3",
                prompt=request.prompt,
                response=result.url,
                tokens={"prompt": 50},
                duration_ms=3500
            )
            
            return result
            
        except Exception as e:
            await self.logger.log_error(e, {"request": request.model_dump()})
            raise
```

### 8. Additional Libraries

**Image Generation**:
```python
# OpenAI DALL-E
from openai import AsyncOpenAI

client = AsyncOpenAI()
response = await client.images.generate(
    model="dall-e-3",
    prompt="Modern corporate presentation slide background",
    size="1792x1024",
    quality="hd",
    style="natural"
)

# Stable Diffusion via Replicate
import replicate

output = replicate.run(
    "stability-ai/stable-diffusion-3",
    input={
        "prompt": "Professional presentation chart visualization",
        "negative_prompt": "cartoon, anime, low quality",
        "num_inference_steps": 50
    }
)
```

**Chart Generation**:
```python
# Plotly for interactive charts
import plotly.graph_objects as go
import plotly.io as pio

fig = go.Figure(data=[
    go.Bar(name='Q1', x=['Product A', 'Product B'], y=[20, 14]),
    go.Bar(name='Q2', x=['Product A', 'Product B'], y=[25, 18])
])

# Convert to HTML component
html_div = pio.to_html(fig, div_id="chart_1", include_plotlyjs='cdn')
```

**Diagram Generation**:
```python
# Python Mermaid wrapper
from mermaid import Mermaid

diagram = Mermaid("""
graph LR
    A[Start] --> B{Decision}
    B -->|Yes| C[Process]
    B -->|No| D[End]
    C --> D
""")

svg_output = diagram.render(format='svg')
```

## Development Best Practices

### 1. Code Organization Guidelines

**IMPORTANT: File Size Limits**
- **Maximum file size**: 1000 lines (hard limit)
- **Recommended file size**: 700 lines or less
- **When to refactor**: As soon as a file approaches 700 lines

**Refactoring Strategy**:
```python
# BAD: Single large file (>700 lines)
# agents/director_inbound.py (1200 lines)

# GOOD: Split into logical modules
# agents/director_inbound/
#   ├── __init__.py           # Main agent class (200 lines)
#   ├── clarifications.py     # Question generation logic (250 lines)
#   ├── structure_builder.py  # Structure creation (300 lines)
#   ├── validators.py         # Input validation (150 lines)
#   └── utils.py             # Helper functions (100 lines)
```

**Example Refactoring**:
```python
# agents/director_inbound/__init__.py
"""
Main DirectorInbound agent implementation.
Orchestrates user interaction and presentation structure generation.
"""
from .clarifications import ClarificationGenerator
from .structure_builder import StructureBuilder
from .validators import RequestValidator

class DirectorInboundAgent(Agent):
    """
    Director agent responsible for initial user interaction.
    
    This agent handles:
    - User requirement gathering
    - Clarification questions
    - Initial structure generation
    - Orchestration of downstream agents
    """
    
    def __init__(self):
        # Initialize components
        self.clarification_gen = ClarificationGenerator()
        self.structure_builder = StructureBuilder()
        self.validator = RequestValidator()
        
        super().__init__(
            name="director_inbound",
            model="gpt-4",
            system_prompt=self._load_system_prompt()
        )
    
    async def process_request(self, request: PresentationRequest):
        """
        Main entry point for processing user requests.
        
        Args:
            request: User's presentation request
            
        Returns:
            PresentationStructure or ClarificationRound
        """
        # Validate request completeness
        validation_result = await self.validator.validate(request)
        
        if not validation_result.is_complete:
            # Generate clarification questions
            questions = await self.clarification_gen.generate(
                request, 
                validation_result.missing_info
            )
            return ClarificationRound(questions=questions)
        
        # Build presentation structure
        structure = await self.structure_builder.build(request)
        return structure

# agents/director_inbound/clarifications.py
"""
Clarification question generation for DirectorInbound agent.
Handles dynamic question creation based on missing information.
"""

class ClarificationGenerator:
    """Generates contextual clarification questions"""
    
    def __init__(self):
        self.question_templates = self._load_templates()
    
    async def generate(
        self, 
        request: PresentationRequest,
        missing_info: List[str]
    ) -> List[Question]:
        """
        Generate clarification questions based on missing information.
        
        Args:
            request: Original user request
            missing_info: List of missing information types
            
        Returns:
            List of clarification questions
        """
        questions = []
        
        for info_type in missing_info:
            # Generate contextual question
            question = await self._create_question(
                info_type,
                request.context
            )
            questions.append(question)
            
        return questions
```

### 2. Commenting Best Practices

```python
# Module-level docstring (required for all files)
"""
Visual Designer Agent implementation.

This module handles all visual asset generation including:
- AI-generated images via DALL-E/Stable Diffusion
- Style consistency enforcement
- Asset optimization and storage
"""

# Class-level documentation
class VisualDesignerAgent(Agent):
    """
    Agent responsible for creating visual assets for presentations.
    
    Attributes:
        style_manager: Handles style consistency across assets
        image_generator: Interface to image generation APIs
        asset_store: Manages asset storage and retrieval
    """
    
    # Method documentation
    async def create_visual(
        self, 
        request: VisualRequest,
        style_context: Optional[StyleContext] = None
    ) -> VisualAsset:
        """
        Generate a visual asset based on the request.
        
        This method:
        1. Validates the request parameters
        2. Applies style consistency rules
        3. Generates the image using appropriate AI model
        4. Optimizes and stores the result
        
        Args:
            request: Visual generation request with requirements
            style_context: Optional style context for consistency
            
        Returns:
            VisualAsset containing the generated image and metadata
            
        Raises:
            VisualGenerationError: If image generation fails
            StyleValidationError: If style requirements conflict
        """
        # Inline comments for complex logic
        # Apply style inheritance from presentation theme
        final_style = self.style_manager.merge_styles(
            base_style=style_context,
            request_style=request.style_requirements
        )
        
        # Generate image with retry logic
        # Note: DALL-E has rate limits, so we implement exponential backoff
        for attempt in range(self.max_retries):
            try:
                result = await self._generate_with_model(
                    prompt=request.prompt,
                    style=final_style,
                    model=self._select_model(request)
                )
                break
            except RateLimitError as e:
                # Exponential backoff: 2^attempt seconds
                await asyncio.sleep(2 ** attempt)
                if attempt == self.max_retries - 1:
                    raise
        
        # Post-process and store
        optimized = await self._optimize_image(result)
        stored_asset = await self.asset_store.store(optimized)
        
        return stored_asset

    # Complex algorithm documentation
    def _select_model(self, request: VisualRequest) -> str:
        """
        Select the appropriate image generation model.
        
        Selection criteria:
        - Photorealistic images: DALL-E 3
        - Artistic/stylized: Stable Diffusion
        - Diagrams/icons: DALL-E 2 (faster, cheaper)
        - Budget constraints: Stable Diffusion
        
        The selection algorithm considers:
        1. Image type requirements
        2. Quality requirements
        3. Budget constraints
        4. Current API availability
        """
        # Implementation details...
```

### 3. Project Structure

```
presentation-generator/
├── agents/
│   ├── __init__.py
│   ├── base.py              # Base agent class (<200 lines)
│   ├── director_inbound/    # Refactored large agent
│   │   ├── __init__.py     # Main class (<300 lines)
│   │   ├── clarifications.py
│   │   ├── structure_builder.py
│   │   └── validators.py
│   ├── director_outbound.py # Simple agent (<700 lines)
│   ├── ux_architect/       # Another refactored agent
│   │   ├── __init__.py
│   │   ├── layout_engine.py
│   │   └── grid_systems.py
│   ├── researcher.py       # Simple agent (<700 lines)
│   ├── visual_designer/    # Complex agent refactored
│   │   ├── __init__.py
│   │   ├── image_generation.py
│   │   ├── style_manager.py
│   │   └── optimization.py
│   ├── data_analyst.py
│   └── ux_analyst.py
├── models/
│   ├── __init__.py
│   ├── communication.py     # Pydantic models (<500 lines)
│   ├── presentation.py      # Split if grows too large
│   └── agents.py
├── workflows/
│   ├── __init__.py
│   ├── main_workflow.py    # Primary workflow (<600 lines)
│   ├── refinement.py       # Iteration workflow
│   └── error_handling.py
├── storage/
│   ├── __init__.py
│   ├── supabase.py        # Database operations (<500 lines)
│   ├── redis.py           # Cache operations (<400 lines)
│   └── migrations/
├── api/
│   ├── __init__.py
│   ├── websocket/         # WebSocket split into modules
│   │   ├── __init__.py
│   │   ├── handlers.py
│   │   ├── message_processor.py
│   │   └── session_manager.py
│   ├── rest.py
│   └── middleware.py
├── utils/
│   ├── __init__.py
│   ├── embeddings.py      # Vector generation (<300 lines)
│   ├── mcp_clients.py     # MCP connections (<400 lines)
│   └── logging.py         # LogFire setup (<200 lines)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config/
│   ├── settings.py
│   └── prompts/
├── requirements.txt
├── docker-compose.yml
└── README.md
```

### 4. Environment Variables
```bash
# .env.example
# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
REDIS_URL=redis://localhost:6379

# AI Models
OPENAI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
REPLICATE_API_TOKEN=xxx

# MCP Servers
BRAVE_API_KEY=xxx
GITHUB_TOKEN=xxx

# Logging
LOGFIRE_TOKEN=xxx
LOGFIRE_PROJECT=presentation-generator

# Application
APP_ENV=development
APP_SECRET_KEY=xxx
WEBSOCKET_PORT=8000
API_PORT=8001
```

### 5. Testing Strategy

```python
# tests/unit/test_models.py
"""Unit tests for Pydantic models"""
import pytest
from pydantic import ValidationError
from models.presentation import SlideStructure, ComponentSpec

def test_slide_structure_validation():
    """Test slide structure validation rules"""
    # Valid slide
    slide = SlideStructure(
        slide_id="slide_1",
        slide_number=1,
        title="Test Slide",
        layout_type="hero",
        components=[]
    )
    assert slide.slide_id == "slide_1"
    
    # Invalid slide_id format
    with pytest.raises(ValidationError):
        SlideStructure(
            slide_id="invalid",
            slide_number=1,
            title="Test",
            layout_type="hero",
            components=[]
        )

# tests/integration/test_agents.py
"""Integration tests for agent functionality"""
import pytest
from agents.director_inbound import DirectorInboundAgent
from models.communication import PresentationRequest

@pytest.mark.asyncio
async def test_director_processes_request():
    """Test director agent request processing"""
    agent = DirectorInboundAgent()
    request = PresentationRequest(
        session_id="test_123",
        topic="Q4 Financial Results",
        presentation_type="executive_summary"
    )
    
    result = await agent.process_request(request)
    
    assert result.status == "completed"
    assert len(result.slides) > 0
    assert result.slides[0].title is not None
```

### 6. Deployment Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - APP_ENV=production
    depends_on:
      - redis
      - postgres
    volumes:
      - ./data:/app/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_DB: presentations
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./storage/migrations:/docker-entrypoint-initdb.d
  
  mcp_brave:
    image: modelcontextprotocol/brave-search:latest
    environment:
      - BRAVE_API_KEY=${BRAVE_API_KEY}
    ports:
      - "8002:8002"

volumes:
  redis_data:
  postgres_data:
```

## Quick Start Guide

1. **Clone and Setup**:
```bash
git clone <repository>
cd presentation-generator
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Initialize Database**:
```bash
# Run Supabase migrations
supabase db reset
supabase db push

# Or use Docker
docker-compose up -d postgres
docker exec -it postgres psql -U admin -d presentations -f /migrations/init.sql
```

4. **Start Services**:
```bash
# Development
python -m uvicorn api.websocket:app --reload --port 8000

# Production
docker-compose up -d
```

5. **Run Tests**:
```bash
pytest tests/unit -v
pytest tests/integration -v --asyncio-mode=auto
```

## Code Quality Checklist

Before committing code, ensure:

1. **File Size**: No file exceeds 700 lines (1000 absolute max)
2. **Documentation**: All modules, classes, and complex methods have docstrings
3. **Comments**: Complex logic is explained with inline comments
4. **Type Hints**: All functions have proper type annotations
5. **Tests**: New functionality includes unit tests
6. **Formatting**: Code follows PEP 8 standards

This technology stack provides a robust, scalable foundation for building the presentation generation system with clear separation of concerns, type safety, excellent observability, and maintainable code structure.