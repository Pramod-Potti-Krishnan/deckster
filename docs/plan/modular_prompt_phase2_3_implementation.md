# Modular Prompt System - Phase 2 & 3 Implementation Guide

## Overview

This document outlines the implementation plan for Phase 2 (Modular System Implementation) and Phase 3 (Testing & Validation) of the Deckster modular prompt architecture.

### Current State (Phase 1 Complete)
- ✅ Modular prompt files created in `config/prompts/modular/`
- ✅ Base prompt and state-specific prompts separated
- ✅ Shared components integrated into GENERATE_STRAWMAN and REFINE_STRAWMAN

### Goals
- Reduce token usage by 60-70% for simple states
- Improve maintainability and flexibility
- Enable A/B testing between monolithic and modular approaches
- Maintain or improve output quality

---

## Phase 2: Modular System Implementation

### 2.1 PromptManager Class

Create a new file: `src/utils/prompt_manager.py`

```python
import os
from typing import Dict, Optional
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class PromptManager:
    """Manages loading and caching of modular prompts"""
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._base_path = Path(__file__).parent.parent.parent / "config/prompts"
        self._modular_path = self._base_path / "modular"
        self._fallback_path = self._base_path / "director_prompt.md"
        
    def get_modular_prompt(self, state: str) -> str:
        """Get the complete prompt for a given state"""
        cache_key = f"modular_{state}"
        
        if cache_key in self._cache:
            logger.debug(f"Using cached prompt for state: {state}")
            return self._cache[cache_key]
        
        try:
            # Load base prompt
            base = self._load_file("base_prompt.md")
            
            # Map state names to file names
            state_file_map = {
                "PROVIDE_GREETING": "provide_greeting.md",
                "ASK_CLARIFYING_QUESTIONS": "ask_clarifying_questions.md",
                "CREATE_CONFIRMATION_PLAN": "create_confirmation_plan.md",
                "GENERATE_STRAWMAN": "generate_strawman.md",
                "REFINE_STRAWMAN": "refine_strawman.md"
            }
            
            state_file = state_file_map.get(state)
            if not state_file:
                raise ValueError(f"Unknown state: {state}")
            
            # Load state-specific prompt
            state_prompt = self._load_file(state_file)
            
            # Combine prompts
            combined = f"{base}\n\n{state_prompt}"
            
            # Cache the result
            self._cache[cache_key] = combined
            logger.info(f"Loaded modular prompt for state: {state} ({len(combined)} chars)")
            
            return combined
            
        except Exception as e:
            logger.error(f"Failed to load modular prompt for {state}: {e}")
            return self._get_fallback_prompt()
    
    def _load_file(self, filename: str) -> str:
        """Load a prompt file from the modular directory"""
        file_path = self._modular_path / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    
    def _get_fallback_prompt(self) -> str:
        """Get the monolithic fallback prompt"""
        if "fallback" not in self._cache:
            try:
                with open(self._fallback_path, 'r', encoding='utf-8') as f:
                    self._cache["fallback"] = f.read()
            except Exception as e:
                logger.error(f"Failed to load fallback prompt: {e}")
                # Return minimal fallback
                return "You are Deckster, an AI presentation assistant."
        
        return self._cache["fallback"]
    
    def clear_cache(self):
        """Clear the prompt cache (useful for development)"""
        self._cache.clear()
        logger.info("Prompt cache cleared")
```

### 2.2 DirectorAgent Modifications

Update `src/agents/director.py`:

```python
# Add to imports
from src.utils.prompt_manager import PromptManager

class DirectorAgent:
    def __init__(self):
        # ... existing initialization code ...
        
        # Add modular prompt support
        self.use_modular_prompts = settings.USE_MODULAR_PROMPTS
        self.prompt_manager = PromptManager() if self.use_modular_prompts else None
        
        if self.use_modular_prompts:
            logger.info("DirectorAgent using MODULAR prompt system")
            # Create agents with minimal system prompt
            self._init_modular_agents(model, model_turbo)
        else:
            logger.info("DirectorAgent using MONOLITHIC prompt system")
            # Existing agent initialization
            self._init_monolithic_agents(model, model_turbo)
    
    def _init_modular_agents(self, model, model_turbo):
        """Initialize agents for modular prompt system"""
        # Use minimal system prompt for all agents
        minimal_prompt = "You are Deckster, an AI presentation assistant."
        
        self.greeting_agent = Agent(
            model=model,
            output_type=str,
            system_prompt=minimal_prompt,
            retries=2,
            name="director_greeting_modular"
        )
        
        self.questions_agent = Agent(
            model=model,
            output_type=ClarifyingQuestions,
            system_prompt=minimal_prompt,
            retries=2,
            name="director_questions_modular"
        )
        
        self.plan_agent = Agent(
            model=model,
            output_type=ConfirmationPlan,
            system_prompt=minimal_prompt,
            retries=2,
            name="director_plan_modular"
        )
        
        self.strawman_agent = Agent(
            model=model_turbo,
            output_type=PresentationStrawman,
            system_prompt=minimal_prompt,
            retries=2,
            name="director_strawman_modular"
        )
    
    def _init_monolithic_agents(self, model, model_turbo):
        """Keep existing agent initialization for backward compatibility"""
        system_prompt = self._get_system_prompt()
        
        self.greeting_agent = Agent(
            model=model,
            output_type=str,
            system_prompt=system_prompt,
            retries=2,
            name="director_greeting"
        )
        # ... rest of existing agent initialization ...
```

### 2.3 ContextBuilder Enhancements

Update `src/utils/context_builder.py`:

```python
class ContextBuilder:
    def __init__(self):
        # ... existing initialization ...
        self.prompt_manager = None  # Will be set by DirectorAgent if modular
    
    def build_system_prompt(self, state: str) -> str:
        """Build state-specific system prompt for modular approach"""
        if not self.prompt_manager:
            raise ValueError("PromptManager not configured for modular prompts")
        
        return self.prompt_manager.get_modular_prompt(state)
    
    def build_context_with_modular_prompt(
        self, 
        state: str, 
        session_data: Dict[str, Any],
        user_intent: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], str, str]:
        """Build context and return both user and system prompts"""
        
        # Get minimal context as before
        context, user_prompt = self.build_context(state, session_data, user_intent)
        
        # Get state-specific system prompt
        system_prompt = self.build_system_prompt(state)
        
        return context, user_prompt, system_prompt
```

### 2.4 Update DirectorAgent.run Method

Modify the `run` method in `DirectorAgent`:

```python
async def run(self, context: StateContext, session_id: str) -> Union[str, ClarifyingQuestions, ConfirmationPlan, PresentationStrawman]:
    """Run the director agent for the given state context."""
    try:
        if self.use_modular_prompts:
            # Modular approach
            context_data, user_prompt, system_prompt = (
                self.context_builder.build_context_with_modular_prompt(
                    context.current_state,
                    context.session_data,
                    context.user_intent
                )
            )
            
            # Track token usage
            user_tokens = len(user_prompt) // 4
            system_tokens = len(system_prompt) // 4
            
            await self.token_tracker.track_modular(
                session_id,
                context.current_state,
                user_tokens,
                system_tokens
            )
            
            logger.info(
                f"Modular Prompt - State: {context.current_state}, "
                f"User Tokens: {user_tokens}, System Tokens: {system_tokens}, "
                f"Total: {user_tokens + system_tokens}"
            )
            
            # Create a temporary agent with the state-specific prompt
            agent = self._get_agent_for_state(context.current_state)
            
            # Run with state-specific system prompt injected
            result = await agent.run(
                user_prompt,
                model_settings=self._get_model_settings(context.current_state),
                # Override system prompt for this call
                system_prompt_override=system_prompt
            )
            
        else:
            # Existing monolithic approach
            # ... existing implementation ...
```

### 2.5 Feature Flag Configuration

Add to `config/settings.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Modular Prompt System
    USE_MODULAR_PROMPTS: bool = Field(
        default=False,
        description="Enable modular prompt system (experimental)"
    )
    
    # A/B Testing
    MODULAR_PROMPT_PERCENTAGE: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Percentage of sessions to use modular prompts (0-100)"
    )
```

---

## Phase 3: Testing & Validation

### 3.1 A/B Testing Framework

Create `src/utils/ab_testing.py`:

```python
import random
from typing import Dict, Any
import hashlib

class ABTestManager:
    """Manage A/B testing for modular prompts"""
    
    def __init__(self, percentage: int = 0):
        self.percentage = percentage
    
    def should_use_modular(self, session_id: str) -> bool:
        """Deterministically decide if session should use modular prompts"""
        if self.percentage == 0:
            return False
        if self.percentage == 100:
            return True
        
        # Use hash for consistent assignment
        hash_value = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        return (hash_value % 100) < self.percentage
```

### 3.2 Quality Metrics Tracking

Enhance `src/utils/token_tracker.py`:

```python
class TokenTracker:
    # ... existing code ...
    
    async def track_modular(
        self,
        session_id: str,
        state: str,
        user_tokens: int,
        system_tokens: int
    ):
        """Track token usage for modular system"""
        logfire.info(
            "modular_token_usage",
            session_id=session_id,
            state=state,
            user_tokens=user_tokens,
            system_tokens=system_tokens,
            total_tokens=user_tokens + system_tokens,
            prompt_type="modular"
        )
    
    async def track_quality_metrics(
        self,
        session_id: str,
        state: str,
        prompt_type: str,  # "modular" or "monolithic"
        metrics: Dict[str, Any]
    ):
        """Track quality metrics for comparison"""
        logfire.info(
            "quality_metrics",
            session_id=session_id,
            state=state,
            prompt_type=prompt_type,
            **metrics
        )
```

### 3.3 Test Suite

Create `test/test_modular_prompts.py`:

```python
import pytest
import asyncio
from src.agents.director import DirectorAgent
from src.models.agents import StateContext

class TestModularPrompts:
    """Test suite for modular prompt system"""
    
    @pytest.fixture
    async def monolithic_agent(self):
        """Create agent with monolithic prompts"""
        import os
        os.environ["USE_MODULAR_PROMPTS"] = "false"
        return DirectorAgent()
    
    @pytest.fixture
    async def modular_agent(self):
        """Create agent with modular prompts"""
        import os
        os.environ["USE_MODULAR_PROMPTS"] = "true"
        return DirectorAgent()
    
    async def test_output_parity(self, monolithic_agent, modular_agent):
        """Ensure outputs are equivalent between systems"""
        test_context = StateContext(
            current_state="ASK_CLARIFYING_QUESTIONS",
            session_data={"user_initial_request": "Create a presentation about AI"},
            conversation_history=[],
            user_intent=None
        )
        
        # Run both agents
        mono_result = await monolithic_agent.run(test_context, "test_mono")
        mod_result = await modular_agent.run(test_context, "test_mod")
        
        # Compare outputs
        assert len(mono_result.questions) == len(mod_result.questions)
        assert all(3 <= len(q) <= 5 for q in mod_result.questions)
    
    async def test_token_reduction(self, modular_agent):
        """Verify token usage reduction"""
        # Implementation to verify token usage is reduced
        pass
```

### 3.4 Rollout Strategy

1. **Week 1-2: Internal Testing**
   - Enable for 5% of internal test sessions
   - Monitor quality metrics and token usage
   - Fix any issues discovered

2. **Week 3-4: Limited Rollout**
   - Increase to 25% of sessions
   - A/B test results analysis
   - Performance optimization

3. **Week 5-6: Expanded Testing**
   - 50% rollout
   - Comprehensive metrics analysis
   - User feedback collection

4. **Week 7-8: Full Rollout**
   - 100% if metrics are positive
   - Keep feature flag for emergency rollback

---

## Risk Management

### Monitoring Queries (Logfire)

```sql
-- Token usage comparison
SELECT 
    prompt_type,
    state,
    AVG(total_tokens) as avg_tokens,
    COUNT(*) as session_count
FROM token_usage
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY prompt_type, state;

-- Quality metrics comparison
SELECT 
    prompt_type,
    AVG(response_quality_score) as avg_quality,
    AVG(response_time_ms) as avg_latency
FROM quality_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY prompt_type;
```

### Rollback Procedure

1. **Immediate Rollback**
   ```bash
   # Set environment variable
   export USE_MODULAR_PROMPTS=false
   # Restart service
   ```

2. **Gradual Rollback**
   ```bash
   # Reduce percentage gradually
   export MODULAR_PROMPT_PERCENTAGE=25  # From 50%
   ```

---

## Success Criteria

### Quantitative Metrics
- ✅ 60%+ reduction in system prompt tokens for simple states
- ✅ 40%+ reduction in system prompt tokens for complex states
- ✅ No increase in p95 latency beyond 50ms
- ✅ Error rate remains below 0.1%

### Qualitative Metrics
- ✅ Output quality maintained (human evaluation)
- ✅ No degradation in user satisfaction
- ✅ Easier prompt maintenance and updates

---

## Next Steps

1. Review and approve this implementation plan
2. Create feature branch for Phase 2 implementation
3. Implement PromptManager and DirectorAgent modifications
4. Set up A/B testing framework
5. Deploy to staging environment for testing
6. Begin phased rollout based on metrics