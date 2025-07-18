# WebSocket JSON Communication Flow

This document provides a comprehensive explanation of how information flows through the WebSocket connection in JSON format across all workflow states in the Deckster presentation generation system.

## Table of Contents
1. [WebSocket Connection Setup](#websocket-connection-setup)
2. [Message Format Overview](#message-format-overview)
3. [Streamlined Protocol (New)](#streamlined-protocol-new)
4. [State-by-State JSON Flow](#state-by-state-json-flow)
5. [Intent-Based Routing](#intent-based-routing)
6. [Error Handling](#error-handling)

## WebSocket Connection Setup

### Connection URL
The WebSocket connection is established at:
```
ws://localhost:8000/ws?session_id={session_id}
```
or for secure connections:
```
wss://your-domain.com/ws?session_id={session_id}
```

### Initial Connection Flow
1. Frontend connects to the WebSocket endpoint with a session ID
2. Backend validates the session (creates new if doesn't exist)
3. If it's a new session, backend automatically sends a greeting message
4. Frontend and backend are now ready for bidirectional communication

## Message Format Overview

### User Input Format (Frontend → Backend)
All messages from the frontend to the backend follow this structure:

```json
{
  "type": "user_input",
  "data": {
    "text": "User's message here",
    "response_to": "optional_question_id",  // When responding to a specific question
    "attachments": [],
    "ui_references": [],
    "frontend_actions": []
  }
}
```

### DirectorMessage Format (Backend → Frontend)
All messages from the backend to the frontend follow this unified structure:

```json
{
  "id": "msg_unique_id",
  "type": "director_message",
  "timestamp": "2024-01-01T10:00:00.000Z",
  "session_id": "session_abc123",
  "source": "director_inbound",
  "slide_data": null,  // Contains slide structure when ready
  "chat_data": {
    "type": "info|question|summary|progress|error",
    "content": "Message content or structured data",
    "actions": [],  // Available user actions
    "progress": null,  // Progress information
    "references": null
  }
}
```

## Streamlined Protocol (New)

### Overview
A new streamlined protocol is being rolled out that improves frontend development by providing clear, purpose-driven messages. During the migration period, both protocols are supported.

### Enabling Streamlined Protocol
The protocol is controlled by feature flags:
- `USE_STREAMLINED_PROTOCOL`: Master switch (default: false)
- `STREAMLINED_PROTOCOL_PERCENTAGE`: A/B testing percentage (0-100)

### Streamlined Message Types

#### 1. Base Message Envelope
```json
{
  "message_id": "msg_unique_id",
  "session_id": "session_xyz",
  "timestamp": "2024-01-01T10:00:00.000Z",
  "type": "chat_message" | "action_request" | "slide_update" | "status_update",
  "payload": { /* type-specific content */ }
}
```

#### 2. Chat Message
For conversational content:
```json
{
  "type": "chat_message",
  "payload": {
    "text": "Main message text",
    "sub_title": "Optional subtitle",
    "list_items": ["Optional", "list", "items"],
    "format": "markdown" | "plain"
  }
}
```

#### 3. Action Request
For user interactions:
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

#### 4. Slide Update
For presentation content with pre-rendered HTML:
```json
{
  "type": "slide_update",
  "payload": {
    "operation": "full_update" | "partial_update",
    "metadata": {
      "main_title": "Presentation Title",
      "overall_theme": "Professional",
      "design_suggestions": "Modern design",
      "target_audience": "Executives",
      "presentation_duration": 15
    },
    "slides": [
      {
        "slide_id": "slide_001",
        "slide_number": 1,
        "html_content": "<div class='slide-container'>...</div>"
      }
    ],
    "affected_slides": ["slide_001"] // For partial updates
  }
}
```

#### 5. Status Update
For progress indication:
```json
{
  "type": "status_update",
  "payload": {
    "status": "idle" | "thinking" | "generating" | "complete" | "error",
    "text": "Processing your presentation...",
    "progress": 65, // Optional percentage
    "estimated_time": 10 // Optional seconds
  }
}
```

### Key Differences from Legacy Protocol
1. **Multiple Messages**: States may send 2-4 focused messages instead of one monolithic message
2. **Pre-rendered HTML**: Slides come with complete HTML, no frontend templating needed
3. **Progress Updates**: Real-time status updates during long operations
4. **Clear Separation**: Each message type maps to a specific UI component

### Migration Notes
- Frontend should detect protocol version based on message structure
- Both protocols will be supported for 12 weeks
- See [Streamlined Protocol Migration Guide](./streamlined_protocol_migration_guide.md) for detailed migration instructions

## State-by-State JSON Flow

### 1. PROVIDE_GREETING State

When a new session starts, the backend automatically sends a greeting:

**Backend → Frontend:**
```json
{
  "id": "msg_abc123",
  "type": "director_message",
  "timestamp": "2024-01-01T10:00:00.000Z",
  "session_id": "session_xyz",
  "source": "director_inbound",
  "slide_data": null,
  "chat_data": {
    "type": "info",
    "content": "Hello! I'm Deckster. I can help you structure a clear and compelling presentation on any topic. What would you like to build today?",
    "actions": null,
    "progress": null,
    "references": null
  }
}
```

**User Response (Frontend → Backend):**
```json
{
  "type": "user_input",
  "data": {
    "text": "I need a presentation about AI in healthcare",
    "response_to": null,
    "attachments": [],
    "ui_references": [],
    "frontend_actions": []
  }
}
```

**What Happens Next:**
- Backend classifies this as intent: `Submit_Initial_Topic`
- State transitions to: `ASK_CLARIFYING_QUESTIONS`

### 2. ASK_CLARIFYING_QUESTIONS State

The Director asks 3-5 clarifying questions to understand the user's needs better.

**Backend → Frontend:**
```json
{
  "id": "msg_def456",
  "type": "director_message",
  "timestamp": "2024-01-01T10:01:00.000Z",
  "session_id": "session_xyz",
  "source": "director_inbound",
  "slide_data": null,
  "chat_data": {
    "type": "question",
    "content": {
      "questions": [
        "Who is the target audience for this presentation (e.g., medical professionals, investors, general public)?",
        "What is the primary goal? Is it to inform, persuade, or educate?",
        "How long should the presentation be (in minutes)?",
        "Are there any specific AI applications in healthcare you want to focus on?",
        "Do you have any data or case studies you'd like to include?"
      ]
    },
    "actions": null
  }
}
```

**User Response (Frontend → Backend):**
```json
{
  "type": "user_input",
  "data": {
    "text": "Target audience: Hospital executives and healthcare IT directors\nGoal: Persuade them to adopt AI solutions\nDuration: 15 minutes\nFocus on: Diagnostic AI and patient care optimization\nI have some ROI data I'll share later",
    "response_to": null,
    "attachments": [],
    "ui_references": [],
    "frontend_actions": []
  }
}
```

**What Happens Next:**
- Backend classifies this as intent: `Submit_Clarification_Answers`
- State transitions to: `CREATE_CONFIRMATION_PLAN`

### 3. CREATE_CONFIRMATION_PLAN State

The Director creates a high-level plan and seeks user confirmation.

**Backend → Frontend:**
```json
{
  "id": "msg_ghi789",
  "type": "director_message",
  "timestamp": "2024-01-01T10:02:00.000Z",
  "session_id": "session_xyz",
  "source": "director_inbound",
  "slide_data": null,
  "chat_data": {
    "type": "summary",
    "content": {
      "summary_of_user_request": "You need a 15-minute persuasive presentation for hospital executives about AI in healthcare, focusing on diagnostic AI and patient care optimization with ROI data.",
      "key_assumptions": [
        "Audience is technically savvy but focused on business value",
        "Presentation should balance technical capabilities with financial benefits",
        "Include real-world implementation examples",
        "Executive summary slide after title for quick overview"
      ],
      "proposed_slide_count": 6
    },
    "actions": [
      {
        "action_id": "accept",
        "type": "accept_changes",
        "label": "Accept",
        "primary": true
      },
      {
        "action_id": "reject",
        "type": "provide_feedback",
        "label": "Request Changes",
        "primary": false
      }
    ]
  }
}
```

**User Response - Accept (Frontend → Backend):**
```json
{
  "type": "user_input",
  "data": {
    "text": "Yes, that looks good. Let's proceed.",
    "response_to": null,
    "attachments": [],
    "ui_references": [],
    "frontend_actions": [
      {
        "action_id": "accept",
        "action_type": "button_click",
        "button_id": "accept_changes",
        "context": {}
      }
    ]
  }
}
```

**What Happens Next:**
- Backend classifies this as intent: `Accept_Plan`
- State transitions to: `GENERATE_STRAWMAN`

### 4. GENERATE_STRAWMAN State

The Director generates the complete presentation structure with detailed slides.

**Backend → Frontend:**
```json
{
  "id": "msg_jkl012",
  "type": "director_message",
  "timestamp": "2024-01-01T10:03:00.000Z",
  "session_id": "session_xyz",
  "source": "director_inbound",
  "slide_data": {
    "type": "complete",
    "slides": [
      {
        "slide_id": "slide_001",
        "slide_number": 1,
        "slide_type": "title_slide",
        "title": "AI in Healthcare: Transforming Patient Care & Operations",
        "narrative": "Set a professional, innovative tone that resonates with healthcare executives",
        "key_points": [
          "Revolutionizing Diagnostics & Patient Care",
          "Proven ROI for Healthcare Organizations",
          "[Hospital Name] | [Date]"
        ],
        "analytics_needed": null,
        "visuals_needed": "**Goal:** Create immediate visual impact. **Content:** Modern healthcare facility with subtle AI/tech overlay. **Style:** Professional, clean, technology-forward",
        "diagrams_needed": null,
        "structure_preference": "Full-bleed hero image with text overlay",
        "speaker_notes": "Open with impact - mention the $150B healthcare AI market by 2030",
        "subtitle": null,
        "body_content": [
          {"type": "text", "content": "Revolutionizing Diagnostics & Patient Care"},
          {"type": "text", "content": "Proven ROI for Healthcare Organizations"},
          {"type": "text", "content": "[Hospital Name] | [Date]"}
        ],
        "layout_type": "content",
        "animations": [],
        "transitions": {}
      },
      {
        "slide_id": "slide_002",
        "slide_number": 2,
        "slide_type": "content_heavy",
        "title": "Executive Summary: AI Impact Metrics",
        "narrative": "Provide immediate value with key metrics that matter to executives",
        "key_points": [
          "30% reduction in diagnostic errors",
          "25% decrease in operational costs",
          "40% improvement in patient satisfaction scores",
          "Average ROI: 3.2x within 18 months"
        ],
        "analytics_needed": "**Goal:** Show compelling ROI data. **Content:** 2x2 grid of metric cards with icons. **Style:** Clean, modern dashboard style with brand colors",
        "visuals_needed": null,
        "diagrams_needed": null,
        "structure_preference": "Grid layout with 4 metric cards",
        "speaker_notes": "These are industry averages from McKinsey and Accenture studies",
        "subtitle": null,
        "body_content": [
          {"type": "text", "content": "30% reduction in diagnostic errors"},
          {"type": "text", "content": "25% decrease in operational costs"},
          {"type": "text", "content": "40% improvement in patient satisfaction scores"},
          {"type": "text", "content": "Average ROI: 3.2x within 18 months"}
        ],
        "layout_type": "content",
        "animations": [],
        "transitions": {}
      }
      // ... more slides ...
    ],
    "presentation_metadata": {
      "title": "AI in Healthcare: Transforming Patient Care & Operations",
      "total_slides": 6,
      "theme": "Professional and data-driven",
      "design_suggestions": "Modern healthcare aesthetic with blue/teal color scheme",
      "target_audience": "Hospital executives and healthcare IT directors",
      "presentation_duration": 15
    }
  },
  "chat_data": {
    "type": "info",
    "content": "Here's your presentation structure. Would you like to make any changes?",
    "actions": [
      {
        "action_id": "accept",
        "type": "accept_changes",
        "label": "Looks good!",
        "primary": true
      },
      {
        "action_id": "refine",
        "type": "request_refinement",
        "label": "Make changes",
        "primary": false,
        "requires_input": true
      }
    ]
  }
}
```

**User Response - Request Refinement (Frontend → Backend):**
```json
{
  "type": "user_input",
  "data": {
    "text": "Can you add more visuals to slide 3 and make it less text-heavy?",
    "response_to": null,
    "attachments": [],
    "ui_references": [],
    "frontend_actions": []
  }
}
```

**What Happens Next:**
- Backend classifies this as intent: `Submit_Refinement_Request`
- State transitions to: `REFINE_STRAWMAN`

### 5. REFINE_STRAWMAN State

The Director refines the presentation based on user feedback.

**Backend → Frontend:**
```json
{
  "id": "msg_mno345",
  "type": "director_message",
  "timestamp": "2024-01-01T10:04:00.000Z",
  "session_id": "session_xyz",
  "source": "director_inbound",
  "slide_data": {
    "type": "complete",
    "slides": [
      // ... previous slides unchanged ...
      {
        "slide_id": "slide_003",
        "slide_number": 3,
        "slide_type": "visual_heavy",  // Changed from content_heavy
        "title": "AI Applications in Clinical Settings",
        "narrative": "Showcase practical AI applications with strong visual elements",
        "key_points": [
          "Diagnostic Imaging: 95% accuracy in early detection",
          "Predictive Analytics: Preventing readmissions",
          "Clinical Decision Support: Real-time recommendations"
        ],
        "analytics_needed": null,
        "visuals_needed": "**Goal:** Create a visually stunning slide that immediately communicates AI's impact. **Content:** Three-panel layout showing: 1) AI analyzing medical scan with highlighted areas, 2) Dashboard showing predictive analytics preventing readmission, 3) Doctor using tablet with AI recommendations overlay. **Style:** Modern, clean, with subtle animation effects suggesting real-time processing",
        "diagrams_needed": "**Goal:** Show the interconnected nature of AI systems. **Content:** Simple flowchart showing data flow from patient → AI system → clinical insights → improved outcomes. **Style:** Minimalist with icons, using arrow animations",
        "structure_preference": "Three-column visual layout with minimal text overlay",
        "speaker_notes": "Emphasize that these are proven technologies, not future concepts",
        // ... rest of slide data ...
      }
      // ... remaining slides ...
    ],
    "presentation_metadata": {
      // ... same as before ...
    }
  },
  "chat_data": {
    "type": "info",
    "content": "I've updated slide 3 with more visuals and less text. The slide now features a three-panel visual layout with minimal text overlay. Would you like any other changes?",
    "actions": [
      {
        "action_id": "accept",
        "type": "accept_changes",
        "label": "Perfect, thanks!",
        "primary": true
      },
      {
        "action_id": "refine",
        "type": "request_refinement",
        "label": "Make more changes",
        "primary": false,
        "requires_input": true
      }
    ]
  }
}
```

## Intent-Based Routing

The system uses intelligent intent classification to determine state transitions:

| User Intent | Current State | Next State | Description |
|------------|---------------|------------|-------------|
| Submit_Initial_Topic | PROVIDE_GREETING | ASK_CLARIFYING_QUESTIONS | User provides initial presentation topic |
| Submit_Clarification_Answers | ASK_CLARIFYING_QUESTIONS | CREATE_CONFIRMATION_PLAN | User answers clarifying questions |
| Accept_Plan | CREATE_CONFIRMATION_PLAN | GENERATE_STRAWMAN | User accepts the proposed plan |
| Reject_Plan | CREATE_CONFIRMATION_PLAN | CREATE_CONFIRMATION_PLAN | User wants plan changes (loops back) |
| Accept_Strawman | GENERATE_STRAWMAN | (End/Complete) | User accepts the presentation |
| Submit_Refinement_Request | GENERATE_STRAWMAN | REFINE_STRAWMAN | User requests changes |
| Change_Topic | Any State | ASK_CLARIFYING_QUESTIONS | User wants to start over |
| Change_Parameter | Any State | CREATE_CONFIRMATION_PLAN | User wants to modify parameters |
| Ask_Help_Or_Question | Any State | (Same State) | User asks for help |

## Error Handling

When errors occur, the system sends standardized error messages:

**Backend → Frontend (Error):**
```json
{
  "id": "msg_error_789",
  "type": "director_message",
  "timestamp": "2024-01-01T10:05:00.000Z",
  "session_id": "session_xyz",
  "source": "director_inbound",
  "slide_data": null,
  "chat_data": {
    "type": "error",
    "content": "I encountered an error: Unable to generate presentation structure. Please try again.",
    "actions": null,
    "progress": null,
    "references": null
  }
}
```

### Common Error Scenarios
1. **Token Limit Exceeded**: When AI models hit token limits
2. **Invalid Input**: When user input fails validation
3. **Connection Issues**: When WebSocket connection is interrupted
4. **Processing Errors**: When AI generation fails

## Key Implementation Details

### Session Management
- Sessions are stored in Supabase with a unique session_id
- Session data includes: current_state, conversation_history, user_initial_request, clarifying_answers, confirmation_plan, and presentation_strawman
- Sessions persist across reconnections

### Message Processing Flow
1. User sends message via WebSocket
2. Intent router classifies the user's intent
3. State machine determines next state based on intent
4. Director agent processes request in context of new state
5. Response is packaged in DirectorMessage format
6. Message sent back to frontend via WebSocket

### Data Persistence
- All conversation history is stored in the session
- Key data points (initial request, answers, plans, strawman) are saved separately for easy access
- This allows for session recovery and context preservation

## Best Practices for Frontend Implementation

1. **Always include session_id** in the WebSocket connection URL
2. **Handle all chat_data types**: info, question, summary, progress, error
3. **Preserve user actions**: When action buttons are provided, use them appropriately
4. **Track state**: Keep track of the current workflow state for better UX
5. **Handle reconnections**: Implement reconnection logic with exponential backoff
6. **Validate messages**: Ensure all messages conform to the expected format before processing