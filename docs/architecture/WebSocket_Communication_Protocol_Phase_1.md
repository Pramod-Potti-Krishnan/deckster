# Deckster WebSocket Communication Protocol - Phase 1

## Overview

This document describes the WebSocket communication protocol implemented in Deckster Phase 1. The protocol uses a streamlined, message-type-based approach where each message has a single responsibility and maps directly to frontend UI components.

**Important:** This document reflects the actual Phase 1 implementation. Features planned for future phases are documented separately.

## Core Protocol Principles

1. **Single Responsibility**: Each message type serves one specific purpose
2. **Frontend Simplicity**: Messages map directly to UI components  
3. **Type Safety**: All messages follow strict TypeScript/Pydantic schemas
4. **Asynchronous Support**: Status updates enable progress feedback

## Message Types

Phase 1 implements four distinct message types:

### Base Message Envelope

Every message from backend to frontend follows this structure:

```json
{
  "message_id": "msg_unique_id",
  "session_id": "session_xyz", 
  "timestamp": "2024-01-01T10:00:00.000Z",
  "type": "chat_message" | "action_request" | "slide_update" | "status_update",
  "payload": { /* type-specific content */ }
}
```

### 1. Chat Message (`chat_message`)

Displays conversational content in the chat interface.

```json
{
  "type": "chat_message",
  "payload": {
    "text": "Main message text",
    "sub_title": "Optional subtitle",
    "list_items": ["Optional", "list", "of", "items"],
    "format": "markdown" | "plain"
  }
}
```

**Frontend Action:** Render in chat window with proper formatting.

### 2. Action Request (`action_request`)

Presents interactive buttons for user choices.

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
      }
    ]
  }
}
```

**Frontend Action:** Display buttons and handle clicks by sending the `value` back.

### 3. Slide Update (`slide_update`)

Updates the presentation view with structured slide data.

```json
{
  "type": "slide_update",
  "payload": {
    "operation": "full_update" | "partial_update",
    "metadata": {
      "main_title": "AI in Healthcare: Transforming Patient Care",
      "overall_theme": "Data-driven and persuasive",
      "design_suggestions": "Modern professional with blue color scheme",
      "target_audience": "Healthcare executives",
      "presentation_duration": 15
    },
    "slides": [
      {
        "slide_id": "slide_001",
        "slide_number": 1,
        "slide_type": "title_slide",
        "title": "AI in Healthcare: Transforming Patient Care",
        "narrative": "Setting the stage for transformation",
        "key_points": ["Point 1", "Point 2", "Point 3"],
        "analytics_needed": null,
        "visuals_needed": "**Goal:** Create impact. **Content:** Healthcare imagery. **Style:** Modern.",
        "diagrams_needed": null,
        "structure_preference": "Hero Image / Full-Bleed"
      }
    ],
    "affected_slides": ["slide_003"] // Only for partial_update
  }
}
```

**Phase 1 Important Notes:**
- Slides contain structured JSON data, NOT pre-rendered HTML
- Asset fields (visuals_needed, etc.) are text descriptions following "**Goal:** ... **Content:** ... **Style:** ..." format
- Frontend is responsible for rendering based on slide_type and structure_preference

### 4. Status Update (`status_update`)

Shows processing status or progress indicators.

```json
{
  "type": "status_update",
  "payload": {
    "status": "idle" | "thinking" | "generating" | "complete" | "error",
    "text": "Creating your presentation...",
    "progress": 45,  // Optional: 0-100
    "estimated_time": 10  // Optional: seconds
  }
}
```

**Frontend Action:** Display loading indicator with optional progress bar.

## User Input Format

Frontend sends user input in this format:

```json
{
  "type": "user_input",
  "data": {
    "text": "User's message text",
    "response_to": null,  // Optional: ID of message being responded to
    "attachments": [],
    "ui_references": [],
    "frontend_actions": [
      {
        "action_id": "accept_plan",
        "action_type": "button_click",
        "button_id": "accept_plan",
        "context": {}
      }
    ]
  }
}
```

## State-Specific Message Flows

### 1. PROVIDE_GREETING
**Messages sent:** 1
- `chat_message`: Welcome message

### 2. ASK_CLARIFYING_QUESTIONS  
**Messages sent:** 1
- `chat_message`: Questions as list_items

### 3. CREATE_CONFIRMATION_PLAN
**Messages sent:** 2
- `chat_message`: Plan summary with assumptions
- `action_request`: Accept/Reject buttons

### 4. GENERATE_STRAWMAN
**Messages sent:** 3
- `status_update`: "Generating..." (sent immediately)
- `slide_update`: Full presentation data
- `action_request`: Accept/Refine buttons

### 5. REFINE_STRAWMAN
**Messages sent:** 4
- `status_update`: "Refining..." 
- `slide_update`: Partial update with affected slides
- `chat_message`: Explanation of changes
- `action_request`: Further action options

## Complete Example Flow

### Initial Greeting
```json
{
  "message_id": "msg_001",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T10:00:00Z",
  "type": "chat_message",
  "payload": {
    "text": "Hello! I'm Deckster, your AI presentation assistant. I can help you create professional, engaging presentations on any topic.\n\nWhat presentation would you like to build today?"
  }
}
```

### Clarifying Questions
```json
{
  "message_id": "msg_002",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T10:01:00Z",
  "type": "chat_message",
  "payload": {
    "text": "Great topic! To create the perfect presentation for you, I need to understand your needs better:",
    "list_items": [
      "Who is your target audience?",
      "What's the primary goal of this presentation?", 
      "How long will you be presenting?",
      "Are there specific points you must cover?"
    ]
  }
}
```

### Plan Confirmation (2 messages)
```json
// Message 1: Summary
{
  "message_id": "msg_003",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T10:02:00Z",
  "type": "chat_message",
  "payload": {
    "text": "Perfect! Based on your input, I'll create a 6-slide presentation.",
    "sub_title": "Key assumptions I'm making:",
    "list_items": [
      "The audience is technically savvy but business-focused",
      "The presentation should balance technical details with ROI",
      "Visual elements should be professional and modern"
    ]
  }
}

// Message 2: Actions
{
  "message_id": "msg_004",
  "session_id": "session_abc",
  "timestamp": "2024-01-01T10:02:01Z",
  "type": "action_request",
  "payload": {
    "prompt_text": "Does this structure work for you?",
    "actions": [
      {"label": "Yes, let's build it!", "value": "accept_plan", "primary": true},
      {"label": "I'd like to make changes", "value": "reject_plan", "primary": false}
    ]
  }
}
```

## What's NOT in Phase 1

The following features are planned for future phases but NOT implemented in Phase 1:

1. **HTML Generation**: Slides are JSON data, not pre-rendered HTML
2. **Multiple Agents**: Only single Director agent (no UX Architect, Researcher, etc.)
3. **Director Split**: No Director IN/OUT separation
4. **Asset Generation**: No actual image/chart creation, only text descriptions
5. **Real-time Collaboration**: Single user sessions only
6. **Streaming Updates**: Messages are sent complete, not streamed

## Frontend Implementation Guidelines

1. **Message Handling**: Use a simple switch statement on message type
2. **Slide Rendering**: Frontend must implement rendering logic for each slide_type
3. **Asset Placeholders**: Show placeholders based on text descriptions
4. **State Management**: Track current presentation state locally
5. **Error Handling**: Gracefully handle missing or malformed messages

## Connection Requirements

WebSocket connection requires two parameters:
- `session_id`: Unique identifier for the presentation session
- `user_id`: Authenticated user identifier

Example connection:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws?session_id=abc123&user_id=user456');
```

## Best Practices

1. **Message Ordering**: Process messages in order received
2. **Action Values**: Always use exact action values from buttons
3. **Progress Feedback**: Show status updates immediately
4. **Error Recovery**: Reconnect on unexpected disconnection
5. **Type Safety**: Use TypeScript interfaces matching message schemas

## Future Enhancements

Phase 2 and beyond will introduce:
- Multi-agent architecture for parallel content generation
- HTML slide rendering on backend
- Actual asset generation (images, charts, diagrams)
- Progressive slide-by-slide updates
- Enhanced collaboration features

For details on future phases, see the Future Communication Architecture document.