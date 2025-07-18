# Best Practices for Building Agents with LangGraph and Pydantic

Combining LangGraph's stateful orchestration with Pydantic's data validation is the most effective way to build reliable and maintainable AI agents. This guide outlines the core best practices for integrating these two powerful libraries, with specific focus on Deckster's Phase 2 parallel agent architecture.

## Table of Contents

1. [Core Philosophy](#core-philosophy)
2. [Use Pydantic BaseModel for Graph State](#1-use-a-pydantic-basemodel-for-your-graphs-state)
3. [Define Tool Inputs with Pydantic](#2-define-tool-inputs-with-pydantic)
4. [Enforce Structured Output from LLMs](#3-enforce-structured-output-from-llms-with-pydantic)
5. [Use Specialized Pydantic Agents as Nodes](#4-use-specialized-pydantic-agents-as-nodes)
6. [Practice Immutable State Updates](#5-practice-immutable-state-updates)
7. [Advanced Patterns for Parallel Agents](#6-advanced-patterns-for-parallel-agents)
8. [Testing and Debugging](#7-testing-and-debugging)
9. [Performance Optimization](#8-performance-optimization)
10. [Migration Strategy](#9-migration-strategy)

## Core Philosophy

- **Pydantic defines the structure of your data.** It's the blueprint for your agent's state, tool inputs, and LLM outputs.
- **LangGraph defines the flow of your logic.** It's the engine that directs how the state evolves through various nodes and edges.

## 1. Use a Pydantic BaseModel for Your Graph's State

This is the most critical best practice. Instead of using a simple Python dict or TypedDict for your state, define it with a Pydantic BaseModel.

### Why:

- **Automatic Validation**: LangGraph will automatically validate the entire state object against your Pydantic model before every node execution. This catches errors early and prevents corrupted data from propagating through your graph.
- **Type Coercion**: Pydantic intelligently coerces data types. If an LLM returns a number as a string ("42"), Pydantic will automatically convert it to an integer if the model field is int.
- **Clarity and Self-Documentation**: The BaseModel serves as a single source of truth for the shape of your agent's state, making the code easier to understand and maintain.

### How to Implement:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from langgraph.graph import StateGraph

# Define your state using a Pydantic BaseModel
class AgentState(BaseModel):
    question: str
    intermediate_steps: List[str] = Field(default_factory=list)
    final_answer: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Pass the Pydantic model directly to the StateGraph constructor
graph_builder = StateGraph(AgentState)

# Now, any node in this graph will receive a validated AgentState object
def my_node(state: AgentState):
    # 'state' is guaranteed to be a valid AgentState instance
    print(f"Processing question: {state.question}")
    # ... node logic
    return {"intermediate_steps": state.intermediate_steps + ["Step completed in my_node"]}

graph_builder.add_node("my_node", my_node)
# ... rest of the graph definition
```

### Deckster-Specific Example:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from langgraph.graph import StateGraph
from src.models.agents import PresentationStrawman, UserIntent

class DecksterWorkflowState(BaseModel):
    """State model for Deckster's presentation generation workflow"""
    # Session identification
    session_id: str
    user_id: str
    
    # Current workflow state
    current_state: Literal[
        "PROVIDE_GREETING",
        "ASK_CLARIFYING_QUESTIONS",
        "CREATE_CONFIRMATION_PLAN",
        "GENERATE_STRAWMAN",
        "REFINE_STRAWMAN",
        "PARALLEL_ENHANCEMENT"  # New state for Phase 2
    ]
    
    # User interaction data
    user_intent: Optional[UserIntent] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    
    # Presentation data
    strawman: Optional[PresentationStrawman] = None
    enhanced_slides: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Agent outputs (Phase 2)
    agent_outputs: Dict[str, List[Dict]] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Create the graph with Pydantic state
workflow = StateGraph(DecksterWorkflowState)
```

## 2. Define Tool Inputs with Pydantic

When defining tools for your agent to use (especially for function calling), always define the arguments with a Pydantic BaseModel.

### Why:

- **Reliable Function Calling**: The Pydantic model's JSON Schema is passed to the LLM, giving it a highly reliable and structured format to follow when it decides to call a tool.
- **Input Validation**: Before your tool's Python code is even executed, LangChain/LangGraph validates the arguments provided by the LLM against your Pydantic model.
- **Clear Tool Signatures**: It makes the tool's expected inputs explicit and easy to understand.

### How to Implement:

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Optional

# Define the input schema for your tool
class SearchToolInput(BaseModel):
    query: str = Field(description="The search query to execute.")
    source: str = Field(default="web", description="The source to search (e.g., 'web', 'docs').")
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of results to return.")

# Apply the Pydantic model to the tool's args_schema
@tool(args_schema=SearchToolInput)
def web_search(query: str, source: str = "web", max_results: int = 10):
    """Performs a web search for the given query."""
    print(f"Searching {source} for: {query} (max {max_results} results)")
    # ... search logic
    return f"Results for '{query}' from {source}."

# For Deckster's Layout Architect
class LayoutAnalysisInput(BaseModel):
    slide_content: Dict[str, Any] = Field(description="The slide content to analyze")
    target_audience: str = Field(description="The target audience for the presentation")
    visual_preference: Literal["minimal", "balanced", "rich"] = Field(
        default="balanced",
        description="Visual density preference"
    )

@tool(args_schema=LayoutAnalysisInput)
def analyze_slide_layout(slide_content: Dict[str, Any], 
                        target_audience: str, 
                        visual_preference: str = "balanced"):
    """Analyzes slide content and recommends optimal layout."""
    # ... layout analysis logic
    return {
        "recommended_layout": "two_column",
        "container_count": 3,
        "visual_emphasis": 0.7
    }
```

## 3. Enforce Structured Output from LLMs with Pydantic

When a node's job is to extract structured information from text, instruct the LLM to provide its response in a format that conforms to a Pydantic model.

### Why:

- **Eliminates Fragile Parsing**: Instead of writing complex regex or string-splitting logic to parse an LLM's free-text response, you get a validated, structured object directly.
- **Retry and Correction**: Frameworks like instructor can automatically re-prompt the LLM if its first response doesn't validate against the model.

### How to Implement:

```python
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional

# Enable the instructor patch
client = instructor.patch(OpenAI())

class SlideEnhancement(BaseModel):
    """Structured output for slide content enhancement"""
    enhanced_title: str = Field(description="Improved, engaging title")
    key_points: List[str] = Field(max_items=5, description="Core points to cover")
    visual_suggestions: List[str] = Field(description="Suggested visuals or graphics")
    speaker_notes: Optional[str] = Field(description="Notes for the presenter")
    layout_preference: Literal["text_heavy", "visual_heavy", "balanced"] = Field(
        description="Recommended layout style"
    )

def enhance_slide_content(slide: Dict[str, Any]) -> SlideEnhancement:
    """Enhances slide content using an LLM with structured output."""
    enhancement = client.chat.completions.create(
        model="gpt-4o",
        response_model=SlideEnhancement,  # Tell the LLM to respond with this structure
        messages=[
            {
                "role": "system", 
                "content": "You are an expert presentation designer."
            },
            {
                "role": "user", 
                "content": f"Enhance this slide: {slide}"
            }
        ],
    )
    return enhancement

# Integration with LangGraph node
def enhance_slide_node(state: DecksterWorkflowState):
    """Node that enhances slides with structured output."""
    enhanced_slides = {}
    
    if state.strawman:
        for slide in state.strawman.slides:
            enhancement = enhance_slide_content(slide.dict())
            enhanced_slides[slide.slide_id] = enhancement.dict()
    
    return {"enhanced_slides": enhanced_slides}
```

### Using PydanticAI for Structured Output:

```python
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import List

class LayoutSpecification(BaseModel):
    """Layout specification for a slide"""
    layout_type: str = Field(description="The layout template to use")
    containers: List[Dict[str, Any]] = Field(description="Container definitions")
    visual_balance: float = Field(ge=0.0, le=1.0, description="Visual to text ratio")

# Create a PydanticAI agent with structured output
layout_agent = Agent(
    model="gpt-4o",
    output_type=LayoutSpecification,
    system_prompt="You are a presentation layout expert."
)

async def generate_layout(slide_content: str) -> LayoutSpecification:
    """Generate layout using PydanticAI with guaranteed structure."""
    result = await layout_agent.run(
        f"Create a layout for this slide: {slide_content}"
    )
    return result.output  # Guaranteed to be a LayoutSpecification
```

## 4. Use Specialized Pydantic Agents as Nodes

For complex workflows, create small, specialized agents (often built with pydantic-ai) and use each one as a node in a larger LangGraph orchestrator.

### Why:

- **Modularity and Reusability**: Each agent has a single, well-defined responsibility.
- **Separation of Concerns**: The LangGraph orchestrator doesn't need to know the internal logic of each agent.
- **Scalability**: It's easy to add, remove, or replace agents in the workflow.

### Deckster Phase 2 Implementation:

```python
from pydantic_ai import Agent
from pydantic import BaseModel
from langgraph.graph import StateGraph
from typing import Dict, List, Any
import asyncio

# 1. Define specialized agents for specific tasks
class LayoutArchitectAgent:
    """Specialized agent for slide layout decisions"""
    def __init__(self):
        self.agent = Agent(
            model="gpt-4o",
            output_type=LayoutSpecification,
            system_prompt="""You are an expert presentation layout architect.
            Analyze content and create optimal visual layouts."""
        )
    
    async def process_slide(self, slide: Dict[str, Any]) -> LayoutSpecification:
        result = await self.agent.run(
            f"Create layout for: {slide}"
        )
        return result.output

class ContentResearcherAgent:
    """Specialized agent for content enhancement"""
    def __init__(self):
        self.agent = Agent(
            model="gpt-4o",
            output_type=EnhancedContent,
            system_prompt="""You are a research specialist.
            Enhance content with relevant facts and examples."""
        )
    
    async def enhance_content(self, slide: Dict[str, Any]) -> EnhancedContent:
        result = await self.agent.run(
            f"Enhance this content: {slide}"
        )
        return result.output

# 2. Create the orchestrator state
class ParallelAgentState(BaseModel):
    strawman: PresentationStrawman
    agent_outputs: Dict[str, List[AgentMessage]] = Field(default_factory=dict)
    assembled_slides: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    processing_status: Dict[str, str] = Field(default_factory=dict)

# 3. Create nodes that wrap these agents
async def layout_architect_node(state: ParallelAgentState):
    """Node wrapper for Layout Architect agent"""
    layout_agent = LayoutArchitectAgent()
    outputs = []
    
    for slide in state.strawman.slides:
        try:
            layout = await layout_agent.process_slide(slide.dict())
            outputs.append({
                "slide_id": slide.slide_id,
                "agent": "layout_architect",
                "output": layout.dict(),
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            outputs.append({
                "slide_id": slide.slide_id,
                "agent": "layout_architect",
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
    
    return {
        "agent_outputs": {
            **state.agent_outputs,
            "layout_architect": outputs
        },
        "processing_status": {
            **state.processing_status,
            "layout_architect": "complete"
        }
    }

async def content_researcher_node(state: ParallelAgentState):
    """Node wrapper for Content Researcher agent"""
    researcher = ContentResearcherAgent()
    outputs = []
    
    for slide in state.strawman.slides:
        try:
            enhanced = await researcher.enhance_content(slide.dict())
            outputs.append({
                "slide_id": slide.slide_id,
                "agent": "content_researcher",
                "output": enhanced.dict(),
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            outputs.append({
                "slide_id": slide.slide_id,
                "agent": "content_researcher",
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
    
    return {
        "agent_outputs": {
            **state.agent_outputs,
            "content_researcher": outputs
        },
        "processing_status": {
            **state.processing_status,
            "content_researcher": "complete"
        }
    }

# 4. Build the parallel execution graph
parallel_graph = StateGraph(ParallelAgentState)

# Add nodes
parallel_graph.add_node("layout_architect", layout_architect_node)
parallel_graph.add_node("content_researcher", content_researcher_node)
parallel_graph.add_node("visual_designer", visual_designer_node)
parallel_graph.add_node("data_analyst", data_analyst_node)

# Configure parallel execution
parallel_graph.set_entry_point(["layout_architect", "content_researcher", 
                                "visual_designer", "data_analyst"])

# Add assembly node
parallel_graph.add_node("director_out", director_out_assembler)

# All parallel nodes converge to director_out
for node in ["layout_architect", "content_researcher", "visual_designer", "data_analyst"]:
    parallel_graph.add_edge(node, "director_out")

# Compile the graph
parallel_workflow = parallel_graph.compile()
```

## 5. Practice Immutable State Updates

Within a node, treat the incoming state object as immutable. Instead of modifying it directly, your node should return a dictionary containing only the fields you want to update.

### Why:

- **Predictability**: It makes the flow of data explicit and easy to trace.
- **Prevents Side Effects**: Modifying the state object in-place can lead to unexpected behavior.
- **Enables Time Travel Debugging**: You can replay state transitions.

### How to Implement:

```python
# GOOD: Return a dictionary with the updated values
def good_node(state: AgentState):
    # Process without modifying state
    new_steps = state.intermediate_steps + ["A new step"]
    new_metadata = {**state.metadata, "processed_by": "good_node"}
    
    # Return only the fields you want to update
    return {
        "intermediate_steps": new_steps,
        "final_answer": "An answer",
        "metadata": new_metadata,
        "last_updated": datetime.utcnow()
    }

# BAD: Modifying the state object directly
def bad_node(state: AgentState):
    # DON'T DO THIS - modifies state in place
    state.intermediate_steps.append("A new step")  # Side effect!
    state.final_answer = "An answer"
    state.metadata["processed_by"] = "bad_node"
    return {}  # Returning nothing hides the changes

# BETTER: Use immutable update patterns
def better_node(state: AgentState):
    # Create new collections instead of modifying
    return {
        "intermediate_steps": [*state.intermediate_steps, "A new step"],
        "metadata": {**state.metadata, "processed_by": "better_node"},
        "last_updated": datetime.utcnow()
    }
```

### Complex State Update Example:

```python
def assembly_node(state: ParallelAgentState):
    """Assembles outputs from multiple agents immutably"""
    
    # Don't modify state.assembled_slides directly
    new_assembled_slides = {}
    
    # Process each agent's outputs
    for agent_name, outputs in state.agent_outputs.items():
        for output in outputs:
            slide_id = output["slide_id"]
            
            # Get existing slide data or create new
            slide_data = state.assembled_slides.get(slide_id, {})
            
            # Create new slide data with agent's contribution
            new_slide_data = {
                **slide_data,
                agent_name: output.get("output", {}),
                f"{agent_name}_timestamp": output["timestamp"]
            }
            
            new_assembled_slides[slide_id] = new_slide_data
    
    # Return only what changes
    return {
        "assembled_slides": new_assembled_slides,
        "last_updated": datetime.utcnow()
    }
```

## 6. Advanced Patterns for Parallel Agents

### Message Queue Pattern

For Phase 2's parallel agent architecture, implement a message queue pattern for agent communication:

```python
from asyncio import Queue
from typing import AsyncIterator
from pydantic import BaseModel

class AgentMessage(BaseModel):
    """Standard message format for agent communication"""
    agent_id: str
    slide_id: str
    content_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    completion_status: Literal["partial", "complete", "error"]

class MessageQueue:
    """Async message queue for agent communication"""
    def __init__(self, name: str):
        self.name = name
        self.queue: Queue[AgentMessage] = Queue()
        self.closed = False
    
    async def send(self, message: AgentMessage):
        """Send a message to the queue"""
        if self.closed:
            raise RuntimeError(f"Queue {self.name} is closed")
        await self.queue.put(message)
    
    async def receive(self) -> AsyncIterator[AgentMessage]:
        """Receive messages from the queue"""
        while not self.closed or not self.queue.empty():
            try:
                message = await self.queue.get()
                yield message
            except Exception as e:
                if self.closed and self.queue.empty():
                    break
    
    def close(self):
        """Close the queue"""
        self.closed = True

# Usage in parallel agents
class LayoutArchitectWithQueue:
    def __init__(self, message_queue: MessageQueue):
        self.queue = message_queue
        self.agent = Agent(...)
    
    async def process_slides(self, slides: List[Slide]):
        """Process slides and send results via queue"""
        for slide in slides:
            try:
                # Process slide
                layout = await self.agent.run(slide)
                
                # Send result immediately
                message = AgentMessage(
                    agent_id="layout_architect",
                    slide_id=slide.slide_id,
                    content_type="layout",
                    payload=layout.dict(),
                    timestamp=datetime.utcnow(),
                    completion_status="complete"
                )
                await self.queue.send(message)
                
            except Exception as e:
                # Send error message
                error_message = AgentMessage(
                    agent_id="layout_architect",
                    slide_id=slide.slide_id,
                    content_type="layout",
                    payload={"error": str(e)},
                    timestamp=datetime.utcnow(),
                    completion_status="error"
                )
                await self.queue.send(error_message)
```

### Progressive Assembly Pattern

Implement progressive assembly for real-time updates:

```python
class ProgressiveAssembler:
    """Assembles content progressively as agents complete"""
    
    def __init__(self, websocket_manager):
        self.websocket = websocket_manager
        self.slide_states: Dict[str, Dict[str, Any]] = {}
        self.agent_queues = {
            "layout_architect": MessageQueue("layout"),
            "content_researcher": MessageQueue("content"),
            "visual_designer": MessageQueue("visual"),
            "data_analyst": MessageQueue("data")
        }
    
    async def start_assembly(self, session_id: str, strawman: PresentationStrawman):
        """Start the progressive assembly process"""
        # Initialize slide states
        for slide in strawman.slides:
            self.slide_states[slide.slide_id] = {
                "base": slide.dict(),
                "agents": {},
                "last_sent": None
            }
        
        # Start agent listeners
        tasks = []
        for agent_name, queue in self.agent_queues.items():
            task = asyncio.create_task(
                self._listen_to_agent(agent_name, queue, session_id)
            )
            tasks.append(task)
        
        # Wait for all agents
        await asyncio.gather(*tasks)
    
    async def _listen_to_agent(self, agent_name: str, queue: MessageQueue, session_id: str):
        """Listen to an agent's message queue"""
        async for message in queue.receive():
            # Update slide state
            slide_id = message.slide_id
            self.slide_states[slide_id]["agents"][agent_name] = {
                "status": message.completion_status,
                "data": message.payload,
                "timestamp": message.timestamp
            }
            
            # Check if we should send update
            if self._should_send_update(slide_id):
                await self._send_slide_update(session_id, slide_id)
    
    def _should_send_update(self, slide_id: str) -> bool:
        """Determine if slide has enough new content to send"""
        state = self.slide_states[slide_id]
        
        # Send if we have new agent data since last send
        has_new_data = any(
            agent_data["timestamp"] > (state["last_sent"] or datetime.min)
            for agent_data in state["agents"].values()
        )
        
        return has_new_data
    
    async def _send_slide_update(self, session_id: str, slide_id: str):
        """Send progressive update for a slide"""
        state = self.slide_states[slide_id]
        
        # Build update message
        update = {
            "type": "slide_update",
            "operation": "progressive_update",
            "slide_id": slide_id,
            "content_state": {
                agent: data["status"]
                for agent, data in state["agents"].items()
            },
            "slide_data": self._merge_slide_data(state)
        }
        
        # Send via websocket
        await self.websocket.send_json(session_id, update)
        
        # Update last sent time
        state["last_sent"] = datetime.utcnow()
```

## 7. Testing and Debugging

### Unit Testing LangGraph Nodes

```python
import pytest
from unittest.mock import Mock, AsyncMock
from langgraph.graph import StateGraph

@pytest.fixture
def mock_state():
    """Create a mock state for testing"""
    return AgentState(
        question="Test question",
        intermediate_steps=["step1", "step2"],
        final_answer="",
        metadata={"test": True}
    )

def test_node_immutability(mock_state):
    """Test that nodes don't modify state"""
    original_steps = mock_state.intermediate_steps.copy()
    
    # Run node
    result = good_node(mock_state)
    
    # Verify original state unchanged
    assert mock_state.intermediate_steps == original_steps
    
    # Verify correct return
    assert "intermediate_steps" in result
    assert len(result["intermediate_steps"]) == len(original_steps) + 1

@pytest.mark.asyncio
async def test_parallel_agent_error_handling():
    """Test error handling in parallel agents"""
    # Create mock agent that fails
    mock_agent = AsyncMock()
    mock_agent.process_slide.side_effect = Exception("Agent failed")
    
    # Run node with mock
    state = ParallelAgentState(strawman=mock_strawman)
    result = await layout_architect_node(state)
    
    # Verify error captured
    assert "layout_architect" in result["agent_outputs"]
    assert any("error" in output for output in result["agent_outputs"]["layout_architect"])
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_full_parallel_workflow():
    """Test complete parallel agent workflow"""
    # Create test strawman
    strawman = PresentationStrawman(
        main_title="Test Presentation",
        overall_theme="Testing",
        slides=[
            Slide(slide_id="s1", slide_number=1, title="Test Slide", ...)
        ]
    )
    
    # Create graph
    graph = create_parallel_workflow()
    
    # Run workflow
    initial_state = ParallelAgentState(strawman=strawman)
    final_state = await graph.ainvoke(initial_state)
    
    # Verify all agents completed
    assert len(final_state.processing_status) == 4  # 4 parallel agents
    assert all(status == "complete" for status in final_state.processing_status.values())
    
    # Verify assembled output
    assert "s1" in final_state.assembled_slides
    assert "layout_architect" in final_state.assembled_slides["s1"]
```

### Debugging with LangSmith

```python
from langsmith import traceable
from langgraph.graph import StateGraph

# Enable tracing for debugging
@traceable
async def traced_node(state: AgentState):
    """Node with LangSmith tracing enabled"""
    # Your node logic here
    return {"updated_field": "value"}

# Add metadata for better debugging
@traceable(metadata={"node_type": "layout", "version": "1.0"})
async def layout_node(state: ParallelAgentState):
    """Layout node with metadata"""
    # Process layouts
    return {"agent_outputs": {...}}

# Create graph with checkpointing for debugging
from langgraph.checkpoint import MemorySaver

checkpointer = MemorySaver()
graph = StateGraph(AgentState)
# ... build graph
app = graph.compile(checkpointer=checkpointer)

# Now you can inspect state at any point
config = {"configurable": {"thread_id": "debug-session-1"}}
result = await app.ainvoke(initial_state, config=config)

# Get state history
state_history = checkpointer.get_state_history(config)
```

## 8. Performance Optimization

### Batch Processing

```python
class BatchProcessor:
    """Process multiple items efficiently"""
    
    def __init__(self, batch_size: int = 5):
        self.batch_size = batch_size
    
    async def process_slides_in_batches(self, slides: List[Slide], processor_func):
        """Process slides in batches for better performance"""
        results = []
        
        for i in range(0, len(slides), self.batch_size):
            batch = slides[i:i + self.batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                processor_func(slide) for slide in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            results.extend(batch_results)
        
        return results

# Usage in node
async def optimized_layout_node(state: ParallelAgentState):
    """Layout node with batch processing"""
    processor = BatchProcessor(batch_size=5)
    layout_agent = LayoutArchitectAgent()
    
    # Process in batches
    results = await processor.process_slides_in_batches(
        state.strawman.slides,
        layout_agent.process_slide
    )
    
    # Convert to agent outputs
    outputs = []
    for slide, result in zip(state.strawman.slides, results):
        if isinstance(result, Exception):
            outputs.append({
                "slide_id": slide.slide_id,
                "error": str(result)
            })
        else:
            outputs.append({
                "slide_id": slide.slide_id,
                "output": result.dict()
            })
    
    return {"agent_outputs": {"layout_architect": outputs}}
```

### Caching for Repeated Operations

```python
from functools import lru_cache
from typing import Tuple
import hashlib

class CachedAgent:
    """Agent with caching for repeated operations"""
    
    def __init__(self):
        self.agent = Agent(...)
        self.cache = {}
    
    def _get_cache_key(self, slide: Slide) -> str:
        """Generate cache key for slide"""
        # Create deterministic key from slide content
        content = f"{slide.title}:{slide.narrative}:{':'.join(slide.key_points)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def process_slide_with_cache(self, slide: Slide):
        """Process slide with caching"""
        cache_key = self._get_cache_key(slide)
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Process and cache
        result = await self.agent.run(slide)
        self.cache[cache_key] = result
        
        return result

# LRU cache for stateless operations
@lru_cache(maxsize=100)
def compute_layout_metrics(slide_type: str, content_length: int, visual_count: int) -> Dict:
    """Cached computation of layout metrics"""
    # Expensive computation here
    return {
        "complexity": content_length / 100 + visual_count * 2,
        "recommended_duration": content_length / 150  # words per minute
    }
```

### Resource Management

```python
import asyncio
from contextlib import asynccontextmanager

class ResourcePool:
    """Manage limited resources (e.g., API connections)"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a resource slot"""
        async with self.semaphore:
            yield

# Global resource pool
api_pool = ResourcePool(max_concurrent=5)

async def rate_limited_node(state: AgentState):
    """Node with rate limiting"""
    results = []
    
    async def process_with_limit(item):
        async with api_pool.acquire():
            # Only 5 concurrent API calls
            return await expensive_api_call(item)
    
    # Process all items with rate limiting
    tasks = [process_with_limit(item) for item in state.items]
    results = await asyncio.gather(*tasks)
    
    return {"results": results}
```

## 9. Migration Strategy

### Gradual Migration from Sequential to Parallel

```python
from typing import Union

class HybridWorkflow:
    """Supports both sequential and parallel execution during migration"""
    
    def __init__(self, enable_parallel: bool = False):
        self.enable_parallel = enable_parallel
        self.sequential_graph = self._build_sequential_graph()
        self.parallel_graph = self._build_parallel_graph()
    
    def _build_sequential_graph(self) -> StateGraph:
        """Build the Phase 1 sequential graph"""
        graph = StateGraph(DecksterWorkflowState)
        
        # Add sequential nodes
        graph.add_node("greeting", provide_greeting)
        graph.add_node("questions", ask_questions)
        graph.add_node("plan", create_plan)
        graph.add_node("strawman", generate_strawman)
        graph.add_node("refine", refine_strawman)
        
        # Sequential flow
        graph.add_edge("greeting", "questions")
        graph.add_edge("questions", "plan")
        graph.add_edge("plan", "strawman")
        graph.add_edge("strawman", "refine")
        
        return graph.compile()
    
    def _build_parallel_graph(self) -> StateGraph:
        """Build the Phase 2 parallel graph"""
        graph = StateGraph(DecksterWorkflowState)
        
        # Add all sequential nodes
        # ... same as above ...
        
        # Add parallel enhancement after strawman
        graph.add_conditional_edges(
            "strawman",
            self._should_enhance_parallel,
            {
                True: ["layout", "research", "visual", "data"],
                False: "refine"
            }
        )
        
        # Add parallel nodes
        graph.add_node("layout", layout_architect_node)
        graph.add_node("research", researcher_node)
        graph.add_node("visual", visual_designer_node)
        graph.add_node("data", data_analyst_node)
        
        # Converge to assembly
        graph.add_node("assembly", assembly_node)
        for node in ["layout", "research", "visual", "data"]:
            graph.add_edge(node, "assembly")
        
        graph.add_edge("assembly", "refine")
        
        return graph.compile()
    
    def _should_enhance_parallel(self, state: DecksterWorkflowState) -> bool:
        """Decide whether to use parallel enhancement"""
        return (
            self.enable_parallel and 
            state.strawman is not None and
            len(state.strawman.slides) > 0
        )
    
    async def run(self, initial_state: DecksterWorkflowState):
        """Run the appropriate workflow"""
        if self.enable_parallel:
            return await self.parallel_graph.ainvoke(initial_state)
        else:
            return await self.sequential_graph.ainvoke(initial_state)

# Usage during migration
workflow = HybridWorkflow(enable_parallel=os.getenv("ENABLE_PARALLEL", "false") == "true")
result = await workflow.run(initial_state)
```

### Feature Flag Management

```python
from pydantic import BaseModel
from typing import Dict, Any

class FeatureFlags(BaseModel):
    """Feature flags for gradual rollout"""
    enable_parallel_agents: bool = False
    enable_layout_architect: bool = True
    enable_content_researcher: bool = False
    enable_visual_designer: bool = False
    enable_progressive_updates: bool = True
    parallel_agent_timeout: int = 30  # seconds
    
    class Config:
        # Allow dynamic updates
        validate_assignment = True

# Global feature flags
features = FeatureFlags()

# Conditional node execution
async def conditional_layout_node(state: ParallelAgentState):
    """Only run if feature enabled"""
    if not features.enable_layout_architect:
        return {"processing_status": {"layout_architect": "skipped"}}
    
    # Normal processing
    return await layout_architect_node(state)

# A/B testing with feature flags
def get_user_features(user_id: str) -> FeatureFlags:
    """Get feature flags for specific user"""
    # Implement your A/B testing logic
    if hash(user_id) % 100 < 10:  # 10% of users
        return FeatureFlags(
            enable_parallel_agents=True,
            enable_content_researcher=True
        )
    return FeatureFlags()  # Default flags
```

## Best Practices Summary

1. **Always use Pydantic models** for state, tool inputs, and LLM outputs
2. **Keep nodes pure** - they should only return updates, not modify state
3. **Design for failure** - handle errors gracefully in parallel execution
4. **Test thoroughly** - unit test nodes, integration test workflows
5. **Monitor everything** - use tracing and logging for debugging
6. **Optimize wisely** - batch operations and cache when appropriate
7. **Migrate gradually** - use feature flags and hybrid approaches

## Conclusion

The combination of LangGraph and Pydantic provides a powerful foundation for building robust, scalable AI agent systems. By following these best practices, you can create maintainable workflows that are easy to test, debug, and evolve. The patterns shown here are particularly relevant for Deckster's Phase 2 parallel agent architecture, where multiple specialized agents work together to create rich, engaging presentations.