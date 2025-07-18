# Deckster Logfire Implementation Guide

## Overview

This guide consolidates all Logfire documentation for Deckster into a single, actionable implementation plan. Logfire provides automatic token tracking, performance monitoring, and observability for our PydanticAI agents.

**Key Benefits:**
- Automatic token usage tracking for all LLM calls
- Real-time performance monitoring
- Cost visibility and estimation
- Zero-code instrumentation for PydanticAI

## Phase A: Foundation Setup

### Objective
Establish Logfire connection and validate basic functionality.

### A.1 Environment Configuration

Add to `.env`:
```bash
# Required
LOGFIRE_TOKEN=your-write-token-here

# Optional but recommended
LOGFIRE_ENVIRONMENT=development    # or staging, production
LOGFIRE_CONSOLE=false             # true for local debugging
LOGFIRE_TRACE_SAMPLE_RATE=1.0    # 1.0 = 100% sampling
LOGFIRE_SEND_TO_LOGFIRE=true     # false to disable sending
```

### A.2 Create Logfire Configuration Module

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
        
        # Validate configuration
        logfire.info("Logfire configured successfully")
        _configured = True
        return True
        
    except Exception as e:
        print(f"ERROR: Logfire configuration failed: {e}")
        return False

def is_configured() -> bool:
    """Check if Logfire is configured."""
    return _configured
```

### A.3 Initialize in Main Entry Point

Update `main.py`:
```python
# At the very top, after imports
from src.utils.logfire_config import configure_logfire

# Configure Logfire before anything else
print("[DEBUG] Configuring Logfire...")
configure_logfire()

# Rest of your application...
```

### A.4 Validation

Run the application and verify:
- ✓ No errors during startup
- ✓ "Logfire configured successfully" appears in logs
- ✓ Check Logfire dashboard for the test log entry

## Phase B: PydanticAI Token Tracking

### Objective
Enable automatic token tracking for all AI agents with zero code changes.

### B.1 Enable PydanticAI Instrumentation

Update `src/utils/logfire_config.py`:
```python
def instrument_pydantic_ai() -> bool:
    """Enable PydanticAI instrumentation for token tracking."""
    if not is_configured():
        return False
    
    try:
        import logfire
        
        # This single line instruments ALL PydanticAI agents
        logfire.instrument_pydantic_ai()
        
        logfire.info("PydanticAI instrumentation enabled")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to instrument PydanticAI: {e}")
        return False
```

### B.2 Update Main Entry Point

In `main.py`, after configuring Logfire:
```python
from src.utils.logfire_config import configure_logfire, instrument_pydantic_ai

# Configure Logfire
configure_logfire()

# Enable PydanticAI instrumentation
instrument_pydantic_ai()
```

### B.3 What Gets Tracked Automatically

With instrumentation enabled, Logfire automatically captures:
- `gen_ai.usage.prompt_tokens` - Input token count
- `gen_ai.usage.completion_tokens` - Output token count
- `gen_ai.usage.total_tokens` - Total tokens used
- `gen_ai.model` - Model name (e.g., "gpt-4")
- Response time and duration
- Any errors or exceptions

### B.4 Validation

1. Run a test conversation through Deckster
2. Check Logfire dashboard for spans with:
   - Name containing your agent names
   - Attributes showing token counts
   - Duration metrics

## Phase C: Enhanced Monitoring

### Objective
Add session tracking, custom metrics, and cost estimation.

### C.1 Session Context Tracking

Create `src/utils/logfire_context.py`:
```python
"""
Enhanced Logfire tracking for Deckster sessions.
"""
import logfire
from contextlib import contextmanager
from typing import Optional, Dict, Any

@contextmanager
def session_context(session_id: str, user_id: Optional[str] = None):
    """
    Track all operations within a session.
    
    Usage:
        with session_context(session_id, user_id):
            # All operations here will be tagged with session
    """
    with logfire.span(
        'session',
        session_id=session_id,
        user_id=user_id
    ) as span:
        # Make session_id available to all nested spans
        logfire.set_attribute('session_id', session_id)
        if user_id:
            logfire.set_attribute('user_id', user_id)
        yield span

def track_state_transition(
    from_state: str,
    to_state: str,
    session_id: str
):
    """Log state machine transitions."""
    logfire.info(
        'State transition',
        from_state=from_state,
        to_state=to_state,
        session_id=session_id
    )
    
    # Track as metric for dashboards
    logfire.metric_counter(
        'state_transitions',
        unit='1',
        description='Number of state transitions'
    ).add(1, {'to_state': to_state})
```

### C.2 Cost Tracking

Add to `src/utils/logfire_context.py`:
```python
# Token costs per 1K tokens (update as needed)
TOKEN_COSTS = {
    'gpt-4': {'input': 0.03, 'output': 0.06},
    'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
    'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
    'gemini-2.0-flash': {'input': 0.0001, 'output': 0.0003},
    'claude-3-sonnet': {'input': 0.003, 'output': 0.015}
}

def estimate_token_cost(
    model: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """Estimate cost based on token usage."""
    # Find model in costs table
    model_key = None
    for key in TOKEN_COSTS:
        if key in model.lower():
            model_key = key
            break
    
    if not model_key:
        return 0.0
    
    # Calculate costs
    input_cost = (input_tokens / 1000) * TOKEN_COSTS[model_key]['input']
    output_cost = (output_tokens / 1000) * TOKEN_COSTS[model_key]['output']
    
    return input_cost + output_cost
```

### C.3 Integrate with WebSocket Handler

Update `src/handlers/websocket.py`:
```python
from src.utils.logfire_context import session_context, track_state_transition

async def handle_connection(self, websocket: WebSocket, session_id: str, user_id: str):
    """Handle WebSocket connection with session tracking."""
    
    # Wrap entire session in context
    with session_context(session_id, user_id):
        try:
            # Your existing connection handling code
            session = await self.sessions.get_or_create(session_id, user_id)
            
            # ... rest of your code ...
            
        except Exception as e:
            logfire.error(
                "WebSocket error",
                error=str(e),
                session_id=session_id
            )
            raise
```

### C.4 Add Performance Metrics

Create key metrics for monitoring:
```python
# Response time histogram
response_time = logfire.metric_histogram(
    'agent_response_time',
    unit='ms',
    description='Time to generate agent response'
)

# Token usage counter
token_counter = logfire.metric_counter(
    'tokens_used',
    unit='1',
    description='Total tokens consumed'
)

# Cost metric
cost_histogram = logfire.metric_histogram(
    'request_cost_usd',
    unit='$',
    description='Estimated cost per request'
)
```

## Phase D: Production Optimization

### Objective
Optimize for production with sampling, alerts, and operational excellence.

### D.1 Production Configuration

Update production environment variables:
```bash
# Production settings
LOGFIRE_TOKEN=your-production-write-token
LOGFIRE_ENVIRONMENT=production
LOGFIRE_CONSOLE=false
LOGFIRE_TRACE_SAMPLE_RATE=0.1  # Sample 10% of traces
APP_VERSION=1.0.0
```

### D.2 Intelligent Sampling

Add to `src/utils/logfire_config.py`:
```python
def should_force_trace() -> bool:
    """Determine if current operation should be traced regardless of sampling."""
    # Always trace errors
    if logfire.get_level() >= logfire.ERROR:
        return True
    
    # Always trace slow operations (implement your logic)
    # Always trace high-cost operations
    
    return False

# Use in critical paths:
with logfire.span('critical_operation', force_trace=should_force_trace()):
    # Your code here
```

### D.3 Operational Dashboards

#### Token Usage Dashboard
Key metrics to display:
- Total tokens last 24h
- Tokens by agent (pie chart)
- Token usage trend (line graph)
- Top 10 most expensive operations

#### Performance Dashboard
- Average response time by state
- 95th percentile response times
- Error rate by agent
- Slowest operations table

#### Cost Dashboard
- Estimated cost per hour
- Cost by model
- Daily cost trend
- Cost per user session

### D.4 Alerts Configuration

Set up Logfire alerts for:

1. **High Token Usage**
   - Threshold: >10,000 tokens in 5 minutes
   - Action: Check for runaway agents

2. **Slow Response**
   - Threshold: Any operation >30 seconds
   - Action: Investigate performance bottleneck

3. **High Error Rate**
   - Threshold: >5% errors in 10 minutes
   - Action: Check service health

4. **Cost Threshold**
   - Threshold: >$10/hour estimated cost
   - Action: Review usage patterns

## Quick Reference

### Essential Logfire Queries

**Total Tokens by Agent:**
```
Filter: gen_ai.usage.total_tokens exists
Group by: span.name
Aggregate: sum(gen_ai.usage.total_tokens)
```

**Session Token Usage:**
```
Filter: session_id exists AND gen_ai.usage.total_tokens exists
Group by: session_id
Aggregate: sum(gen_ai.usage.total_tokens)
```

**Error Rate:**
```
Filter: level = ERROR
Group by: span.name
Calculate: count(errors) / count(total) * 100
```

### Common Issues & Solutions

**Issue:** No token data appearing
**Solution:** Ensure `instrument_pydantic_ai()` is called after `configure_logfire()`

**Issue:** Missing session context
**Solution:** Wrap WebSocket handler in `session_context()`

**Issue:** High data volume in production
**Solution:** Reduce `LOGFIRE_TRACE_SAMPLE_RATE` to 0.01-0.1

**Issue:** Can't see logs locally
**Solution:** Set `LOGFIRE_CONSOLE=true` for development

## Implementation Checklist

### Phase A (Day 1)
- [ ] Add LOGFIRE_TOKEN to environment
- [ ] Create logfire_config.py
- [ ] Update main.py
- [ ] Verify basic logging works

### Phase B (Day 2)
- [ ] Enable PydanticAI instrumentation
- [ ] Verify token tracking in dashboard
- [ ] Check all agents are instrumented

### Phase C (Days 3-4)
- [ ] Add session context tracking
- [ ] Implement state transition logging
- [ ] Set up cost estimation
- [ ] Create basic metrics

### Phase D (Day 5+)
- [ ] Configure production sampling
- [ ] Set up dashboards
- [ ] Configure alerts
- [ ] Document runbooks

## Summary

This consolidated guide provides everything needed to implement Logfire in Deckster:

1. **Phase A**: Basic setup and validation
2. **Phase B**: Automatic token tracking with one line of code
3. **Phase C**: Enhanced monitoring with session and cost tracking  
4. **Phase D**: Production optimization with sampling and alerts

The key insight is that PydanticAI's built-in Logfire integration means token tracking "just works" with minimal code changes. Focus on getting the basics right before adding complexity.