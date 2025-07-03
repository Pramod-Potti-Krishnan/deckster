# PRD Phase 2: Director Coordination with UX Architect and Researcher

## References
- [PRD v4.0](./PRD_v4.0.md) - Main product requirements document
- [Communication Protocols](./comms_protocol.md) - Detailed JSON message templates and protocols
- [Technology Stack](./tech_stack.md) - Framework specifications and implementation guidelines
- [Security Requirements](./security.md) - MVP security implementation guidelines
- [Folder Structure](./folder_structure.md) - Project organization and file placement guide

## FEATURE:
Director (Inbound) orchestrates collaboration between UX Architect (specializing in layouts) and Researcher agents to build comprehensive presentation content and structure, with Director (Outbound) producing the first version with placeholders.

## EXAMPLES:
- Director (Inbound) passes requirements to UX Architect: `{"type": "layout_request", "slides": [...], "style": "modern"}`
- UX Architect returns: `{"layouts": [{"slide_id": "1", "grid": "2x2", "components": [...]}]}`
- Researcher receives: `{"type": "content_request", "topics": ["market analysis", "competitor data"]}`
- Director (Outbound) assembles: `{"type": "draft_presentation", "slides": [...], "placeholders": ["image_1", "chart_2"]}`

## DOCUMENTATION:
- **Agent Framework**: Pydantic AI Agent Module for all agents
- **Orchestration**: LangGraph for multi-agent workflows
- **Data Models**: Pydantic BaseModel for inter-agent communication
- **Logging**: Pydantic LogFire for agent interaction tracking
- **MCP Server**: Research tools, layout templates, content libraries
- **Communication**: JSON protocol with HTML-embedded layouts

## KEY COMPONENTS:

### 1. Multi-Agent Architecture
- **Agent Definitions** (Pydantic AI):
  ```python
  class UXArchitectAgent(Agent):
      name = "ux_architect"
      description = "Specializes in presentation layouts and visual structure"
      
      async def design_layout(self, requirements: LayoutRequest) -> LayoutDesign:
          # Access layout templates from MCP
          # Generate responsive grid systems
          # Return Pydantic-validated layouts
  
  class ResearcherAgent(Agent):
      name = "researcher"
      description = "Gathers and structures content for presentations"
      
      async def research_content(self, topics: ContentRequest) -> ResearchOutput:
          # Utilize MCP research tools
          # Structure findings
          # Return validated content blocks
  ```

### 2. LangGraph Orchestration
```python
from langgraph import Graph, StateGraph

# Phase 2 workflow
phase2_workflow = StateGraph()
phase2_workflow.add_node("director_inbound", director_processor)
phase2_workflow.add_node("ux_architect", layout_designer)
phase2_workflow.add_node("researcher", content_researcher)
phase2_workflow.add_node("director_outbound", presentation_assembler)

# Define edges and conditions
phase2_workflow.add_edge("director_inbound", "ux_architect")
phase2_workflow.add_edge("director_inbound", "researcher")
phase2_workflow.add_conditional_edges(
    "ux_architect",
    lambda x: "director_outbound" if x.complete else "director_inbound"
)
```

### 3. Data Models (Pydantic BaseModel)
```python
class LayoutRequest(BaseModel):
    session_id: str
    slide_count: int
    presentation_type: str
    style_preferences: Dict[str, Any]
    content_hints: List[str]

class LayoutDesign(BaseModel):
    slide_layouts: List[SlideLayout]
    global_theme: ThemeConfig
    responsive_breakpoints: List[int]
    
class SlideLayout(BaseModel):
    slide_id: str
    grid_system: str  # "2x2", "1x3", "hero", etc.
    components: List[LayoutComponent]
    html_template: str  # HTML string for layout
    
class ResearchOutput(BaseModel):
    topic_id: str
    content_blocks: List[ContentBlock]
    sources: List[Source]
    relevance_score: float
    
class ContentBlock(BaseModel):
    id: str
    type: Literal['text', 'bullet_points', 'quote', 'statistic']
    content: str
    metadata: Dict[str, Any]
```

### 4. Director (Outbound) Integration
```python
class DirectorOutboundAgent(Agent):
    name = "director_outbound"
    description = "Assembles final presentation from agent outputs"
    
    async def assemble_presentation(
        self, 
        layouts: LayoutDesign,
        content: List[ResearchOutput],
        structure: PresentationStructure
    ) -> DraftPresentation:
        # Merge layouts with content
        # Insert placeholders for Phase 3 agents
        # Generate complete JSON with HTML
```

## OTHER CONSIDERATIONS:

### Agent Communication Protocol
- **Standardized Messages**:
  ```json
  {
    "from_agent": "director_inbound",
    "to_agent": "ux_architect",
    "message_type": "layout_request",
    "correlation_id": "session_123_req_456",
    "payload": {
      "requirements": {...},
      "constraints": {...}
    },
    "timestamp": "2024-01-01T00:00:00Z"
  }
  ```

### MCP Server Utilization
- **UX Architect Tools**:
  - Layout template library
  - Grid system generators
  - Theme builders
- **Researcher Tools**:
  - Web search integration
  - Document parsing
  - Knowledge base queries
  - Citation management

### Parallel Processing
- UX Architect and Researcher work concurrently
- Director (Inbound) manages dependencies
- Async/await patterns for efficiency
- Result aggregation by Director (Outbound)

### Placeholder System
```python
class Placeholder(BaseModel):
    id: str
    type: Literal['image', 'chart', 'diagram', 'animation']
    requirements: Dict[str, Any]
    fallback_content: Optional[str]
    position: LayoutPosition
```

### Memory Management

#### Short-term Memory (Contextual)
- **Agent Working Memory**: Redis + Supabase hybrid
  ```python
  class AgentContext(BaseModel):
      agent_id: str
      session_id: str
      current_task: Dict[str, Any]
      intermediate_results: List[Any]
      dependencies: Dict[str, Any]  # Results from other agents
  ```
- **Inter-Agent Communication Cache**:
  - Redis pub/sub for real-time agent messages
  - Supabase for persistent message history
  - Task queue in Redis for agent coordination
- **Layout/Content Drafts**:
  - Redis for active work-in-progress
  - Supabase for completed components
  - Automatic migration after task completion

#### Long-term Memory (Tools & Knowledge)
- **Layout Library** (Supabase):
  ```python
  class LayoutLibrary:
      async def store_successful_layout(self, layout: SlideLayout):
          # Store with vector embedding for similarity search
          await supabase.table('layout_templates').insert({
              'layout_type': layout.grid_system,
              'embedding': await generate_layout_embedding(layout),
              'usage_count': 0,
              'success_rate': 0.0,
              'metadata': layout.dict()
          })
          
      async def find_best_layouts(self, context: LayoutRequest) -> List[SlideLayout]:
          # Combine vector search with usage statistics
          return await supabase.rpc('find_optimal_layouts', {
              'context_embedding': await generate_context_embedding(context),
              'presentation_type': context.presentation_type,
              'limit': 10
          })
  ```
- **Research Knowledge Base**:
  - Supabase vector storage for research findings
  - Cached search results with expiry
  - Domain-specific knowledge graphs
  - Citation database with credibility scores
- **Agent Learning**:
  - Track successful agent collaborations
  - Store effective prompt patterns
  - Build style preference models

### Performance Requirements
- Layout generation: <3s per slide
- Content research: <5s per topic
- Assembly time: <2s for 20-slide deck
- Parallel agent execution

### Development Priorities
1. Implement UX Architect with layout engine
2. Build Researcher with MCP tool integration
3. Create Director (Outbound) assembly logic
4. Setup LangGraph workflow orchestration
5. Implement placeholder system
6. Add comprehensive LogFire logging
7. Build integration tests for agent communication

### Success Metrics
- Layout quality score: >85%
- Content relevance: >80%
- Placeholder accuracy: >90%
- Agent coordination efficiency: <10s total