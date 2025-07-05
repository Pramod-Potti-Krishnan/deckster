# Deploy Fixes Command

## Purpose
This command is used when there are production issues that need systematic debugging and resolution. It provides a structured approach to identify root causes and plan fixes for both frontend and backend components.

## Usage
When you encounter production issues, use this command with the following information:

### Required Information to Provide:
1. **F12 Console Logs** - Browser developer console output showing errors, warnings, and debug information
2. **Railway Logs** - Backend server logs from Railway deployment showing server-side errors and processing
3. **User Input Context** - Description of what the user was trying to do when the issue occurred
4. **Expected vs Actual Behavior** - What should have happened vs what actually happened

### Example Usage:
```
/deploy-fixes

**F12 Console Logs:**
```
TypeError: Cannot read properties of undefined (reading 'length')
at sO (page-fded51b4292c41df.js:1:104989)
WebSocket connected successfully
Session established: session_4ef1eb278bb9
```

**Railway Logs:**
```
INFO:presentation-generator:Agent Response: director_inbound - completed
ERROR:websocket:Connection failed with status 500
```

**User Input:** 
User clicked "Create Presentation" and typed "Create a presentation about AI trends"

**Expected:** Should show AI agents working and then display slides
**Actual:** Page crashes with TypeError
```

## Claude's Response Process

When this command is used, Claude will:

### 1. **Root Cause Analysis**
- Analyze F12 console logs to identify frontend issues
- Examine Railway logs to identify backend issues  
- Correlate user input with error patterns
- Identify the sequence of events leading to the failure

### 2. **Issue Classification**
- **Frontend Issues**: Component crashes, state management, UI rendering problems
- **Backend Issues**: API failures, database errors, processing crashes
- **Integration Issues**: WebSocket communication, data format mismatches
- **Infrastructure Issues**: Deployment, configuration, network problems

### 3. **Priority Assessment**
- **P0 (Critical)**: System completely broken, blocks all users
- **P1 (High)**: Major functionality broken, affects most users
- **P2 (Medium)**: Some features broken, workarounds available
- **P3 (Low)**: Minor issues, cosmetic problems

### 4. **Create Task Lists**

#### Frontend Task List (Example):
- [ ] **P0** - Fix TypeError in slide rendering component
- [ ] **P1** - Add null checks to slide.length access
- [ ] **P2** - Improve error boundaries for component crashes
- [ ] **P3** - Add loading states during WebSocket connection

#### Backend Task List (Example):
- [ ] **P0** - Fix 500 error in presentation generation endpoint
- [ ] **P1** - Add error handling for malformed requests
- [ ] **P2** - Improve logging for debugging
- [ ] **P3** - Optimize response times

#### Integration Task List (Example):
- [ ] **P0** - Fix WebSocket message format mismatch
- [ ] **P1** - Add retry logic for failed connections
- [ ] **P2** - Implement heartbeat/ping mechanism
- [ ] **P3** - Add connection status indicators

### 5. **Implementation Plan**
- Create round-by-round communication documents (e.g., `round18_FE2BE.md`)
- Implement fixes in priority order
- Test each fix before moving to next
- Document all changes made
- Create commit messages with proper tracking

### 6. **Coordination Guidelines**
- **Frontend Team**: Focus on UI stability, error handling, user experience
- **Backend Team**: Focus on API reliability, data processing, error responses
- **Integration**: Ensure both teams align on data formats, protocols, error codes

## Expected Outcomes

After using this command, you should have:
-  Clear understanding of what went wrong
-  Prioritized list of tasks for each team
-  Communication plan between frontend and backend teams
-  Testing strategy to verify fixes
-  Documentation of the debugging process

## Best Practices

1. **Provide Complete Information**: Include all relevant logs, not just error messages
2. **Be Specific**: Exact user actions, timestamps, affected features
3. **Include Context**: What was working before, what changed recently
4. **Multiple Scenarios**: If the issue happens in different situations, include all
5. **Environment Details**: Production vs staging, browser versions, user types

## Follow-up Actions

After Claude provides the analysis and task lists:
1. Review and prioritize the tasks
2. Assign tasks to appropriate team members
3. Create tracking issues/tickets
4. Begin implementation starting with P0 tasks
5. Regular check-ins to ensure coordination
6. Document lessons learned for future issues

---

This command helps ensure systematic debugging and coordination between frontend and backend teams for efficient issue resolution.