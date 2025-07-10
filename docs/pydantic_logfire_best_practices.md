# Pydantic Logfire Best Practices for Deckster

## Table of Contents
1. [Overview](#overview)
2. [Core Principles](#core-principles)
3. [Environment Configuration](#environment-configuration)
4. [PydanticAI Integration](#pydanticai-integration)
5. [Token Usage Tracking](#token-usage-tracking)
6. [Performance Monitoring](#performance-monitoring)
7. [Security Best Practices](#security-best-practices)
8. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
9. [Testing and Validation](#testing-and-validation)
10. [Production Deployment](#production-deployment)

## Overview

Pydantic Logfire is an observability platform built by the Pydantic team, designed specifically for Python applications with excellent support for LLM observability. This guide outlines best practices for integrating Logfire into the Deckster project with a focus on tracking token usage and monitoring performance.

### Why Logfire for Deckster?
- **Native PydanticAI Integration**: Single line instrumentation for all PydanticAI agents
- **Token Usage Visibility**: Automatic tracking of LLM token consumption
- **OpenTelemetry Based**: Industry standard for observability
- **Multi-Provider Support**: Works with OpenAI, Anthropic, Google, and more
- **Real-time Monitoring**: Live view of agent interactions and costs

## Core Principles

### 1. Start Simple
- Begin with basic PydanticAI instrumentation
- Add complexity incrementally
- Validate each phase before proceeding

### 2. Fail Gracefully
- Logfire should never break the application
- Always provide fallback options
- Use try-except blocks for all Logfire operations

### 3. Environment-Specific Configuration
- Separate configurations for development, staging, and production
- Use environment variables for sensitive data
- Never commit tokens to version control

### 4. Performance First
- Logfire should have minimal impact on application performance
- Use sampling in high-traffic scenarios
- Monitor the monitoring overhead

## Environment Configuration

### Essential Environment Variables

```bash
# Required for Logfire
LOGFIRE_TOKEN=your-write-token-here

# Environment identification
LOGFIRE_ENVIRONMENT=development  # or staging, production

# Optional performance tuning
LOGFIRE_TRACE_SAMPLE_RATE=1.0  # 1.0 = 100% sampling
LOGFIRE_SEND_TO_LOGFIRE=true   # Set to false to disable
LOGFIRE_CONSOLE=false           # Enable for local debugging
```

### Configuration Hierarchy
1. **Programmatic configuration** (highest priority)
2. **Environment variables**
3. **Configuration file** (pyproject.toml)

### Development vs Production

**Development Configuration:**
```python
logfire.configure(
    environment="development",
    console=True,  # Enable console output
    service_name="deckster-dev"
)
```

**Production Configuration:**
```python
logfire.configure(
    # Token from environment variable
    environment=os.getenv("LOGFIRE_ENVIRONMENT", "production"),
    console=False,
    service_name="deckster",
    service_version=os.getenv("APP_VERSION", "unknown")
)
```

## PydanticAI Integration

### Basic Instrumentation

The simplest approach for immediate token tracking:

```python
import logfire
from pydantic_ai import Agent

# Configure Logfire once at application startup
logfire.configure()

# Instrument all PydanticAI agents
logfire.instrument_pydantic_ai()

# Now all agents are automatically tracked
agent = Agent('openai:gpt-4', ...)
```

### Agent-Specific Instrumentation

For more control, instrument specific agents:

```python
# Instrument only specific agents
director_agent = Agent(...)
logfire.instrument_pydantic_ai(director_agent)
```

### Custom Attributes

Add context to your traces:

```python
with logfire.span("presentation_generation", 
                  user_id=user_id,
                  presentation_topic=topic,
                  session_id=session_id):
    result = await agent.run(...)
```

## Token Usage Tracking

### Automatic Token Tracking

When PydanticAI is instrumented, Logfire automatically captures:
- Input tokens
- Output tokens
- Total tokens
- Model name
- Response time

### Accessing Token Metrics

Token usage appears in Logfire spans with these attributes:
- `gen_ai.usage.prompt_tokens`
- `gen_ai.usage.completion_tokens`
- `gen_ai.usage.total_tokens`

### Cost Estimation

While Logfire tracks tokens, cost calculation varies by provider:
- **OpenAI**: Token costs are usually calculated
- **Google/Anthropic**: May require manual cost mapping
- **Custom providers**: Implement cost calculation separately

### Token Usage Monitoring Pattern

```python
async def track_agent_usage(agent, prompt, context):
    """Execute agent with enhanced token tracking."""
    with logfire.span(
        "agent_execution",
        agent_name=agent.name,
        state=context.current_state
    ) as span:
        try:
            result = await agent.run(prompt)
            
            # Log successful execution
            logfire.info(
                "Agent execution completed",
                agent=agent.name,
                state=context.current_state,
                # Token data is automatically included
            )
            
            return result
        except Exception as e:
            logfire.error(
                "Agent execution failed",
                agent=agent.name,
                error=str(e)
            )
            raise
```

## Performance Monitoring

### Key Metrics to Track

1. **Response Times**
   - Agent execution duration
   - State transition times
   - End-to-end presentation generation time

2. **Success Rates**
   - Successful vs failed agent calls
   - Retry rates
   - Error types and frequencies

3. **Resource Usage**
   - Token consumption per state
   - API rate limit proximity
   - Concurrent request counts

### Performance Monitoring Pattern

```python
class MonitoredDirectorAgent:
    def __init__(self):
        self.director = DirectorAgent()
        # Track performance metrics
        self.state_timings = {}
    
    async def process_with_monitoring(self, context):
        state = context.current_state
        
        with logfire.span(
            f"director.{state}",
            state=state,
            session_id=context.session_id
        ) as span:
            start_time = time.time()
            
            try:
                result = await self.director.process(context)
                
                # Track timing
                duration = time.time() - start_time
                self.state_timings[state] = duration
                
                # Log metrics
                logfire.metric(
                    "director.state.duration",
                    duration,
                    state=state
                )
                
                return result
            except Exception as e:
                logfire.metric(
                    "director.state.error",
                    1,
                    state=state,
                    error_type=type(e).__name__
                )
                raise
```

## Security Best Practices

### 1. Token Management

**DO:**
- Use environment variables for tokens
- Create separate tokens for each environment
- Rotate tokens regularly
- Use read-only tokens where possible

**DON'T:**
- Commit tokens to version control
- Log tokens in error messages
- Share tokens across environments
- Use personal tokens in production

### 2. Data Privacy

**Sensitive Data Handling:**
```python
# Sanitize user data before logging
def sanitize_user_input(text):
    # Remove potential PII
    return re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)

logfire.info(
    "Processing user request",
    topic=sanitize_user_input(user_topic)
)
```

### 3. Access Control

- Use Logfire's project-based access control
- Separate projects for different environments
- Limit production access to necessary personnel
- Regular access audits

## Common Pitfalls and Solutions

### Pitfall 1: Token Configuration Issues

**Problem**: "LOGFIRE_TOKEN is invalid" errors
**Solution**:
```python
# Validate token before use
import os
import logfire

def safe_configure_logfire():
    token = os.getenv("LOGFIRE_TOKEN")
    
    if not token:
        print("WARNING: LOGFIRE_TOKEN not set, logging disabled")
        return False
    
    try:
        logfire.configure(token=token)
        # Test with a simple log
        logfire.info("Logfire configured successfully")
        return True
    except Exception as e:
        print(f"ERROR: Logfire configuration failed: {e}")
        return False
```

### Pitfall 2: Import Order Issues

**Problem**: Logfire not capturing all spans
**Solution**: Configure Logfire before importing other modules
```python
# main.py or app startup
import logfire
logfire.configure()  # Configure first!

# Then import your modules
from src.agents import DirectorAgent
```

### Pitfall 3: Overwhelming Log Volume

**Problem**: Too many logs in production
**Solution**: Use sampling and filtering
```python
# Reduce trace volume in production
logfire.configure(
    trace_sample_rate=0.1  # Sample 10% of traces
)

# Filter by importance
if context.is_important:
    logfire.info("Important event", force_sample=True)
```

### Pitfall 4: Missing Context

**Problem**: Logs lack correlation
**Solution**: Use consistent span attributes
```python
# Create a context manager for sessions
@contextmanager
def session_context(session_id):
    with logfire.span("session", session_id=session_id):
        # Set session_id for all nested spans
        logfire.set_attribute("session_id", session_id)
        yield
```

## Testing and Validation

### 1. Local Testing

```python
# Test configuration
def test_logfire_setup():
    """Verify Logfire is properly configured."""
    try:
        import logfire
        
        # Test basic logging
        logfire.info("Test message")
        
        # Test PydanticAI instrumentation
        from pydantic_ai import Agent
        test_agent = Agent("openai:gpt-3.5-turbo", system_prompt="Test")
        logfire.instrument_pydantic_ai(test_agent)
        
        print("✅ Logfire setup successful")
        return True
    except Exception as e:
        print(f"❌ Logfire setup failed: {e}")
        return False
```

### 2. Token Tracking Validation

```python
async def validate_token_tracking():
    """Ensure token usage is being captured."""
    with logfire.span("token_validation_test") as span:
        # Run a minimal agent task
        result = await agent.run("Say hello in 5 words")
        
        # Check span attributes
        attributes = span.get_attributes()
        assert "gen_ai.usage.total_tokens" in attributes
        print(f"✅ Token tracking working: {attributes['gen_ai.usage.total_tokens']} tokens")
```

### 3. Performance Impact Testing

```python
import time

async def measure_overhead():
    """Measure Logfire overhead."""
    # Without Logfire
    start = time.time()
    for _ in range(100):
        result = await agent.run("Test")
    baseline = time.time() - start
    
    # With Logfire
    logfire.instrument_pydantic_ai(agent)
    start = time.time()
    for _ in range(100):
        result = await agent.run("Test")
    with_logfire = time.time() - start
    
    overhead = ((with_logfire - baseline) / baseline) * 100
    print(f"Logfire overhead: {overhead:.2f}%")
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Write token created and tested
- [ ] Environment variables configured
- [ ] Sampling rate appropriate for load
- [ ] Error handling implemented
- [ ] Performance impact measured
- [ ] Access controls configured
- [ ] Alerts and dashboards created

### Deployment Strategy

1. **Stage 1: Shadow Mode**
   ```python
   # Log locally but don't send to Logfire
   logfire.configure(
       send_to_logfire=False,
       console=True
   )
   ```

2. **Stage 2: Partial Rollout**
   ```python
   # Sample small percentage
   logfire.configure(
       trace_sample_rate=0.01  # 1% sampling
   )
   ```

3. **Stage 3: Full Deployment**
   ```python
   # Full production configuration
   logfire.configure(
       environment="production",
       trace_sample_rate=0.1  # Adjust based on volume
   )
   ```

### Monitoring the Monitoring

Set up alerts for:
- Logfire SDK errors
- Sudden drops in log volume
- API rate limit warnings
- Unusual token consumption patterns

### Rollback Plan

If issues arise:
1. Set `LOGFIRE_SEND_TO_LOGFIRE=false`
2. The application continues with NoOpLogger
3. Investigate issues offline
4. Re-enable when resolved

## Summary

Successful Logfire integration requires:
1. **Start simple** with basic PydanticAI instrumentation
2. **Configure properly** using environment variables
3. **Handle failures** gracefully
4. **Monitor impact** on performance
5. **Scale gradually** in production

Following these best practices will ensure reliable token tracking and performance monitoring without compromising application stability.