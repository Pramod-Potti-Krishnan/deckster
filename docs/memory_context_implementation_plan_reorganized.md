# Deckster Memory & Context Management - Reorganized Implementation Plan

## Executive Summary

This document outlines a reorganized plan to transform Deckster's memory system. The core insight: **the ContextBuilder is the foundation** that enables all other improvements. By establishing it first, subsequent phases become simple additions rather than major refactors.

- **Phase 1**: Implement state-aware ContextBuilder to drastically reduce token usage
- **Phase 2**: Optimize database schema to separate structured data  
- **Phase 3**: Add RAG capabilities for document-grounded generation

## Phase 1: State-Aware Context Builder (Week 1-2)

### Goal
Implement the core ContextBuilder module that intelligently selects only the necessary information for each workflow state. This foundational component will reduce token usage by 60%+ while maintaining quality.

### Why Phase 1?
- The ContextBuilder is the **core abstraction** that everything else plugs into
- Once established, adding database optimizations or RAG becomes trivial
- Immediate value: 60%+ token reduction without any database changes
- Easy to test: compare token counts before/after

### 1.1 Create the ContextBuilder Module

**File**: `src/utils/context_builder.py`

```python
from typing import Dict, List, Any, Optional
import json
from abc import ABC, abstractmethod

class StateContextStrategy(ABC):
    """Abstract base for state-specific context strategies"""
    
    @abstractmethod
    def build_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build minimal context for this state"""
        pass
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """List fields this state needs from session data"""
        pass

class GreetingStrategy(StateContextStrategy):
    """PROVIDE_GREETING needs almost nothing"""
    
    def build_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "is_returning_user": bool(session_data.get("conversation_history"))
        }
    
    def get_required_fields(self) -> List[str]:
        return []  # No specific fields needed

class ClarifyingQuestionsStrategy(StateContextStrategy):
    """ASK_CLARIFYING_QUESTIONS needs only the topic"""
    
    def build_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "user_initial_request": session_data.get("user_initial_request", "")
        }
    
    def get_required_fields(self) -> List[str]:
        return ["user_initial_request"]

class ConfirmationPlanStrategy(StateContextStrategy):
    """CREATE_CONFIRMATION_PLAN needs topic + answers"""
    
    def build_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "user_initial_request": session_data.get("user_initial_request", ""),
            "clarifying_answers": session_data.get("clarifying_answers", {})
        }
    
    def get_required_fields(self) -> List[str]:
        return ["user_initial_request", "clarifying_answers"]

class GenerateStrawmanStrategy(StateContextStrategy):
    """GENERATE_STRAWMAN needs the full context: plan + original request + Q&A"""
    
    def build_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        # Note: In Phase 1, plan might still be in conversation history
        # We'll extract it from there
        plan = self._extract_plan_from_session(session_data)
        
        # GENERATE_STRAWMAN needs the complete picture
        return {
            "user_initial_request": session_data.get("user_initial_request", ""),
            "clarifying_answers": session_data.get("clarifying_answers", {}),
            "confirmation_plan": plan
        }
    
    def get_required_fields(self) -> List[str]:
        return ["user_initial_request", "clarifying_answers"]  # Plus plan from history
    
    def _extract_plan_from_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract plan from conversation history (Phase 1 approach)"""
        # Look through conversation history for the plan
        for msg in reversed(session_data.get("conversation_history", [])):
            if msg.get("role") == "assistant":
                content = msg.get("content", {})
                if isinstance(content, dict) and content.get("type") == "ConfirmationPlan":
                    return content
        return {}

class RefineStrawmanStrategy(StateContextStrategy):
    """REFINE_STRAWMAN needs current content + recent feedback"""
    
    def build_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        # Get last 3 messages for refinement context
        recent_history = session_data.get("conversation_history", [])[-3:]
        
        # Extract refinement request
        refinement_request = ""
        for msg in reversed(recent_history):
            if msg.get("role") == "user":
                refinement_request = msg.get("content", "")
                break
        
        # Extract current strawman (Phase 1: from conversation history)
        current_strawman = self._extract_strawman_from_session(session_data)
        
        return {
            "current_strawman_summary": self._summarize_strawman(current_strawman),
            "refinement_request": refinement_request
        }
    
    def get_required_fields(self) -> List[str]:
        return []  # Will use conversation history in Phase 1
    
    def _extract_strawman_from_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract strawman from conversation history (Phase 1 approach)"""
        for msg in reversed(session_data.get("conversation_history", [])):
            if msg.get("role") == "assistant":
                content = msg.get("content", {})
                if isinstance(content, dict) and content.get("type") == "PresentationStrawman":
                    return content
        return {}
    
    def _summarize_strawman(self, strawman: Dict[str, Any]) -> Dict[str, Any]:
        """Create a lightweight summary instead of full content"""
        if not strawman:
            return {}
        
        slides = strawman.get("slides", [])
        return {
            "title": strawman.get("title", ""),
            "num_slides": len(slides),
            "slide_titles": [s.get("title", "") for s in slides]
        }

class ContextBuilder:
    """State-aware context builder - Phase 1 Core Component"""
    
    def __init__(self):
        self.strategies = {
            "PROVIDE_GREETING": GreetingStrategy(),
            "ASK_CLARIFYING_QUESTIONS": ClarifyingQuestionsStrategy(),
            "CREATE_CONFIRMATION_PLAN": ConfirmationPlanStrategy(),
            "GENERATE_STRAWMAN": GenerateStrawmanStrategy(),
            "REFINE_STRAWMAN": RefineStrawmanStrategy()
        }
    
    def build_context(
        self, 
        state: str, 
        session_data: Dict[str, Any],
        user_intent: Optional[Dict[str, Any]] = None
    ) -> tuple[Dict[str, Any], str]:
        """Build minimal context for the given state"""
        
        strategy = self.strategies.get(state)
        if not strategy:
            raise ValueError(f"No strategy defined for state: {state}")
        
        # Get minimal context from strategy
        context = strategy.build_context(session_data)
        
        # Add current state and intent
        context["current_state"] = state
        if user_intent:
            context["user_intent"] = user_intent
        
        # Generate prompt
        prompt = self._generate_prompt(state, context)
        
        return context, prompt
    
    def _generate_prompt(self, state: str, context: Dict[str, Any]) -> str:
        """Generate state-specific prompts with minimal context"""
        
        if state == "PROVIDE_GREETING":
            return "Provide a warm greeting and ask what presentation the user wants to create."
        
        elif state == "ASK_CLARIFYING_QUESTIONS":
            return f"""The user wants to create a presentation about:
{context.get('user_initial_request')}

Ask 3-5 clarifying questions about audience, duration, key messages, and focus areas."""
        
        elif state == "CREATE_CONFIRMATION_PLAN":
            return f"""Create a presentation plan based on:
Topic: {context.get('user_initial_request')}
Details: {json.dumps(context.get('clarifying_answers', {}), indent=2)}

Include title, 5-7 slides with key points, duration, and themes."""
        
        elif state == "GENERATE_STRAWMAN":
            return f"""Generate a complete presentation based on:

Original Request: {context.get('user_initial_request')}
User Requirements: {json.dumps(context.get('clarifying_answers', {}), indent=2)}
Approved Plan: {json.dumps(context.get('confirmation_plan', {}), indent=2)}

Create detailed content for each slide that incorporates all the above context."""
        
        elif state == "REFINE_STRAWMAN":
            summary = context.get('current_strawman_summary', {})
            return f"""Refine the presentation:
Current structure: {json.dumps(summary, indent=2)}
User request: {context.get('refinement_request')}

Make the requested changes."""
        
        return json.dumps(context)
    
    def estimate_tokens(self, text: str) -> int:
        """Simple token estimation"""
        return len(text) // 4
```

### 1.2 Add Token Tracking for Metrics

**File**: `src/utils/token_tracker.py`

```python
from typing import Dict, Any
from datetime import datetime

class TokenTracker:
    """Track token usage for before/after comparison"""
    
    def __init__(self):
        self.baseline_usage = {}  # Before context builder
        self.optimized_usage = {}  # After context builder
    
    async def track_baseline(self, session_id: str, state: str, tokens: int):
        """Track token usage before optimization"""
        if session_id not in self.baseline_usage:
            self.baseline_usage[session_id] = {}
        self.baseline_usage[session_id][state] = tokens
    
    async def track_optimized(self, session_id: str, state: str, tokens: int):
        """Track token usage after optimization"""
        if session_id not in self.optimized_usage:
            self.optimized_usage[session_id] = {}
        self.optimized_usage[session_id][state] = tokens
    
    def get_savings_report(self, session_id: str) -> Dict[str, Any]:
        """Calculate token savings"""
        baseline = self.baseline_usage.get(session_id, {})
        optimized = self.optimized_usage.get(session_id, {})
        
        report = {
            "states": {},
            "total_baseline": sum(baseline.values()),
            "total_optimized": sum(optimized.values()),
            "total_savings": 0,
            "percentage_saved": 0
        }
        
        for state in baseline:
            if state in optimized:
                saved = baseline[state] - optimized[state]
                report["states"][state] = {
                    "baseline": baseline[state],
                    "optimized": optimized[state],
                    "saved": saved,
                    "percentage": (saved / baseline[state] * 100) if baseline[state] > 0 else 0
                }
        
        if report["total_baseline"] > 0:
            report["total_savings"] = report["total_baseline"] - report["total_optimized"]
            report["percentage_saved"] = (report["total_savings"] / report["total_baseline"]) * 100
        
        return report
```

### 1.3 Integrate ContextBuilder into Director

**Changes to**: `src/agents/director.py`

```python
from src.utils.context_builder import ContextBuilder
from src.utils.token_tracker import TokenTracker

class DirectorWorkflow:
    def __init__(self, agents: Dict[str, Any], llm_client: Any):
        self.agents = agents
        self.llm_client = llm_client
        
        # Phase 1: Add context builder and token tracker
        self.context_builder = ContextBuilder()
        self.token_tracker = TokenTracker()
        
        # Feature flag for A/B testing
        self.use_context_builder = True  # Can toggle for comparison
    
    async def process(self, state_context: StateContext) -> str:
        """Process with optional state-aware context"""
        
        session_id = state_context.session_data.get("id")
        
        if self.use_context_builder:
            # NEW: Use context builder for minimal context
            context, prompt = self.context_builder.build_context(
                state=state_context.current_state,
                session_data={
                    "id": session_id,
                    "user_initial_request": state_context.session_data.get("user_initial_request"),
                    "clarifying_answers": state_context.session_data.get("clarifying_answers"),
                    "conversation_history": state_context.conversation_history
                },
                user_intent=state_context.user_intent.dict() if state_context.user_intent else None
            )
            
            # Track optimized token usage
            token_count = self.context_builder.estimate_tokens(prompt)
            await self.token_tracker.track_optimized(
                session_id,
                state_context.current_state,
                token_count
            )
            
            logger.info(
                f"Context Builder - State: {state_context.current_state}, "
                f"Tokens: {token_count}"
            )
        else:
            # BASELINE: Full context as before
            prompt = f"""
            Current state: {state_context.current_state}
            Conversation history: {json.dumps(state_context.conversation_history)}
            Session data: {json.dumps(state_context.session_data)}
            
            Process according to the rules for state {state_context.current_state}.
            """
            
            # Track baseline token usage
            token_count = len(prompt) // 4
            await self.token_tracker.track_baseline(
                session_id,
                state_context.current_state,
                token_count
            )
            
            logger.info(
                f"Full Context - State: {state_context.current_state}, "
                f"Tokens: {token_count}"
            )
        
        # Call LLM with appropriate prompt
        response = await self.llm_client.generate(prompt)
        
        return response
```

### 1.4 Phase 1 Testing Strategy

```python
# test_phase1_context_builder.py
async def test_token_reduction():
    """Verify significant token reduction per state"""
    
    # Create test session with full conversation
    test_session = create_test_session_with_full_history()
    
    # Test both modes
    director = DirectorWorkflow(agents, llm_client)
    
    # Run with full context (baseline)
    director.use_context_builder = False
    await run_all_states(director, test_session)
    
    # Run with context builder
    director.use_context_builder = True
    await run_all_states(director, test_session)
    
    # Get savings report
    report = director.token_tracker.get_savings_report(test_session["id"])
    
    # Verify expectations
    assert report["percentage_saved"] > 60, f"Expected >60% savings, got {report['percentage_saved']}%"
    
    # Print detailed report
    print("\n=== Token Savings Report ===")
    for state, data in report["states"].items():
        print(f"{state}: {data['baseline']} → {data['optimized']} (saved {data['percentage']:.1f}%)")
    print(f"\nTotal: {report['total_baseline']} → {report['total_optimized']} (saved {report['percentage_saved']:.1f}%)")

async def test_quality_maintained():
    """Ensure output quality is maintained with reduced context"""
    # Run parallel tests with human evaluation
    # Compare outputs between full context and context builder
    pass
```

### Phase 1 Deliverables & Success Metrics

**Deliverables**:
- ✅ ContextBuilder module with state-specific strategies
- ✅ Token tracking for comparison
- ✅ Feature flag for A/B testing
- ✅ Comprehensive test suite

**Success Metrics**:
- [ ] Token usage reduced by 60%+ across all states
- [ ] All conversation flows pass with context builder
- [ ] No degradation in output quality
- [ ] Clear documentation of token savings per state

**Key Achievement**: The core abstraction is now in place. Adding database optimizations or RAG becomes a simple enhancement to the existing strategies.

---

## Phase 2: Database Schema Optimization (Week 3)

### Goal
Optimize data storage by separating structured artifacts (plans, presentations) from conversation history. This builds on Phase 1's ContextBuilder by providing cleaner data access.

### Why Phase 2 Now?
- ContextBuilder is already working and tested
- Database changes become a simple optimization
- Strategies can be updated to use dedicated columns instead of searching history
- No risk to core functionality - ContextBuilder provides abstraction

### 2.1 Database Schema Update

```sql
-- Add dedicated columns for structured data
ALTER TABLE sessions ADD COLUMN confirmation_plan JSONB;
ALTER TABLE sessions ADD COLUMN presentation_strawman JSONB;
ALTER TABLE sessions ADD COLUMN session_summary TEXT;
```

### 2.2 Update SessionManager

**Changes to**: `src/utils/session_manager.py`

```python
async def save_session_data(self, session_id: str, field: str, data: Any):
    """Save specific session data fields to dedicated columns"""
    if field in ["confirmation_plan", "presentation_strawman", "session_summary"]:
        update_data = {field: data}
        await self.supabase.update_session(session_id, update_data)
        
        # Update cache
        session = self.cache.get(session_id)
        if session:
            setattr(session, field, data)
```

### 2.3 Update ContextBuilder Strategies

**Simple Update to**: `src/utils/context_builder.py`

```python
class GenerateStrawmanStrategy(StateContextStrategy):
    """Updated to use dedicated column"""
    
    def build_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        # Phase 2: Use dedicated column instead of searching history
        plan = session_data.get("confirmation_plan", {})
        
        # Fallback to Phase 1 approach if needed
        if not plan:
            plan = self._extract_plan_from_session(session_data)
        
        # Still need all context components
        return {
            "user_initial_request": session_data.get("user_initial_request", ""),
            "clarifying_answers": session_data.get("clarifying_answers", {}),
            "confirmation_plan": plan
        }

class RefineStrawmanStrategy(StateContextStrategy):
    """Updated to use dedicated column"""
    
    def build_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        # Phase 2: Use dedicated column
        current_strawman = session_data.get("presentation_strawman", {})
        
        # Fallback to Phase 1 approach if needed
        if not current_strawman:
            current_strawman = self._extract_strawman_from_session(session_data)
        
        # Rest remains the same...
```

### Phase 2 Deliverables & Success Metrics

**Deliverables**:
- ✅ Optimized database schema
- ✅ Updated strategies using dedicated columns
- ✅ Migration script for existing data

**Success Metrics**:
- [ ] Data correctly migrated to new columns
- [ ] Faster data access (no more searching through history)
- [ ] ContextBuilder seamlessly uses new structure
- [ ] Zero functional regressions

---

## Phase 3: RAG Integration (Week 4-5)

### Goal
Enhance the ContextBuilder with RAG capabilities to ground presentations in user-provided documents. This becomes a simple addition to existing strategies.

### Why Phase 3 Last?
- ContextBuilder provides the perfect integration point
- Just need to enhance specific strategies with RAG
- Core system already optimized and stable
- RAG becomes an enhancement, not a requirement

### 3.1 RAG Infrastructure

```sql
CREATE TABLE user_document_chunks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    source_filename TEXT
);
```

### 3.2 Update ContextBuilder with RAG

**Enhance existing strategies in**: `src/utils/context_builder.py`

```python
class RAGEnhancedGenerateStrawmanStrategy(GenerateStrawmanStrategy):
    """Phase 3: Add RAG to existing strategy"""
    
    def __init__(self, rag_service=None):
        self.rag = rag_service
    
    async def build_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        # Get base context from parent
        context = super().build_context(session_data)
        
        # Phase 3: Augment with RAG if available
        if self.rag and session_data.get("id"):
            plan = context.get("confirmation_plan", {})
            query = f"{plan.get('title', '')} {' '.join(plan.get('key_themes', []))}"
            
            retrieved = await self.rag.retrieve(
                session_data["id"], 
                query, 
                top_k=10
            )
            
            if retrieved:
                context["retrieved_knowledge"] = retrieved
        
        return context

# Update ContextBuilder to use enhanced strategies when RAG available
class ContextBuilder:
    def __init__(self, rag_service=None):
        # Base strategies
        base_strategies = {
            "PROVIDE_GREETING": GreetingStrategy(),
            "ASK_CLARIFYING_QUESTIONS": ClarifyingQuestionsStrategy(),
            "CREATE_CONFIRMATION_PLAN": ConfirmationPlanStrategy(),
            "GENERATE_STRAWMAN": GenerateStrawmanStrategy(),
            "REFINE_STRAWMAN": RefineStrawmanStrategy()
        }
        
        # Phase 3: Use RAG-enhanced strategies if available
        if rag_service:
            base_strategies["GENERATE_STRAWMAN"] = RAGEnhancedGenerateStrawmanStrategy(rag_service)
            base_strategies["ASK_CLARIFYING_QUESTIONS"] = RAGEnhancedClarifyingQuestionsStrategy(rag_service)
        
        self.strategies = base_strategies
```

### Phase 3 Deliverables & Success Metrics

**Deliverables**:
- ✅ Document processing pipeline
- ✅ RAG-enhanced strategies
- ✅ Seamless integration with existing ContextBuilder

**Success Metrics**:
- [ ] Documents processed and searchable
- [ ] Generated content includes facts from documents
- [ ] Questions reduced when answers in documents
- [ ] System works with or without documents

---

## Implementation Timeline

### Week 1-2: Phase 1 - ContextBuilder Foundation
- Day 1-3: Implement core ContextBuilder with strategies
- Day 4-5: Add token tracking and metrics
- Day 6-7: Integrate with Director
- Day 8-10: Extensive testing and validation

### Week 3: Phase 2 - Database Optimization
- Day 1: Schema updates
- Day 2: Update SessionManager
- Day 3: Update ContextBuilder strategies
- Day 4-5: Migration and testing

### Week 4-5: Phase 3 - RAG Enhancement
- Day 1-2: RAG infrastructure
- Day 3-4: Document processor
- Day 5-6: Enhance ContextBuilder strategies
- Day 7-10: Integration testing

## Key Benefits of This Approach

1. **Foundation First**: ContextBuilder is the core that enables everything
2. **Incremental Value**: Each phase delivers immediate benefits
3. **Low Risk**: Each phase builds on stable foundation
4. **Easy Testing**: Clear before/after comparisons at each phase
5. **Flexible**: Can stop at any phase with full value delivered

## Summary

By making the ContextBuilder the Phase 1 focus, we:
- Establish the core abstraction immediately
- Get 60%+ token savings without database changes
- Make subsequent phases simple additions rather than major changes
- Reduce risk and complexity throughout the project

The reorganized approach recognizes that **the ContextBuilder is the heart of the system** - once it's in place, everything else becomes a natural extension.