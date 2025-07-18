# Build Agent Solution Architecture Command

## Overview
This command takes a product analysis document (created by `/analyze-agent-product`) and generates a comprehensive technical architecture and implementation plan for a PydanticAI-based agent.

## Usage
```
/build-agent-architecture /docs/plan/[AgentName]_Product_Analysis.md
```

## Output
Creates: `/docs/plan/[AgentName]_Architecture.md`

## Prerequisites
- Must have a completed Product Analysis document from `/analyze-agent-product`
- Product Analysis should include detailed functionality specifications
- Memory requirements should be defined

## Process

### Phase 1: Review Product Analysis

Read the provided Product Analysis document to understand:
- Detailed functional specifications
- Memory architecture requirements
- Integration points
- Performance requirements
- Success metrics

### Phase 2: Critical Architectural Decision - Prompting vs Tools

This is the most critical decision in agent design. Using the functional specifications from the Product Analysis, determine whether each function should be handled through prompting or tools.

#### The Core Principle

**Prompting is for Reasoning and Knowledge**
- Use prompts for tasks requiring creativity, synthesis, understanding nuance, or generating natural language
- The agent's persona, instructions, context, and general strategy
- Subjective decisions and information synthesis

**Tools are for Acting and Facts**
- Use tools for deterministic, reliable, and repeatable actions
- External data access, system interactions, precise calculations
- Enforcing business rules and constraints

#### Decision Framework

For each function identified in the Product Analysis, classify it:

**Use PROMPTING When:**
1. **Defining Agent Goal and Persona**: System prompt tells the agent what it is and its objectives
   - Example: "You are an expert presentation designer who creates engaging slide layouts"

2. **Making Subjective Decisions**: Choosing "best" options based on vague criteria
   - Example: "Analyze the content and decide if a chart or table would be more effective"

3. **Generating Creative Content**: Writing summaries, titles, or explanations
   - Example: "Create an engaging title for this data visualization"

4. **Transforming Unstructured Data**: Converting messy input into structured plans
   - Example: "Understand the user's request and identify the key components needed"

**Use TOOLS When:**
1. **Getting External Information**: Data not in the model's training set
   - Example: `search_web()`, `query_database()`, `fetch_current_prices()`

2. **Performing Calculations**: Precise math or geometry
   - Example: `calculate_layout_positions()`, `compute_statistics()`

3. **Interacting with Systems**: APIs, files, databases
   - Example: `save_to_database()`, `send_email()`, `update_crm()`

4. **Enforcing Rules**: Business logic that must be exact
   - Example: `validate_slide_constraints()`, `check_brand_compliance()`

### Phase 3: Build Technical Architecture

Generate a comprehensive agent architecture focusing on PydanticAI best practices:

#### 3.1 Base Models Definition
Define Pydantic models based on the Product Analysis:
- **Input Models**: Structure for data coming into the agent
- **Output Models**: Structure for agent responses
- **State Models**: Internal state representations
- **Dependency Models**: External service dependencies

Example structure:
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class [AgentName]Input(BaseModel):
    """Based on functional requirements from Product Analysis"""
    # Fields derived from input specifications
    
class [AgentName]Output(BaseModel):
    """Based on output specifications from Product Analysis"""
    # Fields derived from output specifications

class [AgentName]State(BaseModel):
    """Internal state management based on memory requirements"""
    # Fields derived from memory architecture

class [AgentName]Dependencies(BaseModel):
    """External dependencies"""
    session_manager: Any
    supabase_client: Any
    # Other dependencies from integration analysis
```

#### 3.2 Agent Configuration

Design the agent configuration including:

**System Prompt Engineering** (for reasoning tasks):
```python
system_prompt = """
You are [agent role from Product Analysis]. Your primary goal is [main objective].

Core Responsibilities (handled via reasoning):
[List from prompting decisions]

You have access to tools for:
[List from tools decisions]

Decision Framework:
[Specific guidance based on functional requirements]
"""
```

**Tool Integration Strategy**:
- Clear tool descriptions that help the LLM understand when to use each tool
- Explicit guidance in prompts about tool usage
- Tool composition for complex operations

#### 3.3 Tools Architecture

Based on the Prompting vs Tools analysis, design specific tools:

```python
from pydantic_ai import RunContext, Tool
from pydantic import BaseModel, Field

# For each function marked for tools in Phase 2
@tool
async def [tool_name](
    ctx: RunContext[[AgentName]Dependencies],
    # Parameters from functional specification
) -> [OutputType]:
    """
    Clear description for LLM to understand when to use this tool.
    Based on: [Function name from Product Analysis]
    """
    # Implementation based on processing steps
```

#### 3.4 Memory Implementation

Implement the memory architecture from Product Analysis:

```python
class [AgentName]Memory:
    """Memory management based on Product Analysis requirements"""
    
    async def store_working_memory(self, session_id: str, data: Dict):
        """Store temporary working memory"""
        
    async def persist_long_term_memory(self, session_id: str, data: Dict):
        """Persist important state to database"""
        
    async def retrieve_context(self, session_id: str) -> Dict:
        """Build context from stored memory"""
```

### Phase 4: Production Optimizations

#### 4.1 Context Management
Implement context strategies from Product Analysis:
- State-aware context building
- Token optimization
- Session integration

#### 4.2 Logfire Logging
Add comprehensive logging:
```python
import logfire

# Log all major decisions and operations
logfire.info("agent.operation",
    agent_name="[AgentName]",
    operation="[specific operation]",
    # Relevant metrics
)
```

#### 4.3 LangGraph Workflow
Design workflow orchestration based on user interaction flows:
```python
from langgraph import StateGraph

class [AgentName]Workflow:
    """Workflow implementation based on interaction flows from Product Analysis"""
```

### Phase 5: Implementation Plan

Create a detailed implementation plan with phases:

**Phase 1: Foundation** [Week 1-2]
- [ ] Project setup and structure
- [ ] Base models implementation
- [ ] Core agent class
- [ ] Essential tools (based on priority)
- [ ] Unit tests

**Phase 2: Integration** [Week 3]
- [ ] Deckster integration
- [ ] Memory implementation
- [ ] Context management
- [ ] Logging setup
- [ ] Integration tests

**Phase 3: Workflow** [Week 4]
- [ ] LangGraph workflow
- [ ] State management
- [ ] Error handling
- [ ] End-to-end tests

**Phase 4: Optimization** [Week 5]
- [ ] Performance tuning
- [ ] Token optimization
- [ ] Caching implementation
- [ ] Documentation

## Output Format

Generate architecture document saved as:
`/docs/plan/[AgentName]_Architecture.md`

```markdown
# [Agent Name] Solution Architecture

## Executive Summary
- **Purpose**: [From Product Analysis]
- **Key Architectural Decisions**: [Prompting vs Tools summary]
- **Integration Overview**: [How it fits in Deckster]

## Architectural Decisions

### Prompting vs Tools Analysis
Based on the functional requirements from the Product Analysis:

#### Reasoning Tasks (Prompting)
1. **[Function]**: [Why prompting is appropriate]
2. **[Function]**: [Why prompting is appropriate]

#### Deterministic Tasks (Tools)
1. **[Function]**: [Why tool is appropriate]
2. **[Function]**: [Why tool is appropriate]

## Technical Architecture

### 1. Component Architecture
[Diagram showing agent components, tools, and integrations]

### 2. Base Models
```python
# Complete model definitions
```

### 3. Agent Configuration
```python
# System prompt and configuration
```

### 4. Tools Implementation
```python
# Tool definitions with clear docstrings
```

### 5. Memory Architecture
```python
# Memory management implementation
```

### 6. Workflow Design
```python
# LangGraph workflow if applicable
```

## Integration Architecture

### Deckster Integration
- Session management approach
- WebSocket message handling
- State synchronization

### Database Integration
- Schema implementation from Product Analysis
- Migration scripts
- Data access patterns

## Implementation Plan

### Phase Breakdown
[Detailed phases with specific tasks]

### Risk Mitigation
- Technical risks and mitigation strategies
- Dependencies and fallback plans

## Code Examples

### Basic Usage
```python
# Example of using the agent
```

### Tool Usage
```python
# Example showing tool integration
```

### Memory Management
```python
# Example of memory operations
```

## Testing Strategy

### Unit Tests
- Model validation
- Tool functionality
- Prompt effectiveness

### Integration Tests
- Deckster integration
- Database operations
- End-to-end flows

## Deployment Considerations

### Configuration
- Environment variables
- Model selection
- Feature flags

### Monitoring
- Key metrics to track
- Alerting thresholds
- Performance benchmarks

## Appendices

### A: API Reference
[Complete API documentation]

### B: Configuration Reference
[All configuration options]

### C: Troubleshooting Guide
[Common issues and solutions]
```

## Command Implementation Notes

When executing this command:

1. **Extract agent name** from Product Analysis for file naming
2. **Save to correct location** - `/docs/plan/[AgentName]_Architecture.md`
3. **Reference Product Analysis** throughout the document
4. **Make prompting vs tools decisions** for each function
5. **Design complete implementation** including models, tools, and workflows
6. **Include working code examples** not just abstractions
7. **Create actionable implementation plan** with clear phases
8. **Consider production requirements** from the start
9. **Document integration points** clearly
10. **Provide testing strategies** for all components

## Best Practices Checklist

- ✅ Use consistent file naming: `[AgentName]_Architecture.md`
- ✅ Save in `/docs/plan/` directory
- ✅ Clear prompting vs tools decisions for each function
- ✅ Type-safe models matching Product Analysis
- ✅ Descriptive tool docstrings for LLM
- ✅ Memory implementation matching requirements
- ✅ Integration with existing Deckster systems
- ✅ Comprehensive logging strategy
- ✅ Clear implementation phases
- ✅ Working code examples
- ✅ Testing approach defined
- ✅ Production considerations included

## Example Execution

```bash
# Build architecture for Layout Architect
/build-agent-architecture /docs/plan/LayoutArchitect_Product_Analysis.md

# Creates: /docs/plan/LayoutArchitect_Architecture.md

# Build architecture for Research Agent
/build-agent-architecture /docs/plan/ResearchAgent_Product_Analysis.md

# Creates: /docs/plan/ResearchAgent_Architecture.md
```

## References

Key documents to consider:
- PydanticAI Best Practices: `/docs/clean_documents/PydanticAI_Best_Practices.md`
- Context Management: `/docs/clean_documents/Context_and_Memory_Management.md`
- Phase 1 Architecture: `/docs/architecture/phase1-architecture.md`
- WebSocket Protocol: `/docs/clean_documents/WebSocket_Communication_Protocol.md`
- Modular Prompts: `/docs/clean_documents/Modular_Prompt_Architecture.md`