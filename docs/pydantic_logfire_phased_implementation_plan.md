# Pydantic Logfire Phased Implementation Plan for Deckster

## Executive Summary

This document outlines a systematic, phased approach to implementing Pydantic Logfire in the Deckster project. The plan prioritizes minimal risk, maximum observability gain, and careful validation at each stage to ensure we successfully track token usage and system performance.

## Implementation Phases Overview

```
Phase 1: Basic Setup & Validation (1-2 days)
  ↓
Phase 2: PydanticAI Agent Instrumentation (2-3 days)
  ↓
Phase 3: Enhanced Context & Metrics (2-3 days)
  ↓
Phase 4: Production Deployment (1-2 days)
  ↓
Phase 5: Advanced Features & Optimization (Ongoing)
```

## Phase 1: Basic Setup & Validation

### Objective
Establish Logfire connection and verify basic functionality without modifying existing application logic.

### Tasks

#### 1.1 Environment Setup
```bash
# Add to .env.local (development)
LOGFIRE_TOKEN=your-dev-write-token
LOGFIRE_ENVIRONMENT=development
LOGFIRE_CONSOLE=true  # Enable console output for verification
```

#### 1.2 Create Logfire Configuration Module
Create `src/utils/logfire_config.py`:
```python
"""
Centralized Logfire configuration for Deckster.
"""
import os
import logfire
from typing import Optional

_configured = False

def configure_logfire(force: bool = False) -> bool:
    """
    Configure Logfire with proper error handling.
    
    Args:
        force: Force reconfiguration even if already configured
        
    Returns:
        bool: True if successfully configured
    """
    global _configured
    
    if _configured and not force:
        return True
    
    token = os.getenv("LOGFIRE_TOKEN")
    if not token:
        print("WARNING: LOGFIRE_TOKEN not set, Logfire disabled")
        return False
    
    try:
        logfire.configure(
            token=token,
            environment=os.getenv("LOGFIRE_ENVIRONMENT", "development"),
            console=os.getenv("LOGFIRE_CONSOLE", "false").lower() == "true",
            service_name="deckster",
            service_version=os.getenv("APP_VERSION", "dev")
        )
        
        # Test with a simple log
        logfire.info("Logfire configured successfully")
        _configured = True
        return True
        
    except Exception as e:
        print(f"ERROR: Logfire configuration failed: {e}")
        _configured = False
        return False

def is_configured() -> bool:
    """Check if Logfire is configured."""
    return _configured
```

#### 1.3 Update Main Entry Point
Modify `main.py` to configure Logfire early:
```python
# At the top of main.py, after imports
from src.utils.logfire_config import configure_logfire

# Configure Logfire before anything else
configure_logfire()

# Rest of the application...
```

#### 1.4 Create Test Script
Create `test/test_logfire_setup.py`:
```python
"""
Test script to verify Logfire setup.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logfire_config import configure_logfire
import logfire

async def test_basic_logging():
    """Test basic Logfire functionality."""
    print("Testing Logfire setup...")
    
    if not configure_logfire():
        print("❌ Logfire configuration failed")
        return False
    
    # Test different log levels
    logfire.info("Test info message", test_data={"key": "value"})
    logfire.warn("Test warning message", count=42)
    logfire.error("Test error message", error_code="TEST_001")
    
    # Test span
    with logfire.span("test_operation", test_id="12345") as span:
        logfire.info("Inside test span")
        span.set_attribute("result", "success")
    
    print("✅ Logfire basic tests completed")
    print("Check your Logfire dashboard to verify logs are appearing")
    return True

if __name__ == "__main__":
    asyncio.run(test_basic_logging())
```

### Validation Criteria
- [ ] Logfire configuration succeeds without errors
- [ ] Test logs appear in Logfire dashboard
- [ ] Console output works in development
- [ ] Application runs normally with Logfire enabled
- [ ] No performance degradation observed

### Rollback Plan
If issues occur:
1. Set `LOGFIRE_TOKEN=""` in environment
2. The application continues with existing logging

## Phase 2: PydanticAI Agent Instrumentation

### Objective
Instrument PydanticAI agents to track token usage and response times.

### Tasks

#### 2.1 Update Logfire Configuration
Add PydanticAI instrumentation to `src/utils/logfire_config.py`:
```python
def instrument_agents():
    """Instrument PydanticAI agents if Logfire is configured."""
    if not is_configured():
        return False
    
    try:
        import logfire
        # This single line instruments ALL PydanticAI agents
        logfire.instrument_pydantic_ai()
        logfire.info("PydanticAI instrumentation enabled")
        return True
    except Exception as e:
        logfire.error(f"Failed to instrument PydanticAI: {e}")
        return False
```

#### 2.2 Update Director Agent
Modify `src/agents/director.py` to add instrumentation:
```python
# After imports
from src.utils.logfire_config import instrument_agents

class DirectorAgent:
    def __init__(self):
        """Initialize state-specific agents with Logfire instrumentation."""
        # Instrument agents after Logfire is configured
        instrument_agents()
        
        # Rest of initialization...
```

#### 2.3 Create Token Tracking Test
Create `test/test_token_tracking.py`:
```python
"""
Test token usage tracking with Logfire.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logfire_config import configure_logfire, instrument_agents
from src.agents.director import DirectorAgent
from src.models.agents import StateContext
import logfire

async def test_token_tracking():
    """Test that token usage is being tracked."""
    print("Testing token tracking...")
    
    # Configure and instrument
    if not configure_logfire():
        print("❌ Logfire configuration failed")
        return
    
    instrument_agents()
    
    # Create agent and context
    director = DirectorAgent()
    context = StateContext(
        current_state="PROVIDE_GREETING",
        conversation_history=[],
        session_data={}
    )
    
    # Track the operation
    with logfire.span("test_token_tracking") as span:
        # Run agent
        result = await director.process(context)
        
        # Log result
        logfire.info(
            "Director response generated",
            state="PROVIDE_GREETING",
            response_length=len(str(result))
        )
    
    print("✅ Token tracking test completed")
    print("Check Logfire dashboard for:")
    print("- Span named 'test_token_tracking'")
    print("- Token usage attributes (gen_ai.usage.*)")
    print("- Response time metrics")

if __name__ == "__main__":
    asyncio.run(test_token_tracking())
```

#### 2.4 Create Dashboard Queries
Document useful Logfire queries for the team:
```sql
-- Total tokens by agent
SELECT 
    attributes->>'agent_name' as agent,
    SUM(CAST(attributes->>'gen_ai.usage.total_tokens' AS INT)) as total_tokens
FROM spans
WHERE attributes->>'gen_ai.usage.total_tokens' IS NOT NULL
GROUP BY 1
ORDER BY 2 DESC;

-- Token usage over time
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    SUM(CAST(attributes->>'gen_ai.usage.total_tokens' AS INT)) as tokens
FROM spans
WHERE attributes->>'gen_ai.usage.total_tokens' IS NOT NULL
GROUP BY 1
ORDER BY 1;
```

### Validation Criteria
- [ ] All PydanticAI agents are instrumented
- [ ] Token usage appears in Logfire dashboard
- [ ] Input/output tokens are tracked separately
- [ ] Response times are recorded
- [ ] No errors in agent execution

## Phase 3: Enhanced Context & Metrics

### Objective
Add session tracking, state machine monitoring, and custom metrics.

### Tasks

#### 3.1 Create Session Context Manager
Create `src/utils/logfire_context.py`:
```python
"""
Context managers for enhanced Logfire tracking.
"""
import logfire
from contextlib import contextmanager
from typing import Optional

@contextmanager
def session_context(session_id: str, user_id: Optional[str] = None):
    """
    Context manager for tracking session-wide operations.
    
    Usage:
        with session_context(session_id, user_id):
            # All operations here will be tagged with session
    """
    with logfire.span(
        "session",
        session_id=session_id,
        user_id=user_id
    ) as span:
        # Make session_id available to all nested spans
        logfire.set_attribute("session_id", session_id)
        if user_id:
            logfire.set_attribute("user_id", user_id)
        yield span

@contextmanager
def state_transition_span(
    from_state: str,
    to_state: str,
    session_id: str
):
    """Track state machine transitions."""
    with logfire.span(
        "state_transition",
        from_state=from_state,
        to_state=to_state,
        session_id=session_id
    ) as span:
        yield span
```

#### 3.2 Instrument State Machine
Update `src/workflows/state_machine.py`:
```python
# Add import
from src.utils.logfire_context import state_transition_span
import logfire

class WorkflowOrchestrator:
    async def transition_state(self, context: StateContext, new_state: str):
        """Transition to a new state with tracking."""
        old_state = context.current_state
        
        with state_transition_span(
            from_state=old_state,
            to_state=new_state,
            session_id=context.session_id
        ):
            # Log transition
            logfire.info(
                "State transition",
                from_state=old_state,
                to_state=new_state,
                conversation_length=len(context.conversation_history)
            )
            
            # Perform transition
            context.current_state = new_state
            
            # Track metric
            logfire.metric(
                "state_transitions",
                1,
                state=new_state
            )
```

#### 3.3 Add Cost Tracking
Create `src/utils/token_cost_tracker.py`:
```python
"""
Track and estimate token costs.
"""
import logfire
from typing import Dict, Optional

# Approximate costs per 1K tokens (update as needed)
TOKEN_COSTS = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
    "gemini-2.5-flash": {"input": 0.0001, "output": 0.0003},
    "gemini-2.5-pro": {"input": 0.001, "output": 0.003},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-opus": {"input": 0.015, "output": 0.075}
}

def track_token_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    session_id: Optional[str] = None
):
    """Calculate and track token costs."""
    # Find model in costs table
    model_key = None
    for key in TOKEN_COSTS:
        if key in model.lower():
            model_key = key
            break
    
    if not model_key:
        logfire.warn(f"Unknown model for cost tracking: {model}")
        return
    
    # Calculate costs
    input_cost = (input_tokens / 1000) * TOKEN_COSTS[model_key]["input"]
    output_cost = (output_tokens / 1000) * TOKEN_COSTS[model_key]["output"]
    total_cost = input_cost + output_cost
    
    # Log cost metrics
    logfire.metric(
        "token_cost_usd",
        total_cost,
        model=model,
        session_id=session_id
    )
    
    logfire.info(
        "Token cost calculated",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=round(total_cost, 4)
    )
```

#### 3.4 Create Monitoring Dashboard
Document key metrics to monitor:

**Real-time Metrics:**
- Active sessions
- Tokens per minute
- Cost per hour
- Error rate

**Session Metrics:**
- Average session duration
- States per session
- Total tokens per session
- Session success rate

**Agent Metrics:**
- Tokens per agent
- Response time per agent
- Error rate per agent
- Most expensive operations

### Validation Criteria
- [ ] Session tracking works end-to-end
- [ ] State transitions are logged
- [ ] Token costs are estimated
- [ ] Custom metrics appear in dashboard
- [ ] No performance impact

## Phase 4: Production Deployment

### Objective
Deploy Logfire to production with proper configuration and monitoring.

### Tasks

#### 4.1 Production Configuration
Update Railway environment variables:
```bash
# Production Logfire settings
LOGFIRE_TOKEN=your-production-write-token
LOGFIRE_ENVIRONMENT=production
LOGFIRE_CONSOLE=false
LOGFIRE_TRACE_SAMPLE_RATE=0.1  # Sample 10% of traces
APP_VERSION=1.0.0  # Your version
```

#### 4.2 Add Monitoring Alerts
Configure Logfire alerts for:
- High token usage (>10K tokens/minute)
- High error rate (>5% of requests)
- Slow response times (>10s for any agent)
- Cost threshold ($10/hour)

#### 4.3 Create Runbook
Document operational procedures:

**High Token Usage:**
1. Check active sessions
2. Identify expensive operations
3. Review agent prompts
4. Consider rate limiting

**Performance Issues:**
1. Check trace sample rate
2. Review span cardinality
3. Disable console logging
4. Consider batching

#### 4.4 Implement Graceful Degradation
Update `src/utils/logfire_config.py`:
```python
import threading
import time

class LogfireHealthCheck:
    """Monitor Logfire health and disable if issues."""
    
    def __init__(self, check_interval: int = 300):
        self.check_interval = check_interval
        self.is_healthy = True
        self._stop = False
        
    def start(self):
        """Start background health check."""
        thread = threading.Thread(target=self._check_loop)
        thread.daemon = True
        thread.start()
    
    def _check_loop(self):
        """Background health check loop."""
        while not self._stop:
            try:
                # Simple health check
                with logfire.span("health_check"):
                    pass
                self.is_healthy = True
            except Exception as e:
                logfire.error(f"Logfire health check failed: {e}")
                self.is_healthy = False
            
            time.sleep(self.check_interval)
```

### Validation Criteria
- [ ] Production deployment successful
- [ ] Sampling reduces data volume
- [ ] Alerts configured and tested
- [ ] Runbook documented
- [ ] Graceful degradation works

## Phase 5: Advanced Features & Optimization

### Objective
Optimize token tracking and add advanced features based on learnings.

### Potential Features

#### 5.1 Token Budget Management
```python
class TokenBudgetManager:
    """Manage token budgets per user/session."""
    
    def __init__(self, daily_limit: int = 100000):
        self.daily_limit = daily_limit
        self.usage = {}
    
    async def check_budget(self, user_id: str) -> bool:
        """Check if user has budget remaining."""
        # Implementation here
        pass
```

#### 5.2 Intelligent Sampling
- Sample 100% of error cases
- Sample 10% of successful cases
- Sample 100% of slow operations
- Sample 100% of high-cost operations

#### 5.3 Custom Dashboards
- Executive dashboard (costs, usage)
- Developer dashboard (errors, performance)
- Operations dashboard (health, alerts)

#### 5.4 Export & Analysis
- Daily token usage reports
- Cost analysis by feature
- Performance trends
- User behavior patterns

## Risk Mitigation

### Common Risks and Mitigations

1. **Risk**: Logfire service outage
   - **Mitigation**: Application continues without logging
   - **Detection**: Health check alerts

2. **Risk**: High data volume
   - **Mitigation**: Sampling and filtering
   - **Detection**: Cost alerts

3. **Risk**: Performance impact
   - **Mitigation**: Async logging, batching
   - **Detection**: Response time monitoring

4. **Risk**: Token exposure
   - **Mitigation**: Environment variables, access control
   - **Detection**: Audit logs

## Success Metrics

### Phase 1 Success
- Logfire connected and logging
- No application errors
- Basic logs visible

### Phase 2 Success
- Token usage tracked for all agents
- Response times measured
- No performance degradation

### Phase 3 Success
- Full session tracking
- Cost visibility achieved
- Custom metrics working

### Phase 4 Success
- Production deployment stable
- Alerts functioning
- <1% performance impact

### Phase 5 Success
- Token budgets enforced
- Advanced analytics available
- ROI demonstrated

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 | 1-2 days | Logfire account |
| Phase 2 | 2-3 days | Phase 1 complete |
| Phase 3 | 2-3 days | Phase 2 complete |
| Phase 4 | 1-2 days | Phase 3 complete |
| Phase 5 | Ongoing | Phase 4 complete |

**Total Initial Implementation: 6-10 days**

## Conclusion

This phased approach ensures we implement Logfire successfully with minimal risk. Each phase builds on the previous one, with clear validation criteria and rollback plans. By starting simple and adding complexity incrementally, we maximize our chances of success while maintaining application stability.

The key to success is patience - don't rush through phases. Validate thoroughly at each stage before proceeding to the next.