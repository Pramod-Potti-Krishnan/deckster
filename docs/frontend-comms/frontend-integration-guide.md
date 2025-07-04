# Frontend WebSocket Integration Guide

This guide provides comprehensive instructions for integrating your frontend application with the Deckster.xyz WebSocket API. It covers connection setup, authentication, message handling, UI updates, and error management.

## Table of Contents

1. [Overview](#overview)
2. [WebSocket Connection Setup](#websocket-connection-setup)
3. [Authentication Methods](#authentication-methods)
4. [Message Formats and Types](#message-formats-and-types)
5. [Handling Different Response Types](#handling-different-response-types)
6. [UI Update Patterns](#ui-update-patterns)
7. [Error Handling](#error-handling)
8. [Code Examples](#code-examples)
9. [Best Practices](#best-practices)

## Overview

The Deckster.xyz WebSocket API enables real-time bidirectional communication between the frontend and the Director agents. The system uses JSON messages for all communications, with HTML-embedded visual content for slide previews.

### Key Features
- JWT-based authentication
- Real-time message streaming
- Automatic reconnection with session recovery
- Progress tracking and status updates
- Concurrent slide and chat data handling

## WebSocket Connection Setup

### Basic Connection

```javascript
class DecksterWebSocket {
  constructor(url = 'wss://api.deckster.xyz/ws') {
    this.url = url;
    this.ws = null;
    this.sessionId = null;
    this.messageHandlers = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.heartbeatInterval = null;
  }

  async connect(token) {
    return new Promise((resolve, reject) => {
      try {
        // Include JWT in connection URL or headers
        this.ws = new WebSocket(`${this.url}?token=${token}`);
        
        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = (event) => {
          this.handleClose(event);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, 30000); // Every 30 seconds
  }

  handleClose(event) {
    console.log('WebSocket closed:', event.code, event.reason);
    clearInterval(this.heartbeatInterval);
    
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnect();
    }
  }

  async reconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(async () => {
      try {
        await this.connect(this.getStoredToken());
        // Restore session if available
        if (this.sessionId) {
          this.send({
            type: 'restore_session',
            session_id: this.sessionId
          });
        }
      } catch (error) {
        console.error('Reconnection failed:', error);
      }
    }, delay);
  }
}
```

### Connection with React Hook

```javascript
import { useEffect, useState, useCallback, useRef } from 'react';

export function useDecksterWebSocket(token) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!token) return;

    const ws = new DecksterWebSocket();
    wsRef.current = ws;

    // Setup message handlers
    ws.on('director_message', (message) => {
      setMessages(prev => [...prev, message]);
    });

    // Connect
    ws.connect(token)
      .then(() => setConnected(true))
      .catch(err => setError(err));

    return () => {
      ws.disconnect();
    };
  }, [token]);

  const sendMessage = useCallback((data) => {
    if (wsRef.current && connected) {
      wsRef.current.send(data);
    }
  }, [connected]);

  return { connected, messages, error, sendMessage };
}
```

## Authentication Methods

### JWT in Headers (Recommended)

```javascript
class AuthenticatedWebSocket extends WebSocket {
  constructor(url, token) {
    super(url, [], {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
  }
}
```

### JWT in First Message

```javascript
async connectWithAuth(token) {
  this.ws = new WebSocket(this.url);
  
  return new Promise((resolve, reject) => {
    this.ws.onopen = () => {
      // Send token as first message
      this.ws.send(JSON.stringify({
        type: 'auth',
        token: token
      }));
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'auth_success') {
        this.sessionId = message.session_id;
        resolve();
      } else if (message.type === 'auth_failed') {
        reject(new Error(message.reason));
      }
    };
  });
}
```

### Token Refresh Strategy

```javascript
class TokenManager {
  constructor() {
    this.token = null;
    this.refreshToken = null;
    this.expiryTime = null;
  }

  async getValidToken() {
    // Check if token is still valid (with 5 minute buffer)
    if (this.token && this.expiryTime > Date.now() + 300000) {
      return this.token;
    }

    // Refresh token
    return await this.refreshAccessToken();
  }

  async refreshAccessToken() {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        refresh_token: this.refreshToken
      })
    });

    const data = await response.json();
    this.token = data.access_token;
    this.expiryTime = Date.now() + (data.expires_in * 1000);
    
    return this.token;
  }
}
```

## Message Formats and Types

### Sending Messages to Director

```javascript
// Basic user input message
const userMessage = {
  message_id: generateMessageId(), // Use UUID v4
  timestamp: new Date().toISOString(),
  session_id: sessionId,
  type: "user_input",
  data: {
    text: "Create a B2B SaaS pitch deck for our AI startup",
    response_to: null, // Or question_id if responding to a question
    attachments: [],
    ui_references: [],
    frontend_actions: []
  }
};

// Responding to a clarification question
const clarificationResponse = {
  message_id: generateMessageId(),
  timestamp: new Date().toISOString(),
  session_id: sessionId,
  type: "user_input",
  data: {
    text: "Our target audience is enterprise CTOs and VPs of Engineering",
    response_to: "q_audience_001",
    attachments: [],
    ui_references: [],
    frontend_actions: []
  }
};

// File upload with text
const fileUploadMessage = {
  message_id: generateMessageId(),
  timestamp: new Date().toISOString(),
  session_id: sessionId,
  type: "user_input",
  data: {
    text: "Here's our brand guidelines and financial data",
    response_to: null,
    attachments: [
      {
        type: "file",
        file_id: "file_001",
        filename: "brand_guidelines.pdf",
        mime_type: "application/pdf",
        size_bytes: 5242880,
        upload_url: "https://storage.example.com/uploads/session_abc123/file_001"
      }
    ],
    ui_references: [],
    frontend_actions: []
  }
};

// Referencing specific slide elements
const slideEditMessage = {
  message_id: generateMessageId(),
  timestamp: new Date().toISOString(),
  session_id: sessionId,
  type: "user_input",
  data: {
    text: "Make this chart a pie chart with vibrant colors",
    response_to: null,
    attachments: [],
    ui_references: [
      {
        reference_type: "element",
        slide_id: "slide_3",
        element_id: "chart_1",
        css_selector: "#chart_1",
        html_context: document.getElementById('chart_1').outerHTML
      }
    ],
    frontend_actions: []
  }
};

// User action (button click)
const actionMessage = {
  message_id: generateMessageId(),
  timestamp: new Date().toISOString(),
  session_id: sessionId,
  type: "user_input",
  data: {
    text: "",
    response_to: null,
    attachments: [],
    ui_references: [],
    frontend_actions: [
      {
        action_id: "action_001",
        action_type: "button_click",
        button_id: "accept_changes",
        context: {
          presented_changes: ["slide_3", "slide_5"]
        }
      }
    ]
  }
};
```

### Receiving Messages from Director

```javascript
// Director message structure
const directorMessage = {
  message_id: "msg_unique_id_123",
  timestamp: "2024-01-01T10:00:00Z",
  session_id: "session_abc123",
  type: "director_message",
  source: "director_inbound" || "director_outbound",
  data: {
    slide_data: {
      slides: [/* slide objects */],
      presentation_metadata: {/* metadata */}
    },
    chat_data: {
      type: "question" || "summary" || "progress" || "action_required",
      content: {/* content object */},
      actions: [/* available actions */],
      progress: {/* progress info */}
    }
  }
};
```

## Handling Different Response Types

### Message Type Handler

```javascript
class MessageHandler {
  constructor() {
    this.handlers = {
      question: this.handleQuestion.bind(this),
      summary: this.handleSummary.bind(this),
      progress: this.handleProgress.bind(this),
      action_required: this.handleActionRequired.bind(this),
      slides: this.handleSlides.bind(this)
    };
  }

  processDirectorMessage(message) {
    const { data } = message;
    
    // Handle chat data
    if (data.chat_data) {
      const handler = this.handlers[data.chat_data.type];
      if (handler) {
        handler(data.chat_data);
      }
    }
    
    // Handle slide data
    if (data.slide_data && data.slide_data.slides.length > 0) {
      this.handlers.slides(data.slide_data);
    }
  }

  handleQuestion(chatData) {
    const { content, actions } = chatData;
    
    // Display question in chat UI
    displayChatMessage({
      type: 'question',
      message: content.message,
      context: content.context,
      options: content.options,
      questionId: content.question_id,
      required: content.required
    });
    
    // Enable response UI (text input, option buttons, etc.)
    if (content.options) {
      showOptionButtons(content.options, content.question_id);
    } else {
      enableTextInput(content.question_id);
    }
  }

  handleProgress(chatData) {
    const { content, progress } = chatData;
    
    // Update progress bar
    updateProgressBar(progress.percentage);
    
    // Show current step
    updateStatusMessage(progress.current_step);
    
    // Update step list
    updateStepList({
      completed: progress.steps_completed,
      current: progress.current_step,
      remaining: progress.estimated_time_remaining
    });
  }

  handleSlides(slideData) {
    const { slides, presentation_metadata } = slideData;
    
    slides.forEach(slide => {
      // Update or create slide in presentation view
      updateSlide({
        id: slide.slide_id,
        number: slide.slide_number,
        title: slide.title,
        html: slide.html_content,
        assets: slide.assets
      });
      
      // Load assets
      loadSlideAssets(slide.slide_id, slide.assets);
    });
    
    // Update presentation metadata
    updatePresentationInfo(presentation_metadata);
  }

  handleActionRequired(chatData) {
    const { content, actions } = chatData;
    
    // Display message
    displayChatMessage({
      type: 'action_required',
      message: content.message
    });
    
    // Show action buttons
    actions.forEach(action => {
      showActionButton({
        id: action.action_id,
        label: action.label,
        primary: action.primary,
        onClick: () => this.executeAction(action)
      });
    });
  }
}
```

## UI Update Patterns

### Chat and Slides State Management

```javascript
// Using React Context for state management
import React, { createContext, useContext, useReducer } from 'react';

const PresentationContext = createContext();

const initialState = {
  sessionId: null,
  slides: [],
  currentSlide: 0,
  chatMessages: [],
  isProcessing: false,
  progress: {
    percentage: 0,
    currentStep: '',
    stepsCompleted: []
  },
  presentationMetadata: null
};

function presentationReducer(state, action) {
  switch (action.type) {
    case 'ADD_CHAT_MESSAGE':
      return {
        ...state,
        chatMessages: [...state.chatMessages, action.payload]
      };
    
    case 'UPDATE_SLIDES':
      return {
        ...state,
        slides: action.payload.slides,
        presentationMetadata: action.payload.metadata
      };
    
    case 'UPDATE_PROGRESS':
      return {
        ...state,
        progress: action.payload
      };
    
    case 'SET_PROCESSING':
      return {
        ...state,
        isProcessing: action.payload
      };
    
    default:
      return state;
  }
}

export function PresentationProvider({ children }) {
  const [state, dispatch] = useReducer(presentationReducer, initialState);
  
  return (
    <PresentationContext.Provider value={{ state, dispatch }}>
      {children}
    </PresentationContext.Provider>
  );
}
```

### Real-time UI Updates

```javascript
// React component for handling real-time updates
function PresentationEditor() {
  const { state, dispatch } = useContext(PresentationContext);
  const { connected, sendMessage } = useDecksterWebSocket(token);
  
  // Handle incoming messages
  useEffect(() => {
    const handleDirectorMessage = (message) => {
      const { data } = message;
      
      // Update chat
      if (data.chat_data) {
        dispatch({
          type: 'ADD_CHAT_MESSAGE',
          payload: {
            id: message.message_id,
            timestamp: message.timestamp,
            type: data.chat_data.type,
            content: data.chat_data.content,
            actions: data.chat_data.actions
          }
        });
      }
      
      // Update slides
      if (data.slide_data) {
        dispatch({
          type: 'UPDATE_SLIDES',
          payload: {
            slides: data.slide_data.slides,
            metadata: data.slide_data.presentation_metadata
          }
        });
      }
      
      // Update progress
      if (data.chat_data?.progress) {
        dispatch({
          type: 'UPDATE_PROGRESS',
          payload: data.chat_data.progress
        });
      }
    };
    
    // Subscribe to WebSocket messages
    ws.on('director_message', handleDirectorMessage);
    
    return () => {
      ws.off('director_message', handleDirectorMessage);
    };
  }, []);
  
  return (
    <div className="presentation-editor">
      <SlideViewer slides={state.slides} currentSlide={state.currentSlide} />
      <ChatPanel messages={state.chatMessages} onSendMessage={sendMessage} />
      <ProgressBar progress={state.progress} />
    </div>
  );
}
```

### Optimistic UI Updates

```javascript
// Optimistic updates for better UX
function useOptimisticUpdates() {
  const [optimisticState, setOptimisticState] = useState({});
  
  const applyOptimisticUpdate = useCallback((action, data) => {
    // Apply update optimistically
    setOptimisticState(prev => ({
      ...prev,
      [action]: data
    }));
    
    // Return rollback function
    return () => {
      setOptimisticState(prev => {
        const newState = { ...prev };
        delete newState[action];
        return newState;
      });
    };
  }, []);
  
  return { optimisticState, applyOptimisticUpdate };
}

// Usage in component
function SlideEditor({ slide }) {
  const { optimisticState, applyOptimisticUpdate } = useOptimisticUpdates();
  const { sendMessage } = useDecksterWebSocket();
  
  const handleChartTypeChange = async (newType) => {
    // Apply optimistic update
    const rollback = applyOptimisticUpdate(`chart_${slide.id}`, { type: newType });
    
    try {
      // Send actual request
      await sendMessage({
        type: 'user_input',
        data: {
          text: `Change chart to ${newType}`,
          ui_references: [{
            reference_type: 'element',
            slide_id: slide.id,
            element_id: 'chart_1'
          }]
        }
      });
    } catch (error) {
      // Rollback on error
      rollback();
      showError('Failed to update chart type');
    }
  };
  
  // Merge optimistic state with actual state
  const chartType = optimisticState[`chart_${slide.id}`]?.type || slide.chart?.type;
}
```

## Error Handling

### WebSocket Error Handling

```javascript
class ErrorHandler {
  constructor() {
    this.errorCallbacks = new Map();
    this.globalErrorHandler = null;
  }

  handleWebSocketError(error) {
    console.error('WebSocket error:', error);
    
    // Categorize error
    const errorType = this.categorizeError(error);
    
    switch (errorType) {
      case 'AUTH_FAILED':
        this.handleAuthError(error);
        break;
      
      case 'CONNECTION_LOST':
        this.handleConnectionError(error);
        break;
      
      case 'RATE_LIMIT':
        this.handleRateLimitError(error);
        break;
      
      case 'VALIDATION_ERROR':
        this.handleValidationError(error);
        break;
      
      default:
        this.handleGenericError(error);
    }
  }

  categorizeError(error) {
    if (error.code === 1008 || error.message?.includes('Unauthorized')) {
      return 'AUTH_FAILED';
    }
    if (error.code >= 1001 && error.code <= 1003) {
      return 'CONNECTION_LOST';
    }
    if (error.message?.includes('rate limit')) {
      return 'RATE_LIMIT';
    }
    if (error.message?.includes('validation')) {
      return 'VALIDATION_ERROR';
    }
    return 'GENERIC';
  }

  handleAuthError(error) {
    // Clear stored tokens
    localStorage.removeItem('access_token');
    
    // Redirect to login
    window.location.href = '/login';
  }

  handleConnectionError(error) {
    // Show reconnection UI
    showNotification({
      type: 'warning',
      message: 'Connection lost. Attempting to reconnect...',
      persistent: true,
      id: 'connection-error'
    });
  }

  handleRateLimitError(error) {
    const retryAfter = error.retry_after || 60;
    
    showNotification({
      type: 'error',
      message: `Rate limit exceeded. Please try again in ${retryAfter} seconds.`,
      duration: retryAfter * 1000
    });
  }
}
```

### Retry Logic with Exponential Backoff

```javascript
class RetryManager {
  constructor(maxRetries = 3, baseDelay = 1000) {
    this.maxRetries = maxRetries;
    this.baseDelay = baseDelay;
    this.retryQueue = new Map();
  }

  async withRetry(operation, operationId) {
    let retries = 0;
    let lastError;
    
    while (retries < this.maxRetries) {
      try {
        const result = await operation();
        this.retryQueue.delete(operationId);
        return result;
      } catch (error) {
        lastError = error;
        retries++;
        
        if (retries < this.maxRetries) {
          const delay = this.baseDelay * Math.pow(2, retries - 1);
          console.log(`Retry ${retries}/${this.maxRetries} after ${delay}ms`);
          
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    throw new Error(`Operation failed after ${this.maxRetries} retries: ${lastError.message}`);
  }
}

// Usage
const retryManager = new RetryManager();

async function sendMessageWithRetry(message) {
  return retryManager.withRetry(
    () => ws.send(message),
    message.message_id
  );
}
```

## Code Examples

### Complete WebSocket Client Implementation

```javascript
// websocket-client.js
import EventEmitter from 'events';

export class DecksterClient extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = {
      url: config.url || 'wss://api.deckster.xyz/ws',
      reconnectDelay: config.reconnectDelay || 1000,
      maxReconnectDelay: config.maxReconnectDelay || 30000,
      heartbeatInterval: config.heartbeatInterval || 30000,
      messageTimeout: config.messageTimeout || 30000,
      ...config
    };
    
    this.ws = null;
    this.connected = false;
    this.sessionId = null;
    this.pendingMessages = new Map();
    this.messageQueue = [];
  }

  async connect(token) {
    this.token = token;
    
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.config.url);
      
      this.ws.onopen = async () => {
        console.log('WebSocket connected');
        this.connected = true;
        
        // Send authentication
        await this.authenticate(token);
        
        // Process queued messages
        this.processMessageQueue();
        
        // Start heartbeat
        this.startHeartbeat();
        
        this.emit('connected');
        resolve();
      };
      
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse message:', error);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', error);
        reject(error);
      };
      
      this.ws.onclose = (event) => {
        this.connected = false;
        this.stopHeartbeat();
        this.emit('disconnected', event);
        
        if (event.code !== 1000) {
          this.scheduleReconnect();
        }
      };
    });
  }

  async authenticate(token) {
    return this.sendWithResponse({
      type: 'auth',
      token: token
    }, 'auth_response');
  }

  async send(message) {
    if (!this.connected) {
      this.messageQueue.push(message);
      return;
    }
    
    const fullMessage = {
      ...message,
      message_id: message.message_id || this.generateMessageId(),
      timestamp: message.timestamp || new Date().toISOString(),
      session_id: this.sessionId
    };
    
    this.ws.send(JSON.stringify(fullMessage));
    return fullMessage;
  }

  async sendWithResponse(message, responseType, timeout = this.config.messageTimeout) {
    const messageId = this.generateMessageId();
    const fullMessage = { ...message, message_id: messageId };
    
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pendingMessages.delete(messageId);
        reject(new Error(`Message timeout: ${responseType}`));
      }, timeout);
      
      this.pendingMessages.set(messageId, {
        resolve: (response) => {
          clearTimeout(timer);
          resolve(response);
        },
        reject: (error) => {
          clearTimeout(timer);
          reject(error);
        },
        responseType
      });
      
      this.send(fullMessage);
    });
  }

  handleMessage(message) {
    // Handle auth response
    if (message.type === 'auth_response') {
      if (message.success) {
        this.sessionId = message.session_id;
        this.emit('authenticated', message);
      } else {
        this.emit('auth_failed', message);
      }
      return;
    }
    
    // Handle pending message responses
    const pending = this.pendingMessages.get(message.response_to);
    if (pending) {
      this.pendingMessages.delete(message.response_to);
      
      if (message.error) {
        pending.reject(new Error(message.error.message));
      } else {
        pending.resolve(message);
      }
      return;
    }
    
    // Emit message for handling
    this.emit('message', message);
    
    // Emit specific message types
    if (message.type === 'director_message') {
      this.emit('director_message', message);
      
      // Further emit based on chat data type
      if (message.data?.chat_data?.type) {
        this.emit(`chat_${message.data.chat_data.type}`, message);
      }
      
      // Emit if slides are included
      if (message.data?.slide_data?.slides?.length > 0) {
        this.emit('slides_update', message);
      }
    }
  }

  processMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      if (this.connected) {
        this.send({ type: 'ping' });
      }
    }, this.config.heartbeatInterval);
  }

  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  scheduleReconnect() {
    // Implement exponential backoff
    const delay = Math.min(
      this.config.reconnectDelay * Math.pow(2, this.reconnectAttempts || 0),
      this.config.maxReconnectDelay
    );
    
    this.reconnectAttempts = (this.reconnectAttempts || 0) + 1;
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect(this.token).catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  generateMessageId() {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}
```

### React Integration Example

```javascript
// hooks/useDeckster.js
import { useEffect, useState, useCallback, useRef } from 'react';
import { DecksterClient } from '../lib/websocket-client';

export function useDeckster(token) {
  const [state, setState] = useState({
    connected: false,
    authenticated: false,
    sessionId: null,
    slides: [],
    chatMessages: [],
    progress: null,
    error: null
  });
  
  const clientRef = useRef(null);
  
  useEffect(() => {
    if (!token) return;
    
    const client = new DecksterClient();
    clientRef.current = client;
    
    // Setup event handlers
    client.on('connected', () => {
      setState(prev => ({ ...prev, connected: true }));
    });
    
    client.on('authenticated', (message) => {
      setState(prev => ({
        ...prev,
        authenticated: true,
        sessionId: message.session_id
      }));
    });
    
    client.on('director_message', (message) => {
      const { data } = message;
      
      setState(prev => {
        const newState = { ...prev };
        
        // Update chat messages
        if (data.chat_data) {
          newState.chatMessages = [
            ...prev.chatMessages,
            {
              id: message.message_id,
              timestamp: message.timestamp,
              ...data.chat_data
            }
          ];
        }
        
        // Update slides
        if (data.slide_data?.slides) {
          newState.slides = data.slide_data.slides;
        }
        
        // Update progress
        if (data.chat_data?.progress) {
          newState.progress = data.chat_data.progress;
        }
        
        return newState;
      });
    });
    
    client.on('error', (error) => {
      setState(prev => ({ ...prev, error: error.message }));
    });
    
    client.on('disconnected', () => {
      setState(prev => ({ ...prev, connected: false }));
    });
    
    // Connect
    client.connect(token).catch(error => {
      setState(prev => ({ ...prev, error: error.message }));
    });
    
    // Cleanup
    return () => {
      client.disconnect();
    };
  }, [token]);
  
  const sendMessage = useCallback((text, options = {}) => {
    if (!clientRef.current || !state.connected) {
      throw new Error('Not connected');
    }
    
    return clientRef.current.send({
      type: 'user_input',
      data: {
        text,
        response_to: options.responseTo || null,
        attachments: options.attachments || [],
        ui_references: options.uiReferences || [],
        frontend_actions: options.actions || []
      }
    });
  }, [state.connected]);
  
  const uploadFile = useCallback(async (file) => {
    // Upload file to storage first
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });
    
    const { file_id, upload_url } = await response.json();
    
    // Send message with file attachment
    return sendMessage('', {
      attachments: [{
        type: 'file',
        file_id,
        filename: file.name,
        mime_type: file.type,
        size_bytes: file.size,
        upload_url
      }]
    });
  }, [sendMessage, token]);
  
  const referenceSlideElement = useCallback((slideId, elementId, text) => {
    const element = document.querySelector(`[data-slide-id="${slideId}"] [data-element-id="${elementId}"]`);
    
    if (!element) {
      throw new Error('Element not found');
    }
    
    return sendMessage(text, {
      uiReferences: [{
        reference_type: 'element',
        slide_id: slideId,
        element_id: elementId,
        css_selector: `#${elementId}`,
        html_context: element.outerHTML
      }]
    });
  }, [sendMessage]);
  
  return {
    ...state,
    sendMessage,
    uploadFile,
    referenceSlideElement
  };
}
```

### Vue.js Integration Example

```javascript
// composables/useDeckster.js
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import { DecksterClient } from '../lib/websocket-client';

export function useDeckster(token) {
  const client = ref(null);
  const state = reactive({
    connected: false,
    authenticated: false,
    sessionId: null,
    slides: [],
    chatMessages: [],
    progress: null,
    error: null
  });
  
  const connect = async () => {
    client.value = new DecksterClient();
    
    // Setup event handlers
    client.value.on('connected', () => {
      state.connected = true;
    });
    
    client.value.on('authenticated', (message) => {
      state.authenticated = true;
      state.sessionId = message.session_id;
    });
    
    client.value.on('director_message', (message) => {
      const { data } = message;
      
      if (data.chat_data) {
        state.chatMessages.push({
          id: message.message_id,
          timestamp: message.timestamp,
          ...data.chat_data
        });
      }
      
      if (data.slide_data?.slides) {
        state.slides = data.slide_data.slides;
      }
      
      if (data.chat_data?.progress) {
        state.progress = data.chat_data.progress;
      }
    });
    
    client.value.on('error', (error) => {
      state.error = error.message;
    });
    
    try {
      await client.value.connect(token.value);
    } catch (error) {
      state.error = error.message;
    }
  };
  
  const sendMessage = (text, options = {}) => {
    if (!client.value || !state.connected) {
      throw new Error('Not connected');
    }
    
    return client.value.send({
      type: 'user_input',
      data: {
        text,
        response_to: options.responseTo || null,
        attachments: options.attachments || [],
        ui_references: options.uiReferences || [],
        frontend_actions: options.actions || []
      }
    });
  };
  
  onMounted(() => {
    if (token.value) {
      connect();
    }
  });
  
  onUnmounted(() => {
    if (client.value) {
      client.value.disconnect();
    }
  });
  
  return {
    state,
    sendMessage
  };
}
```

## Best Practices

### 1. Connection Management
- Always implement automatic reconnection with exponential backoff
- Store session IDs for recovery after disconnection
- Use heartbeat/ping messages to detect connection health
- Handle token expiry gracefully with refresh logic

### 2. Message Handling
- Validate all incoming messages before processing
- Use message IDs for request-response correlation
- Implement timeout for message responses
- Queue messages when disconnected for later sending

### 3. Error Handling
- Categorize errors for appropriate handling
- Provide user-friendly error messages
- Implement retry logic for transient failures
- Log errors for debugging and monitoring

### 4. UI Updates
- Use optimistic updates for better perceived performance
- Implement proper loading states
- Handle partial updates gracefully
- Debounce rapid user inputs

### 5. Security
- Never expose JWT tokens in URLs or logs
- Validate all user inputs before sending
- Implement rate limiting on the client side
- Use secure WebSocket connections (WSS)

### 6. Performance
- Batch multiple updates when possible
- Implement virtual scrolling for large slide lists
- Lazy load slide assets
- Use WebWorkers for heavy processing

### 7. Testing
- Mock WebSocket connections for unit tests
- Test reconnection scenarios
- Simulate various error conditions
- Test with poor network conditions

## Troubleshooting

### Common Issues and Solutions

1. **Connection Fails Immediately**
   - Check if token is valid and not expired
   - Verify WebSocket URL is correct
   - Ensure WSS is used for secure connections
   - Check browser console for CORS errors

2. **Messages Not Being Received**
   - Verify message handler is properly registered
   - Check if session ID is included in messages
   - Ensure WebSocket state is OPEN before sending
   - Look for parsing errors in message handling

3. **Reconnection Loop**
   - Implement maximum reconnection attempts
   - Check if authentication is failing
   - Verify server-side session handling
   - Look for rate limiting issues

4. **UI Not Updating**
   - Check if state updates are properly triggered
   - Verify event listeners are correctly set up
   - Ensure component re-rendering is working
   - Look for errors in update handlers

This guide provides a comprehensive foundation for integrating with the Deckster.xyz WebSocket API. Follow these patterns and best practices to build a robust, real-time presentation generation experience.