# Streamlined WebSocket Protocol Migration Guide

## Overview

This guide helps frontend developers migrate from the legacy DirectorMessage format to the new streamlined WebSocket protocol. The new protocol improves frontend development by providing clear, purpose-driven messages that map directly to UI components.

## Key Benefits

1. **Simplified Frontend Logic**: Each message type maps to a specific UI component
2. **Better Async Support**: Progress updates and status messages enable responsive UI
3. **Pre-rendered HTML**: Slides come ready to display, no frontend templating needed
4. **Cleaner Code**: No more nested parsing or complex message handling

## Migration Timeline

- **Current**: Both protocols supported via feature flag
- **Week 1-4**: Gradual rollout (0% → 100%)
- **Week 12**: Legacy protocol deprecated
- **Week 16**: Legacy protocol removed

## Message Type Comparison

### Legacy Format
```json
{
  "id": "msg_unique_id",
  "type": "director_message",
  "timestamp": "2024-01-01T10:00:00.000Z",
  "session_id": "session_abc123",
  "source": "director_inbound",
  "slide_data": { /* optional */ },
  "chat_data": { /* optional */ }
}
```

### New Streamlined Format
```json
{
  "message_id": "msg_unique_id",
  "session_id": "session_xyz",
  "timestamp": "2024-01-01T10:00:00.000Z",
  "type": "chat_message" | "action_request" | "slide_update" | "status_update",
  "payload": { /* type-specific content */ }
}
```

## Message Types

### 1. Chat Message
Display conversational content in the chat interface.

```typescript
interface ChatMessage {
  type: "chat_message";
  payload: {
    text: string;
    sub_title?: string;
    list_items?: string[];
    format: "markdown" | "plain";
  };
}
```

**UI Mapping**: Chat bubble, conversation panel

### 2. Action Request
Present interactive buttons to the user.

```typescript
interface ActionRequest {
  type: "action_request";
  payload: {
    prompt_text: string;
    actions: Array<{
      label: string;
      value: string;
      primary: boolean;
      requires_input?: boolean;
    }>;
  };
}
```

**UI Mapping**: Button group, action panel

### 3. Slide Update
Update the presentation view with pre-rendered HTML.

```typescript
interface SlideUpdate {
  type: "slide_update";
  payload: {
    operation: "full_update" | "partial_update";
    metadata: {
      main_title: string;
      overall_theme: string;
      design_suggestions: string;
      target_audience: string;
      presentation_duration: number;
    };
    slides: Array<{
      slide_id: string;
      slide_number: number;
      html_content: string;
    }>;
    affected_slides?: string[]; // For partial updates
  };
}
```

**UI Mapping**: Slide viewer, presentation canvas

### 4. Status Update
Show processing status or progress.

```typescript
interface StatusUpdate {
  type: "status_update";
  payload: {
    status: "idle" | "thinking" | "generating" | "complete" | "error";
    text: string;
    progress?: number; // 0-100
    estimated_time?: number; // seconds
  };
}
```

**UI Mapping**: Progress bar, status indicator

## Frontend Implementation Examples

### Before (Legacy)
```javascript
// Complex nested parsing
socket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'director_message') {
    // Parse chat data
    if (message.chat_data) {
      if (message.chat_data.type === 'question') {
        updateQuestions(message.chat_data.content.questions);
      } else if (message.chat_data.type === 'summary') {
        updateSummary(message.chat_data.content);
        if (message.chat_data.actions) {
          showActions(message.chat_data.actions);
        }
      }
    }
    
    // Parse slide data
    if (message.slide_data) {
      updateSlides(message.slide_data);
    }
  }
};
```

### After (Streamlined)
```javascript
// Clean message handling
socket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'chat_message':
      chatUI.render(message.payload);
      break;
      
    case 'action_request':
      actionUI.render(message.payload);
      break;
      
    case 'slide_update':
      slideUI.render(message.payload);
      break;
      
    case 'status_update':
      statusUI.render(message.payload);
      break;
  }
};
```

## React Component Example

```jsx
function WebSocketHandler({ socket }) {
  const [messages, setMessages] = useState([]);
  const [slides, setSlides] = useState([]);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      switch(message.type) {
        case 'chat_message':
          setMessages(prev => [...prev, {
            id: message.message_id,
            type: 'chat',
            ...message.payload
          }]);
          break;
          
        case 'action_request':
          setMessages(prev => [...prev, {
            id: message.message_id,
            type: 'actions',
            ...message.payload
          }]);
          break;
          
        case 'slide_update':
          if (message.payload.operation === 'full_update') {
            setSlides(message.payload.slides);
          } else {
            // Partial update
            setSlides(prev => {
              const updated = [...prev];
              message.payload.slides.forEach(slide => {
                const index = updated.findIndex(s => s.slide_id === slide.slide_id);
                if (index >= 0) updated[index] = slide;
              });
              return updated;
            });
          }
          break;
          
        case 'status_update':
          setStatus(message.payload);
          break;
      }
    };
  }, [socket]);

  return (
    <>
      <StatusBar status={status} />
      <ChatPanel messages={messages} />
      <SlideViewer slides={slides} />
    </>
  );
}
```

## State-by-State Message Flow

### PROVIDE_GREETING
**Messages**: 1 chat_message
```javascript
// You'll receive:
{
  "type": "chat_message",
  "payload": {
    "text": "Hello! I'm Deckster..."
  }
}
```

### ASK_CLARIFYING_QUESTIONS
**Messages**: 1 chat_message with list_items
```javascript
// You'll receive:
{
  "type": "chat_message",
  "payload": {
    "text": "Great topic! I have some questions:",
    "list_items": ["Question 1?", "Question 2?", ...]
  }
}
```

### CREATE_CONFIRMATION_PLAN
**Messages**: 1 chat_message + 1 action_request
```javascript
// First message:
{
  "type": "chat_message",
  "payload": {
    "text": "Based on your input, I'll create a 10-slide presentation.",
    "sub_title": "Key assumptions:",
    "list_items": ["Assumption 1", "Assumption 2", ...]
  }
}

// Second message:
{
  "type": "action_request",
  "payload": {
    "prompt_text": "Does this look correct?",
    "actions": [
      {"label": "Yes, proceed!", "value": "accept_plan", "primary": true},
      {"label": "Make changes", "value": "reject_plan", "primary": false}
    ]
  }
}
```

### GENERATE_STRAWMAN
**Messages**: 1 status_update + 1 slide_update + 1 action_request
```javascript
// First (immediate):
{
  "type": "status_update",
  "payload": {
    "status": "generating",
    "text": "Creating your presentation...",
    "progress": 0,
    "estimated_time": 20
  }
}

// Second (after generation):
{
  "type": "slide_update",
  "payload": {
    "operation": "full_update",
    "metadata": { ... },
    "slides": [
      {
        "slide_id": "slide_001",
        "slide_number": 1,
        "html_content": "<div class='slide-container'>...</div>"
      }
    ]
  }
}

// Third:
{
  "type": "action_request",
  "payload": {
    "prompt_text": "Your presentation is ready!",
    "actions": [ ... ]
  }
}
```

## HTML Slide Rendering

Slides now come with pre-rendered HTML. Simply inject into your container:

```javascript
function SlideViewer({ slides }) {
  const [currentSlide, setCurrentSlide] = useState(0);
  
  return (
    <div className="slide-viewer">
      <div 
        className="slide-content"
        dangerouslySetInnerHTML={{ 
          __html: slides[currentSlide]?.html_content || '' 
        }}
      />
      <SlideNavigation 
        current={currentSlide}
        total={slides.length}
        onChange={setCurrentSlide}
      />
    </div>
  );
}
```

## Error Handling

Errors now come as status_update + chat_message:

```javascript
socket.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'status_update' && message.payload.status === 'error') {
    // Show error state
    showError(message.payload.text);
  }
};
```

## Testing Your Implementation

1. **Enable streamlined protocol for your session**:
   ```javascript
   // Add to connection URL
   const socket = new WebSocket('wss://api.deckster.ai/ws?session_id=test_streamlined_123');
   ```

2. **Log all messages during development**:
   ```javascript
   socket.onmessage = (event) => {
     const message = JSON.parse(event.data);
     console.log('Streamlined message:', message.type, message);
     // ... handle message
   };
   ```

3. **Handle both protocols during migration**:
   ```javascript
   socket.onmessage = (event) => {
     const message = JSON.parse(event.data);
     
     if (message.type === 'director_message') {
       // Legacy handler
       handleLegacyMessage(message);
     } else {
       // Streamlined handler
       handleStreamlinedMessage(message);
     }
   };
   ```

## TypeScript Definitions

```typescript
// streamlined-protocol.d.ts
export type StreamlinedMessageType = 
  | "chat_message" 
  | "action_request" 
  | "slide_update" 
  | "status_update";

export interface BaseMessage {
  message_id: string;
  session_id: string;
  timestamp: string;
  type: StreamlinedMessageType;
}

export interface ChatMessage extends BaseMessage {
  type: "chat_message";
  payload: {
    text: string;
    sub_title?: string;
    list_items?: string[];
    format: "markdown" | "plain";
  };
}

export interface ActionRequest extends BaseMessage {
  type: "action_request";
  payload: {
    prompt_text: string;
    actions: Array<{
      label: string;
      value: string;
      primary: boolean;
      requires_input?: boolean;
    }>;
  };
}

export interface SlideUpdate extends BaseMessage {
  type: "slide_update";
  payload: {
    operation: "full_update" | "partial_update";
    metadata: SlideMetadata;
    slides: SlideContent[];
    affected_slides?: string[];
  };
}

export interface StatusUpdate extends BaseMessage {
  type: "status_update";
  payload: {
    status: "idle" | "thinking" | "generating" | "complete" | "error";
    text: string;
    progress?: number;
    estimated_time?: number;
  };
}

export type StreamlinedMessage = 
  | ChatMessage 
  | ActionRequest 
  | SlideUpdate 
  | StatusUpdate;
```

## Migration Checklist

- [ ] Update WebSocket message handler to support message type switching
- [ ] Create UI components for each message type
- [ ] Implement slide HTML rendering
- [ ] Add progress/status indicators
- [ ] Update error handling
- [ ] Test with both protocols enabled
- [ ] Add TypeScript types (if using TypeScript)
- [ ] Update any message logging/debugging tools
- [ ] Plan for legacy protocol removal

## Support

For questions or issues during migration:
1. Check the message examples in this guide
2. Enable debug logging to see actual messages
3. Test with `USE_STREAMLINED_PROTOCOL=true` in development
4. Contact the backend team for protocol-specific questions

Remember: The backend supports both protocols during the migration period, so you can migrate at your own pace!