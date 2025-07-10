# Context and Memory Management Analysis - Deckster Director Workflow

## Executive Summary

This document analyzes how context and memory are managed throughout the Director workflow in Deckster. The current implementation has several areas of concern that could lead to token waste, performance issues, and potential context overflow as conversations grow.

### Key Findings
1. **Full context is sent on every LLM call** - Leading to exponential token growth
2. **No context summarization** - History grows unbounded
3. **Redundant data storage** - Same information stored in multiple places
4. **No state-specific context filtering** - All states get all context
5. **Missing token counting** - No awareness of approaching limits

## Current Implementation Analysis

### 1. Core Data Structures

#### StateContext (src/models/agents.py)
```python
class StateContext(BaseModel):
    current_state: Literal[...]
    user_intent: Optional[UserIntent] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    session_data: Dict[str, Any] = Field(default_factory=dict)
```

**Issues:**
- `conversation_history` is an unbounded list
- No token count tracking
- No context window management

#### Session Model (src/models/session.py)
```python
class Session(BaseModel):
    id: str
    current_state: Literal[...]
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    user_initial_request: Optional[str] = None
    clarifying_answers: Optional[Dict[str, str]] = None
    confirmation_plan: Optional[Dict[str, Any]] = None
    presentation_strawman: Optional[Dict[str, Any]] = None
    refinement_feedback: Optional[str] = None
```

**Issues:**
- Duplicate storage of conversation history
- Large objects (strawman) stored entirely
- No compression or summarization

### 2. Context Building Process

#### How Context is Built (src/agents/director.py)

```python
# Current implementation - lines 301-321
history_serializable = []
for item in state_context.conversation_history:
    if isinstance(item, dict):
        item_copy = item.copy()
        if hasattr(item_copy.get('content'), 'dict'):
            item_copy['content'] = item_copy['content'].dict()
        history_serializable.append(item_copy)
    else:
        history_serializable.append(str(item))

prompt = f"""
Current state: {state_context.current_state}
Conversation history: {json.dumps(history_serializable)}
Session data: {json.dumps(state_context.session_data)}

Process according to the rules for state {state_context.current_state}.
"""
```

**Critical Issues:**
1. **ENTIRE conversation history** is serialized and sent every time
2. **ALL session data** is included regardless of relevance
3. **No filtering** based on current state needs
4. **JSON serialization** adds overhead

### 3. Context Flow Through States

#### State: PROVIDE_GREETING
- **Context Sent**: Empty (first interaction)
- **Context Needed**: None
- **Waste**: None

#### State: ASK_CLARIFYING_QUESTIONS
- **Context Sent**: 
  - Full conversation history (1 greeting + 1 user message)
  - All session data
- **Context Needed**: Just the user's initial topic
- **Waste**: ~50% (greeting not needed)

#### State: CREATE_CONFIRMATION_PLAN
- **Context Sent**:
  - Full conversation history (greeting + topic + questions + answers)
  - All session data including stored answers
- **Context Needed**: Initial topic + clarifying answers
- **Waste**: ~40% (greeting, questions could be summarized)

#### State: GENERATE_STRAWMAN
- **Context Sent**:
  - Full conversation history (now 5-6 exchanges)
  - All session data including confirmation plan
- **Context Needed**: Confirmation plan + key requirements
- **Waste**: ~70% (early conversation not needed)

#### State: REFINE_STRAWMAN
- **Context Sent**:
  - Full conversation history (7+ exchanges)
  - All session data including full strawman
- **Context Needed**: Current strawman + specific refinement request
- **Waste**: ~80% (most history irrelevant)

### 4. Token Usage Growth Pattern

Assuming average message sizes:
- Greeting: 50 tokens
- User topic: 30 tokens
- Questions: 200 tokens
- Answers: 150 tokens
- Plan: 300 tokens
- Strawman: 2000 tokens
- Refinement: 100 tokens

**Cumulative Context Size by State:**
1. PROVIDE_GREETING: 0 tokens
2. ASK_CLARIFYING_QUESTIONS: 80 tokens
3. CREATE_CONFIRMATION_PLAN: 430 tokens
4. GENERATE_STRAWMAN: 730 tokens
5. REFINE_STRAWMAN: 2,830 tokens

**With multiple refinements**, context can easily exceed 5,000+ tokens.

### 5. Memory Persistence Issues

#### WebSocket Handler (src/handlers/websocket.py)
```python
# Lines 195-204
await self.sessions.add_to_history(session.id, {
    'role': 'user',
    'content': user_input,
    'intent': intent.dict()
})
await self.sessions.add_to_history(session.id, {
    'role': 'assistant',
    'state': session.current_state,
    'content': response
})
```

**Issues:**
- Every message stored in full
- Intent data adds overhead
- No cleanup or compression
- Pydantic objects stored as dicts (large)

### 6. Context Builder Limitations

The `ContextBuilder` class exists but is **not being used** by the Director!

```python
# src/utils/context_builder.py
def build_conversation_context(
    history: List[Dict[str, Any]], 
    max_messages: int = 10  # Has a limit!
) -> str:
```

This class has better practices but isn't integrated.

## Identified Problems

### 1. Exponential Token Growth
- Each state includes ALL previous context
- No sliding window or summarization
- Token usage grows exponentially

### 2. Redundant Information
- Session data duplicates conversation history
- Pydantic objects serialized multiple times
- Same information in different formats

### 3. State-Agnostic Context
- PROVIDE_GREETING doesn't need history but gets it
- GENERATE_STRAWMAN gets irrelevant early exchanges
- No state-specific filtering

### 4. No Token Awareness
- No counting of tokens before sending
- No graceful degradation near limits
- Risk of hitting model token limits

### 5. Serialization Overhead
- Complex objects fully serialized
- JSON conversion adds characters
- Pydantic dict() calls expensive

## Improvement Opportunities

### 1. State-Specific Context Strategy

```python
# Proposed approach
STATE_CONTEXT_NEEDS = {
    "PROVIDE_GREETING": {
        "history_depth": 0,
        "session_fields": []
    },
    "ASK_CLARIFYING_QUESTIONS": {
        "history_depth": 1,  # Just user topic
        "session_fields": ["user_initial_request"]
    },
    "CREATE_CONFIRMATION_PLAN": {
        "history_depth": 2,  # Topic + answers
        "session_fields": ["user_initial_request", "clarifying_answers"]
    },
    "GENERATE_STRAWMAN": {
        "history_depth": 0,  # Use summary instead
        "session_fields": ["confirmation_plan"]
    },
    "REFINE_STRAWMAN": {
        "history_depth": 1,  # Just refinement request
        "session_fields": ["presentation_strawman"]
    }
}
```

### 2. Context Summarization

After each major state transition, summarize:
```python
# After ASK_CLARIFYING_QUESTIONS
summary = {
    "topic": "AI in Healthcare",
    "audience": "Hospital administrators",
    "duration": "15 minutes",
    "focus": "Implementation strategies"
}
```

### 3. Sliding Window Approach

```python
def get_relevant_history(state: str, full_history: List) -> List:
    if state == "REFINE_STRAWMAN":
        # Only last user message and current strawman
        return full_history[-2:]
    elif state == "GENERATE_STRAWMAN":
        # Only confirmation plan exchange
        return [msg for msg in full_history if "plan" in msg]
    # etc...
```

### 4. Token Counting Integration

```python
def estimate_tokens(text: str) -> int:
    # Rough estimate: 4 characters = 1 token
    return len(text) // 4

def build_context_with_limit(data: Dict, limit: int = 3000) -> str:
    # Build context while tracking tokens
    # Prioritize recent/relevant information
    pass
```

### 5. Efficient Serialization

```python
def serialize_for_llm(obj: Any) -> str:
    if hasattr(obj, 'model_dump_json'):
        return obj.model_dump_json(exclude_none=True)
    elif isinstance(obj, dict):
        # Only include necessary fields
        return json.dumps({k: v for k, v in obj.items() if v})
    return str(obj)
```

### 6. Context Caching

```python
class ContextCache:
    def __init__(self):
        self.summaries = {}
        self.compressed_history = {}
    
    def get_or_compute_summary(self, session_id: str, state: str):
        # Cache computed summaries to avoid recomputation
        pass
```

## Recommendations

### Immediate Actions (Quick Wins)

1. **Use the existing ContextBuilder class** - It already has max_messages limit
2. **Filter session_data by state** - Only send what's needed
3. **Limit conversation history** - Use last 5 messages instead of all
4. **Add token counting** - Log token usage for monitoring

### Short-term Improvements

1. **Implement state-specific context** - Each state gets only what it needs
2. **Add context summarization** - Compress completed states
3. **Create sliding window** - Keep only recent relevant messages
4. **Optimize serialization** - Exclude null/empty fields

### Long-term Enhancements

1. **Semantic compression** - Use embeddings to find relevant context
2. **Async context building** - Pre-compute context while user types
3. **Token budget management** - Allocate tokens per state
4. **Context versioning** - Track what context produced what output

## Implementation Priority

1. **Critical**: Limit conversation history depth (prevent token overflow)
2. **High**: Implement state-specific filtering (reduce waste)
3. **Medium**: Add summarization after key states (compress context)
4. **Low**: Optimize serialization methods (performance gain)

## Conclusion

The current context management approach is unsustainable for longer conversations. The practice of sending the entire conversation history and all session data on every LLM call leads to:

- Exponential token usage growth
- Increased costs
- Higher latency
- Risk of hitting token limits
- Degraded performance over time

By implementing the recommended improvements, particularly state-specific context filtering and conversation summarization, token usage could be reduced by 60-80% while maintaining or improving response quality.