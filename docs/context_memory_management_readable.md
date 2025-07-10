# Context and Memory Management in Deckster - Readable Summary

## Overview

This document explains how Deckster manages context and memory as conversations progress through different phases. The system maintains conversation coherence while guiding users through a structured workflow for creating presentations.

## How Context Flows Through Conversation Phases

### The Context Package

Every time the AI processes a user message, it receives a "context package" containing:

1. **Current State** - Where we are in the workflow (greeting, questions, planning, etc.)
2. **User Intent** - What the user is trying to do (provide info, answer questions, give feedback, etc.)
3. **Conversation History** - Everything said so far by both user and assistant
4. **Session Data** - Structured information collected at each phase

### Phase-by-Phase Context Flow

#### Phase 1: Initial Greeting
- **Context Received**: Empty (first interaction)
- **What Happens**: AI provides a warm greeting
- **Context Stored**: The greeting is added to history

#### Phase 2: Topic Collection
- **Context Received**: Greeting + user's topic
- **What Happens**: AI understands the presentation topic
- **Context Stored**: Topic saved as "user_initial_request"

#### Phase 3: Clarifying Questions
- **Context Received**: 
  - Full conversation so far
  - User's initial topic
- **What Happens**: AI asks 3-5 targeted questions
- **Context Stored**: Questions added to history

#### Phase 4: Creating Confirmation Plan
- **Context Received**:
  - Complete conversation history
  - Initial topic + all clarifying answers
- **What Happens**: AI creates a presentation plan
- **Context Stored**: Plan saved in session data

#### Phase 5: Generating Presentation
- **Context Received**:
  - Everything from before
  - The confirmed plan
- **What Happens**: AI generates full presentation content
- **Context Stored**: Presentation saved as "strawman"

#### Phase 6: Refinement
- **Context Received**:
  - Complete history
  - Current presentation
  - User's refinement feedback
- **What Happens**: AI updates specific parts
- **Context Stored**: Updates tracked in history

## How Context Grows Over Time

### Conversation Example

1. **Start**: Context = Empty
2. **After Greeting**: Context = 50 tokens
3. **After Topic**: Context = 80 tokens
4. **After Questions**: Context = 280 tokens
5. **After Answers**: Context = 430 tokens
6. **After Plan**: Context = 730 tokens
7. **After Presentation**: Context = 2,830 tokens
8. **After Refinements**: Context = 3,500+ tokens

### What's in the Context at Each Stage

The system sends **everything** at each step:
- All previous messages
- All collected data
- All generated content

This ensures the AI never "forgets" what was discussed but leads to exponentially growing context.

## Memory Persistence

### What Gets Remembered

1. **Every Message** - Both user inputs and AI responses
2. **User Intent** - Why the user said what they said
3. **Structured Data** - Topic, answers, plans, presentations
4. **State Transitions** - How the conversation progressed

### How It's Stored

- **Conversation History**: Array of all messages with roles
- **Session Data**: Dictionary with specific fields:
  - `user_initial_request`: Original topic
  - `clarifying_answers`: Responses to questions
  - `confirmation_plan`: Agreed presentation structure
  - `presentation_strawman`: Generated content

## Storage Implementation: PostgreSQL via Supabase

### Database Architecture

All conversation history and session data is stored in **PostgreSQL tables** through Supabase (a hosted PostgreSQL service with additional features).

### Primary Storage Table: `sessions`

The main table stores all session information with the following structure:

- **id**: Unique session identifier (text, primary key)
- **user_id**: Links sessions to authenticated users
- **conversation_history**: JSONB array containing the full conversation
- **current_state**: JSONB tracking the workflow state
- **created_at**: When the session started
- **updated_at**: Last modification time
- **expires_at**: Auto-cleanup timestamp
- **metadata**: Additional session information

### Conversation History Structure

Each message in the conversation history is stored as a JSONB object:

```
{
  'role': 'user' or 'assistant',
  'content': The actual message (text or structured data),
  'intent': User's classified intent (for user messages),
  'state': Current workflow state (for assistant messages),
  'timestamp': When the message was sent
}
```

### Additional Storage Tables

- **presentations**: Stores generated presentations with vector embeddings
- **visual_assets**: Images and graphics for presentations
- **agent_outputs**: All AI responses for debugging and analytics

### Storage Flow

1. **WebSocket Connection**: Established with session ID
2. **Session Lookup**: SessionManager checks Supabase for existing session
3. **Session Creation**: If new, creates in both local cache and database
4. **Real-time Updates**: Each message immediately persisted to PostgreSQL
5. **State Sync**: Workflow transitions saved instantly
6. **Cache Optimization**: Local cache reduces database queries

### Security Features

- **Row Level Security (RLS)**: Users can only access their own sessions
- **Authentication**: Handled via Supabase Auth
- **Automatic Cleanup**: Expired sessions removed automatically
- **Data Isolation**: Complete separation between users

### Performance Optimizations

- **Indexes**: On user_id, expires_at, and created_at for fast queries
- **Vector Search**: Using pgvector extension for similarity searches
- **Local Caching**: SessionManager maintains in-memory cache
- **Async Operations**: All database operations are non-blocking

### No Redis Usage

While the codebase includes Redis documentation, the current implementation uses only PostgreSQL/Supabase for all storage needs. Redis may be considered for future performance optimizations.

## Key Design Principles

### 1. Full Context Preservation
The AI always receives complete conversation history to maintain coherence. Nothing is filtered or removed.

### 2. Structured + Unstructured Mix
- **Structured**: Specific data fields for each workflow phase
- **Unstructured**: Natural conversation flow preserved

### 3. Intent-Aware Processing
Every user message is classified by intent (answering, confirming, refining, etc.) to help the AI understand context beyond just the words.

### 4. State-Specific Behavior
While all context is available, the AI's behavior changes based on the current state - asking questions when needed, generating content when appropriate.

## Current Limitations

### 1. Exponential Growth
Context size doubles or triples with each phase, potentially hitting token limits in long conversations.

### 2. No Summarization
Early conversation details remain even when no longer relevant to current tasks.

### 3. Redundant Storage
Same information exists in multiple places (history and session data).

### 4. All-or-Nothing Approach
Every state gets all context, even if it only needs specific parts.

## Future Improvements Needed

### 1. Smart Context Selection
Only send relevant context for each state:
- Greeting phase needs no history
- Refinement phase needs current content + feedback, not early chat

### 2. Progressive Summarization
After major milestones, compress earlier conversation into key points.

### 3. Sliding Windows
Keep only recent messages plus critical data, not entire history.

### 4. Token Budgeting
Monitor context size and gracefully degrade when approaching limits.

## Conclusion

The current system prioritizes never losing context over efficiency. While this ensures coherent conversations, it creates scalability challenges. The AI receives increasingly large context packages that contain much redundant or outdated information.

Future versions should implement smarter context management that maintains coherence while reducing token usage by 60-80% through selective inclusion and summarization strategies.