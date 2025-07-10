# Useful Logfire Queries for Deckster

This document contains useful queries and filters for monitoring token usage and performance in the Logfire dashboard.

## Token Usage Queries

### 1. Total Tokens by Agent
To see which agents are using the most tokens:

**Filter in Logfire UI:**
- Look for spans with attribute `gen_ai.usage.total_tokens`
- Group by `agent_name` or span name
- Sort by total tokens descending

**What to look for:**
- `gen_ai.usage.prompt_tokens` - Input tokens
- `gen_ai.usage.completion_tokens` - Output tokens  
- `gen_ai.usage.total_tokens` - Combined total

### 2. Token Usage Over Time
Track token consumption trends:

**Time-based view:**
- Select time range (last hour, day, week)
- Filter for spans with `gen_ai.usage.total_tokens`
- Use time histogram view
- Look for spikes or unusual patterns

### 3. Cost Estimation
While Logfire tracks tokens, you'll need to calculate costs based on your model:

**Token to Cost Mapping (approximate):**
- GPT-4: $0.03/1K input, $0.06/1K output tokens
- GPT-4-Turbo: $0.01/1K input, $0.03/1K output tokens
- Gemini 2.5 Flash: $0.0001/1K input, $0.0003/1K output tokens
- Gemini 2.5 Pro: $0.001/1K input, $0.003/1K output tokens

## Performance Queries

### 4. Slowest Agent Operations
Find performance bottlenecks:

**Filter for:**
- Span duration > 5 seconds
- Span name contains "agent" or specific agent names
- Sort by duration descending

### 5. Error Rate by Agent
Monitor agent reliability:

**Filter for:**
- Spans with `level = ERROR`
- Group by agent name
- Calculate error percentage

## Session Tracking

### 6. Session Token Usage
Track token usage per user session:

**Filter for:**
- Attribute `session_id` exists
- Has `gen_ai.usage.total_tokens`
- Group by `session_id`
- Sum total tokens

### 7. State Transition Tracking
Monitor workflow progression:

**Look for:**
- Spans named `state_transition`
- Attributes `from_state` and `to_state`
- Track transition success rates

## Useful Filters

### Quick Filters
1. **High Token Usage**: `gen_ai.usage.total_tokens > 1000`
2. **Slow Responses**: `duration > 10s`
3. **Errors Only**: `level = ERROR`
4. **Specific Agent**: `span.name contains "director"`

### Combined Filters
1. **Expensive Operations**: High tokens AND long duration
2. **Failed High-Cost Ops**: Errors with high token usage
3. **Session Problems**: Sessions with multiple errors

## Dashboard Setup Recommendations

### 1. Token Usage Dashboard
- Total tokens (last 24h)
- Tokens by agent (pie chart)
- Token usage over time (line graph)
- Top 10 most expensive operations

### 2. Performance Dashboard
- Average response time by agent
- 95th percentile response times
- Error rate over time
- Slowest operations table

### 3. Cost Tracking Dashboard
- Estimated cost per hour
- Cost by agent/feature
- Daily cost trend
- Cost per user session

## Alert Recommendations

Set up alerts for:
1. **High Token Usage**: > 10,000 tokens in 5 minutes
2. **Slow Response**: Any operation > 30 seconds
3. **High Error Rate**: > 5% errors in 10 minutes
4. **Cost Threshold**: > $10 estimated cost per hour

## Example Investigations

### "Why are tokens being used so much?"
1. Filter for high token usage operations
2. Look at the span details for prompt/completion sizes
3. Check which states/agents are involved
4. Review the conversation history length

### "Which users are most expensive?"
1. Filter by session_id
2. Sum tokens per session
3. Join with user data if available
4. Sort by total token usage

### "Is the system getting slower?"
1. Compare response times week-over-week
2. Look for duration trends
3. Check if token usage correlates with slowness
4. Identify specific slow operations

## Notes
- Token tracking only works for instrumented PydanticAI agents
- Costs are estimates - verify with your AI provider's billing
- Session tracking requires session_id to be set in spans
- Some metrics may require custom instrumentation