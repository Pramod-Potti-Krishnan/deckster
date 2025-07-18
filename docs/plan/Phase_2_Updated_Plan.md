# Phase 2 Implementation Plan: Parallel Agent Architecture with Layout/UX Architect

## Executive Summary

This document outlines the implementation plan for Phase 2 of Deckster, introducing a parallel agent architecture with the Layout/UX Architect as the first specialist agent. This phase establishes the foundation for multi-agent collaboration where multiple specialist agents work in parallel after strawman approval, with Director OUT assembling their outputs progressively.

## Table of Contents

1. [Overview](#overview)
2. [Workflow Architecture](#workflow-architecture)
3. [Parallel Agent System Design](#parallel-agent-system-design)
4. [Layout Architect Agent](#layout-architect-agent)
5. [Director OUT Assembler](#director-out-assembler)
6. [Data Models](#data-models)
7. [Integration Strategy](#integration-strategy)
8. [Implementation Phases](#implementation-phases)
9. [Technical Specifications](#technical-specifications)
10. [Testing Strategy](#testing-strategy)
11. [Success Metrics](#success-metrics)

## Overview

### Paradigm Shift: Sequential to Parallel

Phase 2 marks a fundamental shift in Deckster's architecture:

- **Phase 1**: Sequential state machine (States 1-5)
- **Phase 2**: Introduction of parallel agent execution
- **Phase 3**: Full multi-agent system with 5 parallel specialists

### Key Architectural Changes

1. **Parallel Execution**: After strawman approval, multiple agents work concurrently
2. **Progressive Assembly**: Director OUT assembles content as it arrives
3. **Slide-by-Slide Delivery**: Frontend receives updates progressively
4. **Targeted Refinements**: User feedback routes to specific agents

### Phase 2 Focus

While the architecture supports multiple parallel agents, Phase 2 focuses on:

- Implementing the Layout/UX Architect as the first parallel agent
- Building Director OUT assembler infrastructure
- Establishing slide-by-slide delivery protocol
- Creating foundation for Phase 3 agents

## Workflow Architecture

### Complete Workflow States and Nodes

```
Sequential States (1-5):
┌─────────────────┐
│ 1. PROVIDE      │
│    GREETING     │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 2. ASK          │
│    CLARIFYING   │
│    QUESTIONS    │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 3. CREATE       │
│    CONFIRMATION │
│    PLAN         │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 4. GENERATE     │
│    STRAWMAN     │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 5. REFINE       │
│    STRAWMAN     │
└────────┬────────┘
         ↓
    [User Accepts]
         ↓
Parallel Execution:
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ 6. ARCHITECT │  │ 7. RESEARCH  │  │ 8. BUILD │ │
│  │    LAYOUT    │  │    CONTENT   │  │   CHARTS │ │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘ │
│         │                  │                │       │
│  ┌──────────────┐  ┌──────────────┐        │       │
│  │ 9. IMAGINE   │  │ 10. DRAW     │        │       │
│  │    VISUALS   │  │    FRAMEWORKS│        │       │
│  └──────┬───────┘  └──────┬───────┘        │       │
│         │                  │                │       │
└─────────┼──────────────────┼────────────────┼───────┘
          ↓                  ↓                ↓
      [Slide-by-slide content delivery]
          ↓                  ↓                ↓
┌─────────────────────────────────────────────────────┐
│              DIRECTOR OUT (Assembler)               │
│  - Receives content progressively                   │
│  - Assembles slides as content arrives             │
│  - Sends updates to frontend immediately           │
└─────────────────────────────────────────────────────┘
                         ↓
                    [Frontend]
```

### LangGraph Implementation Strategy

```python
# Parallel node configuration
parallel_nodes = {
    "layout_architect": LayoutArchitectNode(),      # Phase 2
    "researcher": ResearcherNode(),                 # Phase 3
    "visual_designer": VisualDesignerNode(),        # Phase 3
    "data_analyst": DataAnalystNode(),              # Phase 3
    "ux_analyst": UXAnalystNode()                   # Phase 3
}

# Director OUT as continuous processor
director_out = DirectorOutNode(
    assembly_strategy="progressive",
    delivery_mode="slide_by_slide"
)

```

## Parallel Agent System Design

### Key Principles

1. **Independent Execution**: Each agent works autonomously on the strawman
2. **Slide-Level Granularity**: Agents process and deliver content per slide
3. **Asynchronous Communication**: No agent waits for another
4. **Progressive Enhancement**: Slides improve as more agents contribute

### Agent Communication Protocol

```python
@dataclass
class AgentMessage:
    """Standard message format for agent communication"""
    agent_id: str
    slide_id: str
    content_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    completion_status: Literal["partial", "complete", "error"]

# Example: Layout Architect sends layout for slide 1
message = AgentMessage(
    agent_id="layout_architect",
    slide_id="slide_001",
    content_type="layout_specification",
    payload={
        "layout": "dataSlide",
        "layout_spec": {...}
    },
    timestamp=datetime.utcnow(),
    completion_status="complete"
)
```

### LangGraph Parallel Node Implementation

```python
from langgraph import Graph, StateGraph
from typing import TypedDict, List

class PresentationState(TypedDict):
    """Shared state for all agents"""
    strawman: PresentationStrawman
    agent_outputs: Dict[str, List[AgentMessage]]
    assembled_slides: Dict[str, SlideData]
    delivery_queue: List[str]

# Create parallel workflow
workflow = StateGraph(PresentationState)

# Add sequential states (existing)
workflow.add_node("provide_greeting", provide_greeting)
workflow.add_node("ask_questions", ask_questions)
workflow.add_node("create_plan", create_plan)
workflow.add_node("generate_strawman", generate_strawman)
workflow.add_node("refine_strawman", refine_strawman)

# Add parallel nodes (new)
workflow.add_node("layout_architect", layout_architect_node)
workflow.add_node("researcher", researcher_node)  # Phase 3
workflow.add_node("visual_designer", visual_designer_node)  # Phase 3
workflow.add_node("data_analyst", data_analyst_node)  # Phase 3
workflow.add_node("ux_analyst", ux_analyst_node)  # Phase 3

# Add assembler
workflow.add_node("director_out", director_out_assembler)

# Define edges
workflow.add_edge("refine_strawman", "layout_architect")
workflow.add_edge("refine_strawman", "researcher")
workflow.add_edge("refine_strawman", "visual_designer")
workflow.add_edge("refine_strawman", "data_analyst")
workflow.add_edge("refine_strawman", "ux_analyst")

# All parallel nodes feed into director_out
for node in ["layout_architect", "researcher", "visual_designer", "data_analyst", "ux_analyst"]:
    workflow.add_edge(node, "director_out")
```

## Layout Architect Agent

### Agent Design

```python
# src/agents/layout_architect.py

class LayoutArchitectAgent:
    """
    First parallel agent - transforms content into visual layouts.
    Processes slides independently and sends results progressively.
    """
    
    def __init__(self):
        # Initialize with PydanticAI
        self.agent = Agent(
            model=model,
            output_type=SlideLayoutSpec,  # Per-slide output
            system_prompt=self._load_modular_prompt("ENHANCE_LAYOUT"),
            name="layout_architect"
        )
        
        # Communication channel to Director OUT
        self.message_queue = MessageQueue("layout_architect")
        
        # Layout variety tracker
        self.layout_history = []
        
    async def process_strawman(self, strawman: PresentationStrawman) -> None:
        """
        Process entire strawman, sending layouts slide-by-slide.
        """
        # Process slides concurrently
        tasks = []
        for slide in strawman.slides:
            task = asyncio.create_task(
                self._process_slide(slide, strawman)
            )
            tasks.append(task)
        
        # Wait for all slides to complete
        await asyncio.gather(*tasks)
        
    async def _process_slide(
        self, 
        slide: Slide,
        context: PresentationStrawman
    ) -> None:
        """
        Process individual slide and send to Director OUT.
        """
        try:
            # Generate layout for this slide
            layout_spec = await self._generate_layout_spec(slide, context)
            
            # Send to Director OUT immediately
            message = AgentMessage(
                agent_id="layout_architect",
                slide_id=slide.slide_id,
                content_type="layout_specification",
                payload={
                    "layout": layout_spec.layout,
                    "layout_spec": layout_spec.dict()
                },
                timestamp=datetime.utcnow(),
                completion_status="complete"
            )
            
            await self.message_queue.send(message)
            logger.info(f"Layout sent for slide {slide.slide_id}")
            
        except Exception as e:
            # Send error message
            error_message = AgentMessage(
                agent_id="layout_architect",
                slide_id=slide.slide_id,
                content_type="layout_specification",
                payload={"error": str(e)},
                timestamp=datetime.utcnow(),
                completion_status="error"
            )
            await self.message_queue.send(error_message)
```

### Slide-by-Slide Processing

The Layout Architect processes each slide independently, enabling:

1. **Parallel Slide Processing**: Multiple slides processed concurrently
2. **Immediate Delivery**: Each layout sent as soon as ready
3. **No Dependencies**: Each slide's layout is self-contained
4. **Error Isolation**: One slide's failure doesn't affect others

## Director OUT Assembler

### Core Design

```python
# src/agents/director_out.py

class DirectorOutAssembler:
    """
    Assembles content from parallel agents and delivers to frontend.
    Runs continuously, not as a final state.
    """
    
    def __init__(self):
        # Message queues from all agents
        self.agent_queues = {
            "layout_architect": MessageQueue("layout_architect"),
            "researcher": MessageQueue("researcher"),
            "visual_designer": MessageQueue("visual_designer"),
            "data_analyst": MessageQueue("data_analyst"),
            "ux_analyst": MessageQueue("ux_analyst")
        }
        
        # Slide assembly state
        self.slide_states = {}  # slide_id -> assembled content
        self.delivery_tracker = DeliveryTracker()
        
    async def run_assembly_loop(self, session_id: str, websocket: WebSocket):
        """
        Continuous loop receiving and assembling content.
        """
        # Start listening to all agent queues
        tasks = []
        for agent_id, queue in self.agent_queues.items():
            task = asyncio.create_task(
                self._process_agent_messages(agent_id, queue, session_id, websocket)
            )
            tasks.append(task)
        
        # Run until all agents complete
        await asyncio.gather(*tasks)
    
    async def _process_agent_messages(
        self, 
        agent_id: str, 
        queue: MessageQueue,
        session_id: str,
        websocket: WebSocket
    ):
        """
        Process messages from a specific agent.
        """
        async for message in queue.receive():
            # Update slide state
            slide_id = message.slide_id
            if slide_id not in self.slide_states:
                self.slide_states[slide_id] = SlideAssemblyState()
            
            # Add agent's contribution
            self.slide_states[slide_id].add_content(
                agent_id, 
                message.content_type,
                message.payload
            )
            
            # Check if slide ready to send
            if self._should_send_update(slide_id):
                await self._send_slide_update(
                    websocket, 
                    session_id, 
                    slide_id
                )
    
    def _should_send_update(self, slide_id: str) -> bool:
        """
        Determine if slide has enough content to send update.
        Phase 2: Send when layout is ready
        Phase 3: More sophisticated logic
        """
        state = self.slide_states[slide_id]
        
        # Phase 2: Send when we have layout
        if "layout_architect" in state.contributors:
            return not state.last_sent or state.has_new_content()
        
        return False
    
    async def _send_slide_update(
        self, 
        websocket: WebSocket,
        session_id: str,
        slide_id: str
    ):
        """
        Send progressive slide update to frontend.
        """
        state = self.slide_states[slide_id]
        
        # Assemble current slide data
        slide_data = self._assemble_slide(slide_id, state)
        
        # Create slide update message
        update = create_slide_update(
            session_id=session_id,
            operation="partial_update",
            metadata={...},  # From strawman
            slides=[slide_data],
            affected_slides=[slide_id]
        )
        
        # Send to frontend
        await websocket.send_json(update.dict())
        state.mark_sent()
```

### Assembly Strategy

```python
def _assemble_slide(self, slide_id: str, state: SlideAssemblyState) -> Dict:
    """
    Merge contributions from different agents.
    """
    # Start with base slide from strawman
    slide = state.base_slide.dict()
    
    # Apply layout (Phase 2)
    if layout := state.get_content("layout_architect", "layout_specification"):
        slide["layout"] = layout["layout"]
        slide["layout_spec"] = layout["layout_spec"]
    
    # Apply research content (Phase 3)
    if content := state.get_content("researcher", "content"):
        slide["enhanced_content"] = content
    
    # Apply visuals (Phase 3)
    if visuals := state.get_content("visual_designer", "visuals"):
        slide["visual_assets"] = visuals
    
    # Apply analytics (Phase 3)
    if charts := state.get_content("data_analyst", "charts"):
        slide["data_visualizations"] = charts
    
    # Apply diagrams (Phase 3)
    if diagrams := state.get_content("ux_analyst", "diagrams"):
        slide["diagrams"] = diagrams
    
    return slide
```

## Data Models

### New Models

```python
# src/models/layout.py

from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

class GridPosition(BaseModel):
    """Position using grid units."""
    leftInset: Optional[int] = None
    rightInset: Optional[int] = None
    topInset: Optional[int] = None
    bottomInset: Optional[int] = None
    xCenterOffset: Optional[int] = None
    yCenterOffset: Optional[int] = None
    width: int = Field(ge=1, le=160)
    height: int = Field(ge=1, le=90)

class ContainerSpec(BaseModel):
    """Container specification for layout."""
    name: str
    position: GridPosition
    content_ref: Optional[str] = None
    layout_role: Literal["primary", "secondary", "tertiary"]
    z_index: Optional[int] = Field(default=1, ge=1, le=10)
    padding: Optional[Dict[str, int]] = None
    background: Optional[str] = None

class LayoutHints(BaseModel):
    """Hints for frontend rendering."""
    content_density: Literal["high", "medium", "low"]
    visual_emphasis: float = Field(ge=0.0, le=1.0)
    preferred_flow: Literal["vertical", "horizontal", "grid"]
    color_intensity: Literal["muted", "balanced", "vibrant"] = "balanced"
    spacing_preference: Literal["compact", "balanced", "airy"] = "balanced"

class LayoutSpecification(BaseModel):
    """Complete layout specification for a slide."""
    source: Literal["theme", "custom"]
    theme_layout: Optional[str] = None
    custom_containers: Optional[List[ContainerSpec]] = None
    layout_hints: LayoutHints
    
class EnhancedSlide(Slide):
    """Slide with layout specifications."""
    layout: str  # Theme layout name
    layout_spec: LayoutSpecification

class LayoutEnhancedStrawman(PresentationStrawman):
    """Strawman with layout-enhanced slides."""
    slides: List[EnhancedSlide]
```

### Extended WebSocket Models

```python
# Addition to src/models/websocket_messages.py

class EnhancedSlideData(SlideData):
    """Slide data with layout specifications."""
    layout: str
    layout_spec: Dict[str, Any]  # LayoutSpecification as dict
```

## Integration Strategy

### 1. Context Builder Extension

```python
# src/utils/context_builder.py additions

class EnhanceLayoutStrategy(StateContextStrategy):
    """ENHANCE_LAYOUT needs strawman + theme config"""
    
    def build_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "presentation_strawman": session_data.get("presentation_strawman", {}),
            "theme_preferences": session_data.get("theme_preferences", {}),
            "target_audience": session_data.get("target_audience", "")
        }
    
    def get_required_fields(self) -> List[str]:
        return ["presentation_strawman"]
```

### 2. Workflow Integration

```python
# src/handlers/websocket.py modifications

async def _handle_generate_strawman(self, session_id: str, manager: SessionManager):
    # Existing strawman generation
    strawman = await self.director.process(state_context)
    
    # NEW: Enhance with layout
    if strawman and isinstance(strawman, PresentationStrawman):
        # Initialize Layout Architect
        layout_architect = LayoutArchitectAgent()
        
        # Enhance strawman with layouts
        enhanced_strawman = await layout_architect.enhance_layout(
            strawman,
            theme_config=session_data.get("theme_config")
        )
        
        # Update session with enhanced strawman
        await manager.update_session(
            session_id,
            presentation_strawman=enhanced_strawman.dict()
        )
        
        # Send enhanced slides to frontend
        await self._send_enhanced_slides(websocket, session_id, enhanced_strawman)
```

### 3. Storage Extensions

```python
# src/storage/layout_store.py (new file)

class LayoutStore:
    """Storage for layout templates and patterns."""
    
    def __init__(self):
        self.supabase = SupabaseOperations()
        self.layout_table = "layout_templates"
        self.pattern_table = "layout_patterns"
    
    async def store_successful_layout(
        self, 
        layout: LayoutSpecification,
        slide_type: str,
        effectiveness_score: float
    ):
        """Store successful layout for future reference."""
        # Implementation for storing effective layouts
    
    async def get_layout_suggestions(
        self,
        slide_type: str,
        content_characteristics: Dict[str, Any]
    ) -> List[LayoutSpecification]:
        """Retrieve suitable layouts based on content."""
        # Implementation for retrieving layout suggestions
```

## Implementation Phases

### Phase 2.1: Basic Layout Mapping (Week 1-2)

1. Implement `LayoutArchitectAgent` class
2. Create basic theme layout mappings
3. Integrate with existing workflow
4. Update WebSocket messages

**Deliverables:**
- Working Layout Architect with theme-based layouts
- Updated slide data structure
- Basic integration tests

### Phase 2.2: Custom Container Generation (Week 3-4)

1. Implement container generation logic
2. Add content analysis capabilities
3. Create layout variety tracking
4. Implement layout hints system

**Deliverables:**
- Custom container generation
- Content-aware layout selection
- Variety management system

### Phase 2.3: Intelligence Enhancement (Week 5-6)

1. Add layout pattern learning
2. Implement A/B testing framework
3. Create layout effectiveness metrics
4. Build feedback integration

**Deliverables:**
- Learning system for layouts
- Metrics dashboard
- Feedback loop implementation

## Technical Specifications

### Performance Requirements

- Layout generation: <2s per slide
- Memory usage: <50MB per session
- Concurrent sessions: 100+
- Layout variety: >80% unique layouts in 20-slide deck

### API Specifications

#### Layout Architect Input

```json
{
  "strawman": {
    "main_title": "...",
    "slides": [...]
  },
  "theme_config": {
    "name": "corporate",
    "primary_color": "#0066cc"
  },
  "preferences": {
    "formality": "professional",
    "visual_density": "balanced"
  }
}
```

#### Layout Architect Output

```json
{
  "slides": [{
    "slide_id": "slide_001",
    "layout": "titleSlide",
    "layout_spec": {
      "source": "theme",
      "layout_hints": {
        "content_density": "low",
        "visual_emphasis": 0.8
      }
    }
  }]
}
```

### Error Handling

```python
class LayoutGenerationError(Exception):
    """Raised when layout generation fails."""
    pass

class LayoutMappingError(Exception):
    """Raised when theme layout mapping fails."""
    pass

# Fallback strategy
async def generate_safe_fallback_layout(slide: Slide) -> LayoutSpecification:
    """Generate safe, generic layout as fallback."""
    return LayoutSpecification(
        source="theme",
        theme_layout="contentSlide",
        layout_hints=LayoutHints(
            content_density="medium",
            visual_emphasis=0.5,
            preferred_flow="vertical"
        )
    )
```

## Testing Strategy

### Unit Tests

```python
# test/test_layout_architect.py

async def test_theme_layout_mapping():
    """Test correct mapping of slide types to theme layouts."""
    
async def test_custom_container_generation():
    """Test custom container generation for complex slides."""
    
async def test_layout_variety():
    """Test that layout variety is maintained."""
    
async def test_content_analysis():
    """Test content density and complexity analysis."""
```

### Integration Tests

```python
# test/test_layout_integration.py

async def test_director_to_layout_flow():
    """Test complete flow from Director to Layout Architect."""
    
async def test_websocket_enhanced_slides():
    """Test WebSocket delivery of enhanced slides."""
    
async def test_error_recovery():
    """Test graceful fallback on layout generation errors."""
```

### Performance Tests

- Layout generation speed under load
- Memory usage with concurrent sessions
- Layout variety metrics
- Cache effectiveness

## Success Metrics

### Technical Metrics

1. **Performance**
   - 95% of layouts generated in <2s
   - Zero layout generation failures in production
   - <50MB memory per session

2. **Quality**
   - >80% layout variety in presentations
   - <5% custom container generation failures
   - 100% valid grid positions

3. **Integration**
   - Zero regression in existing functionality
   - Seamless WebSocket message delivery
   - Backward compatibility maintained

### Business Metrics

1. **User Satisfaction**
   - Improved visual appeal ratings
   - Reduced manual layout adjustments
   - Faster presentation creation time

2. **Adoption**
   - >90% of presentations use Layout Architect
   - Positive feedback on layout variety
   - Reduced support tickets for layout issues

### Development Metrics

1. **Code Quality**
   - >90% test coverage
   - Zero critical bugs in production
   - Clear documentation and examples

2. **Maintainability**
   - Modular design for easy updates
   - Clear separation of concerns
   - Comprehensive logging and monitoring

## Next Steps

1. **Immediate Actions**
   - Set up development environment
   - Create layout_architect.py structure
   - Write modular prompts
   - Begin unit test development

2. **Week 1 Goals**
   - Complete basic Layout Architect implementation
   - Integrate with existing Director workflow
   - Deploy to development environment

3. **Feedback Loop**
   - Weekly reviews with frontend team
   - Iterative improvements based on testing
   - Performance optimization as needed

## Conclusion

The Layout/UX Architect agent represents a crucial enhancement to Deckster's capabilities, bridging the gap between content strategy and visual execution. By following this implementation plan, we can deliver an intelligent layout system that ensures every presentation is both content-rich and visually compelling.

The modular design allows for incremental development and testing, ensuring stability while adding powerful new capabilities. The focus on variety, intelligence, and user satisfaction will differentiate Deckster from competitors and provide genuine value to users.