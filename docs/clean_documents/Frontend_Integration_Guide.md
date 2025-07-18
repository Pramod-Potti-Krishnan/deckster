# Deckster Frontend Integration Guide - Phase 1

## Overview

Deckster is an AI-powered presentation assistant that communicates via WebSocket using a streamlined message protocol. This guide documents the **Phase 1 implementation** that is currently in production and being used by the frontend team.

**Important:** This document reflects the actual implementation as of Phase 1. Future phases will add additional capabilities that will be documented separately.

## Key Corrections from Previous Documentation

1. **Protocol**: Streamlined protocol is ON by default (not legacy)
2. **Slide Format**: JSON data with descriptions, NOT pre-rendered HTML
3. **Required Params**: Both `session_id` AND `user_id` are mandatory
4. **Asset Fields**: Text descriptions with Goal/Content/Style format
5. **Message Count**: States may send 2-4 messages (not always one)

## What Phase 1 Delivers

Phase 1 provides a complete presentation planning system through an AI-powered conversation:

1. **Intelligent Conversation**: Director agent guides users through presentation creation
2. **Structured Output**: Complete presentation structure with detailed slide specifications
3. **Content Guidance**: Rich descriptions of what visuals, data, and diagrams each slide needs
4. **Iterative Refinement**: Users can refine specific slides based on feedback
5. **Session Persistence**: All work is saved and can be resumed

**What Frontend Builds**: Using the structured data from Phase 1, the frontend renders the actual slides based on the slide types and structure preferences provided.

## Phase 1 Protocol Summary

- **Protocol**: Streamlined WebSocket Protocol (enabled by default)
- **Message Types**: 4 distinct types (chat_message, action_request, slide_update, status_update)
- **States**: 5-state workflow (greeting → questions → plan → strawman → refinement)
- **Authentication**: Both session_id and user_id required
- **Data Format**: JSON with structured payloads

## Quick Start

### 1. Connect to WebSocket

```javascript
// REQUIRED: Both parameters must be provided
const sessionId = 'unique-session-id'; // Generate a unique ID for each presentation
const userId = 'authenticated-user-id'; // From your authentication system
const ws = new WebSocket(`ws://localhost:8000/ws?session_id=${sessionId}&user_id=${userId}`);

ws.onopen = () => {
  console.log('Connected to Deckster');
  // For new sessions, you'll automatically receive a greeting message
  // For existing sessions, you'll resume from the last state
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  handleMessage(message); // See message handling below
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('Disconnected:', event.code, event.reason);
  // Code 1006 usually means backend couldn't initialize session (Supabase issue)
};
```

**Critical Requirements:**
- Both `session_id` and `user_id` are mandatory
- Supabase must be configured for session persistence
- Each user can have multiple sessions (different presentations)

### 2. Sending Messages

Send user input as simple JSON:

```javascript
function sendUserMessage(text) {
  const message = {
    type: "user_input",
    data: {
      text: text,
      response_to: null,
      attachments: [],
      ui_references: [],
      frontend_actions: []
    }
  };
  ws.send(JSON.stringify(message));
}
```

## Message Types - Phase 1 Implementation

**Current Status:** Phase 1 uses the Streamlined WebSocket Protocol exclusively. The legacy `director_message` format is no longer used in production.

### Base Message Structure

All messages from the backend follow this envelope structure:

```json
{
  "message_id": "msg_abc123",           // Unique message identifier
  "session_id": "session_xyz",          // Your session ID
  "timestamp": "2024-01-01T10:00:00Z",  // ISO timestamp
  "type": "chat_message",               // One of: chat_message, action_request, slide_update, status_update
  "payload": { /* type-specific content */ }
}
```

### 1. Chat Message (`chat_message`)

Display conversational text in your chat interface.

```json
{
  "type": "chat_message",
  "payload": {
    "text": "Main message text",
    "sub_title": "Optional subtitle",
    "list_items": ["Optional", "list", "of", "items"],
    "format": "markdown"
  }
}
```

**Frontend Action:** Display in chat window with proper formatting.

### 2. Action Request (`action_request`)

Show interactive buttons for user choices.

```json
{
  "type": "action_request",
  "payload": {
    "prompt_text": "What would you like to do?",
    "actions": [
      {
        "label": "Accept",
        "value": "accept_plan",
        "primary": true,
        "requires_input": false
      },
      {
        "label": "Modify",
        "value": "reject_plan",
        "primary": false,
        "requires_input": true
      }
    ]
  }
}
```

**Frontend Action:** 
- Display prompt text
- Render buttons with labels
- Style primary button differently
- If `requires_input` is true, show text input field

**Responding to Actions:**
```javascript
function handleActionClick(actionValue, userInput = null) {
  const response = {
    type: "user_input",
    data: {
      text: userInput || actionValue,
      response_to: null,
      attachments: [],
      ui_references: [],
      frontend_actions: [
        {
          action_id: actionValue,
          action_type: "button_click",
          button_id: actionValue,
          context: {}
        }
      ]
    }
  };
  ws.send(JSON.stringify(response));
}
```

### 3. Slide Update (`slide_update`)

**Phase 1 Implementation:** Sends structured slide data as JSON. The frontend is responsible for rendering based on slide types and structure preferences.

```json
{
  "type": "slide_update",
  "payload": {
    "operation": "full_update",  // or "partial_update" for refinements
    "metadata": {
      "main_title": "AI in Healthcare: Transforming Patient Care",
      "overall_theme": "Data-driven and persuasive",
      "design_suggestions": "Modern professional with blue color scheme",
      "target_audience": "Hospital executives",
      "presentation_duration": 15
    },
    "slides": [
      {
        "slide_id": "slide_001",
        "slide_number": 1,
        "slide_type": "title_slide",
        "title": "AI in Healthcare: Transforming Patient Care",
        "narrative": "Set a professional tone that resonates with executives",
        "key_points": [
          "Revolutionizing Diagnostics",
          "Proven ROI for Healthcare",
          "Implementation Roadmap"
        ],
        "analytics_needed": null,
        "visuals_needed": "**Goal:** Create immediate visual impact. **Content:** Modern healthcare facility with AI overlay. **Style:** Professional, clean, technology-forward",
        "diagrams_needed": null,
        "structure_preference": "Hero Image / Full-Bleed"
      }
    ],
    "affected_slides": ["slide_003", "slide_005"] // Only present for partial_update
  }
}
```

**Note on Partial Updates:** 
- The `affected_slides` array lists which slides were modified
- Only the modified slides are included in the `slides` array
- Frontend should update only these specific slides in the presentation
- Other slides remain unchanged from the previous state

**Slide Content Fields (Phase 1):**
- `analytics_needed`: String description of data/charts needed (or null)
- `visuals_needed`: String description of images/graphics needed (or null)
- `diagrams_needed`: String description of diagrams/flows needed (or null)

**Note:** In Phase 1, these are text descriptions following a "**Goal:** ... **Content:** ... **Style:** ..." format. Future phases will include actual generated assets.

**Slide Types (Phase 1):**
- `title_slide`: Opening/hero slide
- `section_divider`: Section break slide
- `content_heavy`: Text-focused content
- `visual_heavy`: Image-focused content
- `data_driven`: Charts and metrics focus
- `diagram_focused`: Process flows and diagrams
- `mixed_content`: Balanced text and visuals
- `conclusion_slide`: Call to action/summary

**Structure Preferences (Guidance for Frontend):**
- `Hero Image / Full-Bleed`: Full-screen visual impact
- `Two-Column (Classic)`: Split layout
- `Grid Layout`: Multiple items in grid
- `Single Focal Point`: One main element
- `Timeline / Process Flow`: Sequential information
- `Quadrant / Matrix`: 2x2 or similar layout

### 4. Status Update (`status_update`)

Show processing status or progress.

```json
{
  "type": "status_update",
  "payload": {
    "status": "generating",
    "text": "Creating your presentation...",
    "progress": 45,
    "estimated_time": 10
  }
}
```

**Status Levels:**
- `idle`: Waiting
- `thinking`: Processing input
- `generating`: Creating content
- `complete`: Finished
- `error`: Something went wrong

**Frontend Action:** Show loading indicator with progress bar if provided.

## Complete Example

```javascript
function handleMessage(message) {
  switch (message.type) {
    case 'chat_message':
      addToChatUI(message.payload);
      break;
      
    case 'action_request':
      showActionButtons(message.payload);
      break;
      
    case 'slide_update':
      updatePresentationView(message.payload);
      break;
      
    case 'status_update':
      updateStatusIndicator(message.payload);
      break;
  }
}

function addToChatUI(payload) {
  const chatElement = document.createElement('div');
  chatElement.className = 'chat-message';
  
  // Main text
  const textElement = document.createElement('p');
  textElement.textContent = payload.text;
  chatElement.appendChild(textElement);
  
  // Subtitle if present
  if (payload.sub_title) {
    const subtitleElement = document.createElement('h4');
    subtitleElement.textContent = payload.sub_title;
    chatElement.appendChild(subtitleElement);
  }
  
  // List items if present
  if (payload.list_items) {
    const listElement = document.createElement('ul');
    payload.list_items.forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      listElement.appendChild(li);
    });
    chatElement.appendChild(listElement);
  }
  
  document.getElementById('chat-container').appendChild(chatElement);
}
```

## Phase 1 Workflow - Actual Implementation

### State Machine Flow

1. **PROVIDE_GREETING** (Initial State)
   - **Trigger**: New session connection
   - **Backend Sends**: `chat_message` with greeting
   - **Next State**: Waits for user topic

2. **ASK_CLARIFYING_QUESTIONS**
   - **Trigger**: User provides initial topic
   - **Backend Sends**: `chat_message` with 3-5 questions as list items
   - **Next State**: Waits for answers

3. **CREATE_CONFIRMATION_PLAN**
   - **Trigger**: User answers questions
   - **Backend Sends**: 
     - `chat_message` with plan summary
     - `action_request` with Accept/Modify buttons
   - **Next State**: Based on user choice

4. **GENERATE_STRAWMAN**
   - **Trigger**: User accepts plan
   - **Backend Sends**:
     - `status_update` (before generation starts)
     - `slide_update` with full presentation data
     - `action_request` for accept/refine
   - **Next State**: Based on user choice

5. **REFINE_STRAWMAN**
   - **Trigger**: User requests changes
   - **Backend Sends** (4 messages):
     - `status_update` (progress indicator during refinement)
     - `slide_update` with `partial_update` operation
     - `chat_message` explaining changes made
     - `action_request` for further actions
   - **Next State**: Can loop back to REFINE_STRAWMAN or end

### Message Sequences by State

**Important:** The exact number of messages per state is deterministic in Phase 1:

| State | Message Count | Message Types in Order |
|-------|---------------|------------------------|
| PROVIDE_GREETING | 1 | chat_message |
| ASK_CLARIFYING_QUESTIONS | 1 | chat_message (with list_items) |
| CREATE_CONFIRMATION_PLAN | 2 | chat_message, action_request |
| GENERATE_STRAWMAN | 3 | status_update (pre-generation), slide_update, action_request |
| REFINE_STRAWMAN | 4 | status_update, slide_update, chat_message, action_request |

#### New Session Start
```
→ Connect with session_id and user_id
← chat_message: "Hello! I'm Deckster..."
→ user_input: "I need a presentation about AI"
← chat_message: "Great topic! To create the perfect presentation..."
```

#### Plan Confirmation (2 Messages)
```
→ user_input: "Audience: executives, Duration: 15 min..."
← chat_message: "Perfect! Based on your input..." (plan summary)
← action_request: "Does this structure work for you?" (buttons)
```

#### Strawman Generation (3 Messages: Pre-status + Result)
```
→ user_input: "accept_plan" (via frontend_actions)
← status_update: "Excellent! I'm now creating..." (sent BEFORE processing starts)
  [15-20 second processing delay]
← slide_update: {full presentation data}
← action_request: "Your presentation is ready!"
```

## Testing Locally

1. Start the Deckster backend:
   ```bash
   python main.py
   ```

2. Backend will run on `http://localhost:8000`

3. Connect your frontend to `ws://localhost:8000/ws?session_id=test-session-123&user_id=test-user-123`

4. Send a test message:
   ```javascript
   ws.send(JSON.stringify({
     type: "user_input",
     data: {
       text: "I need a presentation about AI in healthcare",
       response_to: null,
       attachments: [],
       ui_references: [],
       frontend_actions: []
     }
   }));
   ```

## Important Notes

- Always include both `session_id` and `user_id` in the WebSocket connection URL
- Messages are formatted as JSON
- The backend handles all AI processing - frontend only displays results
- Each message type maps to a specific UI component
- Handle connection errors and reconnection in production

## Authentication & Session Management

### User Authentication
- `user_id` must be provided from your authentication system
- Each user can have multiple sessions (presentations)
- Sessions are isolated by user - users cannot access other users' sessions

### Session Management
- `session_id` should be unique for each presentation/conversation
- You can generate session IDs using UUIDs or your preferred method
- Sessions persist in the database, allowing users to return to previous work

### Example Integration
```javascript
// After user logs in
const currentUser = await authenticateUser();
const userId = currentUser.id;

// Create new presentation session
const sessionId = generateUUID();

// Connect to Deckster
const ws = new WebSocket(
  `ws://localhost:8000/ws?session_id=${sessionId}&user_id=${userId}`
);

// Store session info for later retrieval
saveUserSession(userId, sessionId, 'My AI Presentation');
```

## Important Implementation Notes

### Asset Field Format (Phase 1)

The `analytics_needed`, `visuals_needed`, and `diagrams_needed` fields follow a specific format:

```
"**Goal:** [What this asset should achieve]
**Content:** [Specific content description]
**Style:** [Visual style guidance]"
```

Example:
```json
{
  "visuals_needed": "**Goal:** Create immediate visual impact. **Content:** Modern healthcare facility with subtle AI overlay. **Style:** Professional, clean, technology-forward"
}
```

### Frontend Responsibilities (Phase 1)

1. **Parse Asset Descriptions**: Extract Goal/Content/Style from text
2. **Map Slide Types**: Render appropriate layouts based on `slide_type`
3. **Apply Structure Preferences**: Use `structure_preference` as layout guidance
4. **Handle Null Fields**: Many slides will have null for some asset fields
5. **Maintain State**: Track which slides have been refined

### Database Requirements
Deckster requires Supabase for all session management. The backend will:
- Validate Supabase connection on startup
- Refuse to start if Supabase is not properly configured
- Store all sessions with user_id for proper user isolation
- Persist conversation history and presentation data

**Important:** There is no fallback mode. Supabase must be properly configured and accessible for the application to function.

### Environment Variable Defaults
From `config/settings.py`, these are the Phase 1 defaults:
- `USE_STREAMLINED_PROTOCOL`: **true** (streamlined is default)
- `STREAMLINED_PROTOCOL_PERCENTAGE`: **100** (all sessions use streamlined)
- `PORT`: **8000** (can be overridden by hosting platform)
- `DEBUG`: **true** (set to false in production)
- `LOG_LEVEL`: **DEBUG** (use INFO or WARNING in production)

## Phase 1 Limitations & Future Enhancements

### What's NOT in Phase 1

1. **No HTML Generation**: Slides come as structured JSON data, not pre-rendered HTML
2. **No Actual Assets**: Visual/chart/diagram fields contain text descriptions only
3. **No Multi-Agent System**: Only the Director agent is active
4. **No Parallel Processing**: Sequential state machine only
5. **No Real-time Collaboration**: Single user per session

### Coming in Future Phases

#### Phase 2 (Layout Architecture)
- Layout Architect agent for intelligent slide layouts
- Grid-based positioning system (160×90 grid)
- Progressive content assembly
- Director OUT for parallel agent coordination

#### Phase 3 (Multi-Agent System)
- Researcher agent for content enhancement
- Visual Designer for image generation
- Data Analyst for charts and metrics
- UX Analyst for diagrams and flows
- Parallel agent execution
- Progressive slide updates as agents complete

## Error Handling

### Connection Errors

When errors occur, the backend sends error messages using the streamlined protocol:

```json
[
  {
    "type": "status_update",
    "payload": {
      "status": "error",
      "text": "Error description here"
    }
  },
  {
    "type": "chat_message",
    "payload": {
      "text": "I encountered an error while processing your request. Please try again or let me know if you need help.",
      "format": "plain"
    }
  }
]
```

### WebSocket Close Codes

- **1000**: Normal closure
- **1001**: Going away (server shutdown)
- **1006**: Abnormal closure (usually initialization failure)
- **1011**: Server error (check backend logs)

## Troubleshooting

### Common Issues

1. **Connection Closes Immediately (Code 1006)**
   - Cause: Backend can't initialize session (usually Supabase issues)
   - Fix: Ensure Supabase URL and keys are properly configured
   - Check: Backend logs will show "Failed to initialize Supabase client"

2. **No Greeting Message**
   - Cause: Session initialization failed or missing parameters
   - Fix: Verify both session_id and user_id are provided in connection URL
   - Check: Ensure format is exactly `?session_id=X&user_id=Y`

3. **Empty Slide Updates**
   - Cause: AI generation issues or missing API keys
   - Fix: Verify at least one AI API key is configured (Google/OpenAI/Anthropic)
   - Check: Backend logs for "At least one AI API key must be configured"

4. **State Machine Stuck**
   - Cause: Frontend not sending proper action values
   - Fix: Ensure button clicks send exact `action_value` from the action request
   - Check: `frontend_actions` array must contain the action_id

### Debug Checklist

- ✓ Both `session_id` and `user_id` provided in connection URL
- ✓ Supabase configured and accessible
- ✓ At least one AI API key configured (Google/OpenAI/Anthropic)
- ✓ WebSocket connection established (check onopen)
- ✓ Messages being received (check onmessage)
- ✓ Message structure matches expected format
- ✓ Frontend handles all 4 message types

## Need Help?

- Check browser console for WebSocket errors
- Verify message JSON structure matches this guide
- Ensure your authentication provides consistent user_id
- Monitor backend logs for detailed error information
- Review the Phase 1 workflow diagram above