# Analyze Agent Product Command

## Overview
This command analyzes a product concept document and produces a detailed functional specification with all requirements, functionalities, and data architecture needed for agent development.

## Usage
```
/analyze-agent-product <path-to-product-concept.md>
```

## Output
Creates: `/docs/plan/[AgentName]_Product_Analysis.md`

## Process

### Phase 1: Initial Product Analysis

Read and analyze the provided product concept document to understand:
- Core goals and objectives
- Target users and use cases
- High-level requirements
- Integration context
- Success criteria
- **Agent name(s)** - Extract for file naming

**Important**: Check if the document describes multiple agents. If so, create separate analysis documents for each agent:
- `/docs/plan/[AgentName1]_Product_Analysis.md`
- `/docs/plan/[AgentName2]_Product_Analysis.md`

### Phase 2: Detailed Functionality Definition

Whether the product concept has detailed specifications or not, create a comprehensive functionality breakdown:

#### 2.1 Core Functionality Analysis
1. **Identify Primary Goals**: What are the main objectives this agent must achieve?
2. **Break Down into Specific Functions**: List all discrete tasks the agent must perform
3. **Define Success Criteria**: How do we measure if each function succeeds?
4. **Map User Interactions**: Document all ways users will interact with the agent
5. **Identify Data Requirements**: What data does each function need?

#### 2.2 Functionality Documentation Template
```markdown
## Detailed Functionalities for [Agent Name]

### Primary Functions
1. **[Function Name]**
   - Purpose: [What it accomplishes]
   - Trigger: [When/how it's invoked]
   - Input Requirements:
     - Data: [What data it needs]
     - Format: [Expected format]
     - Validation: [Rules/constraints]
   - Processing Steps:
     - Step 1: [Description]
     - Step 2: [Description]
   - Output Specification:
     - Data: [What it produces]
     - Format: [Output format]
   - Success Criteria: [Measurable outcomes]
   - Error Scenarios: [What could go wrong]
   - Dependencies: [Other functions/systems needed]

### Supporting Functions
[Similar structure for supporting functions]

### User Interaction Flows
1. **[Flow Name]**
   - Entry Point: [How user initiates]
   - Steps: [User journey]
   - Decision Points: [Where choices are made]
   - Exit Points: [How flow completes]
```

### Phase 3: Memory and State Analysis

#### 3.1 Analyze Current Supabase Architecture

Review the existing database schema to understand:

1. **Current Session Structure**:
   ```sql
   -- Document the current sessions table
   sessions:
     - id: UUID
     - user_id: TEXT
     - current_state: TEXT
     - conversation_history: JSONB
     - user_initial_request: TEXT
     - clarifying_answers: JSONB
     - confirmation_plan: JSONB
     - presentation_strawman: JSONB
     - refinement_feedback: TEXT
     - created_at: TIMESTAMP
     - updated_at: TIMESTAMP
   ```

2. **Identify Agent Memory Needs**:
   - What state must persist across interactions?
   - What is temporary/working memory?
   - What context is needed for each function?
   - How does memory relate to user sessions?

3. **Design Memory Architecture**:
   ```markdown
   ## Memory Requirements
   
   ### Working Memory (Session-based)
   - [Item]: [Why needed, lifecycle]
   
   ### Persistent Memory (Database)
   - [Item]: [Why needed, storage strategy]
   
   ### Context Requirements
   - [Function]: [Context needed]
   ```

4. **Propose Schema Changes**:
   ```sql
   -- Example: Additional columns for sessions
   ALTER TABLE sessions ADD COLUMN [agent_name]_state JSONB;
   
   -- Example: New tables if needed
   CREATE TABLE [agent_name]_memory (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       session_id UUID REFERENCES sessions(id),
       memory_type TEXT NOT NULL,
       data JSONB NOT NULL,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```

### Phase 4: Integration Analysis

#### 4.1 System Integration Points
- How does this agent fit into Deckster's workflow?
- Which existing components will it interact with?
- What new WebSocket message types are needed?
- How does it integrate with the Director agent?

#### 4.2 Data Flow Mapping
```markdown
## Data Flow Analysis

### Input Sources
1. **[Source]**: [Type of data, format, frequency]

### Processing Pipeline
1. **[Stage]**: [What happens to data]

### Output Destinations
1. **[Destination]**: [What receives output, format]
```

### Phase 5: Technical Requirements

Based on the functional analysis, define:

1. **Performance Requirements**:
   - Response time expectations
   - Throughput needs
   - Concurrency requirements

2. **Scalability Considerations**:
   - Expected load
   - Growth projections
   - Resource constraints

3. **Security Requirements**:
   - Data sensitivity
   - Access controls needed
   - Compliance requirements

### Phase 6: Success Metrics

Define measurable success criteria:

1. **Functional Metrics**:
   - [Function]: [How to measure success]

2. **Performance Metrics**:
   - Response time targets
   - Error rate thresholds

3. **User Experience Metrics**:
   - User satisfaction indicators
   - Task completion rates

## Output Format

Generate a comprehensive product analysis document saved as:
`/docs/plan/[AgentName]_Product_Analysis.md`

```markdown
# [Agent Name] Product Analysis & Functional Specification

## Executive Summary
- **Purpose**: [One paragraph summary]
- **Key Capabilities**: [Bullet list]
- **Integration Context**: [How it fits in Deckster]
- **Multiple Agents**: [Yes/No - list if multiple]

## Product Concept Analysis
### Original Requirements
[Summary of provided concept]

### Assumptions Made
[Any assumptions needed to complete the analysis]

## Detailed Functional Specification

### Primary Functions
[Complete breakdown using template from Phase 2]

### Supporting Functions
[Complete breakdown]

### User Interaction Flows
[All interaction patterns]

## Memory Architecture Analysis

### Current Supabase Schema
[Analysis of existing structure]

### Agent Memory Requirements
[Working memory, persistent memory, context needs]

### Proposed Schema Changes
```sql
-- SQL for required changes
```

## Integration Requirements

### System Integration Points
[How it connects with existing components]

### Data Flow
[Input sources → Processing → Output destinations]

### New WebSocket Messages
[Any new message types needed]

## Technical Requirements

### Performance
[Specific requirements]

### Scalability
[Considerations and limits]

### Security
[Requirements and constraints]

## Success Metrics
[Measurable criteria for each function]

## Implementation Considerations
[Any special notes for architects/developers]

## Next Steps
- Use this document as input for `/build-agent-architecture`
- Review with team for completeness
- Validate assumptions with stakeholders

## Appendices
### A: Glossary
### B: Referenced Documents
### C: Open Questions
```

## Command Implementation Notes

When executing this command:

1. **Extract agent name** - Use for file naming
2. **Save to correct location** - `/docs/plan/[AgentName]_Product_Analysis.md`
3. **Read thoroughly** - Understand the complete product concept
4. **Check for multiple agents** - Create separate documents if needed
5. **Define all functionalities** - Even if not specified in the concept
6. **Analyze existing schema** - Understand current memory architecture
7. **Be specific** - Avoid vague descriptions
8. **Make reasonable assumptions** - But document them clearly
9. **Consider edge cases** - What could go wrong?
10. **Think about scale** - Will this work with 1000 users?
11. **Map to existing systems** - How does it fit with current architecture?
12. **Define measurable success** - How do we know it works?

## Best Practices

- ✅ Use consistent file naming: `[AgentName]_Product_Analysis.md`
- ✅ Save in `/docs/plan/` directory
- ✅ Complete functional breakdown before architecture
- ✅ Clear input/output specifications
- ✅ Specific success criteria
- ✅ Memory lifecycle management
- ✅ Integration touchpoints identified
- ✅ Performance requirements defined
- ✅ Security considerations documented
- ✅ User flows mapped
- ✅ Error scenarios considered
- ✅ Assumptions documented

## Example Execution

```bash
# Analyze a layout architect product concept
/analyze-agent-product /docs/concepts/layout-architect-concept.md

# Creates: /docs/plan/LayoutArchitect_Product_Analysis.md

# If multiple agents in one concept:
/analyze-agent-product /docs/concepts/multi-agent-concept.md

# Creates:
# - /docs/plan/ResearchAgent_Product_Analysis.md
# - /docs/plan/DesignAgent_Product_Analysis.md
```

## Next Steps

After running this command, use the output as input for:
- `/build-agent-architecture` - To create the technical architecture
- Architecture reviews with the team
- Implementation planning sessions