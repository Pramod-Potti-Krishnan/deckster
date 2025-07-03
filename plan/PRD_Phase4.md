# PRD Phase 4: Iterative User Feedback and Refinement

## References
- [PRD v4.0](./PRD_v4.0.md) - Main product requirements document
- [Communication Protocols](./comms_protocol.md) - Detailed JSON message templates and protocols
- [Technology Stack](./tech_stack.md) - Framework specifications and implementation guidelines
- [Security Requirements](./security.md) - MVP security implementation guidelines
- [Folder Structure](./folder_structure.md) - Project organization and file placement guide

## FEATURE:
Enable users to iterate on generated presentations through targeted feedback on specific slides, triggering appropriate agents to refine content, visuals, layouts, or data while maintaining consistency across the presentation.

## EXAMPLES:
- User feedback: `{"slide_id": "slide_5", "feedback": "Make the chart show quarterly data instead of monthly"}`
- System routes to Data Analyst for chart update
- User requests: `{"slides": ["slide_2", "slide_3"], "feedback": "Change layout to single column"}`
- System engages UX Architect for layout modifications
- User provides: `{"global_feedback": "Make all images more professional and corporate"}`
- Visual Designer updates all images maintaining new style

## DOCUMENTATION:
- **Feedback Processing**: Natural language understanding via Pydantic AI
- **Agent Routing**: LangGraph conditional workflows based on feedback type
- **Version Control**: Track iterations and allow rollbacks
- **State Management**: Maintain presentation coherence across changes
- **MCP Server**: Feedback analysis tools, version comparison
- **Communication**: WebSocket for real-time iteration updates

## KEY COMPONENTS:

### 1. Feedback Analysis System
```python
class FeedbackAnalyzer(Agent):
    name = "feedback_analyzer"
    description = "Interprets user feedback and routes to appropriate agents"
    
    async def analyze_feedback(self, feedback: UserFeedback) -> FeedbackPlan:
        # Parse natural language feedback
        # Identify affected components
        # Determine required agents
        # Create execution plan
        
class UserFeedback(BaseModel):
    session_id: str
    presentation_id: str
    feedback_type: Literal['slide_specific', 'global', 'section']
    target_ids: List[str]  # slide_ids or section_ids
    feedback_text: str
    priority: Literal['high', 'medium', 'low']
    
class FeedbackPlan(BaseModel):
    plan_id: str
    actions: List[FeedbackAction]
    affected_agents: List[str]
    estimated_time: float
    
class FeedbackAction(BaseModel):
    action_id: str
    agent: str
    task_type: str
    parameters: Dict[str, Any]
    dependencies: List[str]
```

### 2. Iterative Workflow (LangGraph)
```python
iteration_workflow = StateGraph()

# Feedback entry point
iteration_workflow.add_node("feedback_analyzer", analyze_feedback)
iteration_workflow.add_node("change_coordinator", coordinate_changes)

# Agent nodes (reuse from previous phases)
iteration_workflow.add_node("director_inbound", director_refiner)
iteration_workflow.add_node("ux_architect", layout_updater)
iteration_workflow.add_node("researcher", content_updater)
iteration_workflow.add_node("visual_designer", visual_refiner)
iteration_workflow.add_node("data_analyst", data_updater)
iteration_workflow.add_node("ux_analyst", diagram_updater)

# Dynamic routing based on feedback
iteration_workflow.add_conditional_edges(
    "feedback_analyzer",
    route_feedback_to_agents,
    {
        "layout": "ux_architect",
        "content": "researcher",
        "visual": "visual_designer",
        "data": "data_analyst",
        "diagram": "ux_analyst",
        "structure": "director_inbound"
    }
)
```

### 3. Version Management
```python
class PresentationVersion(BaseModel):
    version_id: str
    presentation_id: str
    version_number: int
    timestamp: datetime
    changes: List[ChangeRecord]
    parent_version: Optional[str]
    
class ChangeRecord(BaseModel):
    change_id: str
    slide_ids: List[str]
    change_type: str
    description: str
    agent_responsible: str
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    
class VersionManager:
    async def create_version(self, presentation: Presentation) -> PresentationVersion:
        # Snapshot current state
        # Track changes
        # Enable rollback
```

### 4. Coherence Maintenance
```python
class CoherenceEngine:
    async def validate_changes(
        self,
        original: Presentation,
        changes: List[ChangeRecord]
    ) -> ValidationResult:
        # Check style consistency
        # Verify content flow
        # Ensure data accuracy
        # Validate visual harmony
        
class ValidationResult(BaseModel):
    is_valid: bool
    issues: List[CoherenceIssue]
    suggestions: List[Suggestion]
```

## OTHER CONSIDERATIONS:

### Feedback Categories
- **Layout Changes**: Grid system, component positioning
- **Content Updates**: Text edits, data corrections, citations
- **Visual Refinements**: Image style, color scheme, typography
- **Data Modifications**: Chart types, data sources, calculations
- **Structural Changes**: Slide order, section reorganization

### Smart Routing Logic
```python
class FeedbackRouter:
    feedback_patterns = {
        r"(change|modify|update).*(layout|grid|position)": "ux_architect",
        r"(update|correct|fix).*(data|chart|graph)": "data_analyst",
        r"(make|change).*(image|visual|picture)": "visual_designer",
        r"(add|remove|edit).*(content|text|information)": "researcher",
        r"(create|update).*(diagram|flow|chart)": "ux_analyst"
    }
```

### Batch Processing
- Group similar feedback items
- Process related changes together
- Minimize agent switching overhead
- Parallel execution where possible

### Conflict Resolution
- Detect conflicting feedback
- Priority-based resolution
- User confirmation for ambiguous cases
- Maintain audit trail

### WebSocket Communication
```json
{
  "type": "iteration_update",
  "data": {
    "status": "processing",
    "current_agent": "data_analyst",
    "progress": 0.65,
    "completed_changes": ["change_123", "change_124"],
    "estimated_remaining": 15
  }
}
```

### Memory Management

#### Short-term Memory (Contextual)
- **Iteration Context**: Redis + Supabase
  ```python
  class IterationContext(BaseModel):
      session_id: str
      presentation_id: str
      current_version: int
      active_feedback: List[UserFeedback]
      change_queue: List[FeedbackAction]
      rollback_stack: List[str]  # version_ids
      style_lock: Dict[str, Any]  # Locked style params during iteration
  ```
- **Change Tracking Cache**:
  - Redis: Active changes being processed
  - Diff snapshots for quick rollback
  - Agent coordination state
  - Conflict detection buffer
- **Feedback History**:
  - Recent feedback in Redis (last 10 iterations)
  - Complete history in Supabase
  - Pattern recognition data

#### Long-term Memory (Tools & Knowledge)
- **Feedback Pattern Database** (Supabase):
  ```python
  class FeedbackPatternStore:
      async def store_feedback_outcome(self, feedback: UserFeedback, outcome: FeedbackOutcome):
          # Learn from successful feedback handling
          await supabase.table('feedback_patterns').insert({
              'feedback_embedding': await generate_feedback_embedding(feedback),
              'feedback_type': classify_feedback(feedback),
              'agent_routing': outcome.agents_used,
              'success_metrics': outcome.metrics,
              'user_satisfaction': outcome.satisfaction_score,
              'reusable_pattern': extract_pattern(feedback, outcome)
          })
          
      async def find_similar_feedback(self, feedback: UserFeedback) -> List[FeedbackPattern]:
          # Find previously successful handling strategies
          return await supabase.rpc('match_feedback_patterns', {
              'feedback_embedding': await generate_feedback_embedding(feedback),
              'context_type': feedback.feedback_type,
              'min_satisfaction': 0.8
          })
  ```
- **Version History Management**:
  - Supabase: Complete version tree with diffs
  - Successful change patterns
  - User preference evolution
  - A/B testing results storage
- **Iteration Learning**:
  - Common feedback sequences
  - Effective agent combinations
  - Style preference models
  - Performance optimization patterns
- **Collaboration Memory**:
  - Multi-user change history
  - Conflict resolution patterns
  - Team preference profiles
  - Review/approval workflows

### Performance Optimization
- Incremental updates (only changed slides)
- Diff-based change tracking
- Lazy loading for large presentations
- Background processing for non-blocking UX

### Development Priorities
1. Build feedback analyzer with NLP capabilities
2. Implement dynamic routing system
3. Create version management system
4. Add coherence validation engine
5. Setup incremental update mechanism
6. Implement conflict resolution
7. Add comprehensive feedback loop testing

### Success Metrics
- Feedback understanding accuracy: >90%
- Iteration completion time: <30s for single slide
- User satisfaction with changes: >85%
- Coherence maintenance: 100%
- Version rollback success: 100%

### Advanced Features
- **Learning System**: Track successful feedback patterns
- **Suggestion Engine**: Proactive improvement suggestions
- **Collaboration**: Multi-user feedback handling
- **Export Options**: Version comparison reports