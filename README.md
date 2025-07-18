# Deckster - AI-Powered Presentation Assistant

Deckster is an intelligent presentation generation platform that uses AI agents to create compelling, professional presentations through natural conversation.

## Features (Phase 1)

- **Conversational Interface**: Natural dialogue-based presentation scoping
- **Intent-Based Routing**: Intelligent understanding of user requests
- **Flexible Workflow**: Non-linear conversation flow with state management
- **Real-time Communication**: WebSocket-based API for instant responses
- **Session Management**: Persistent conversation context

## Quick Start

### Prerequisites

- Python 3.11.9
- Supabase account (REQUIRED - Get free account at https://supabase.com)
- At least one AI API key (Google AI, OpenAI, or Anthropic)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/deckster.git
cd deckster
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Supabase:
   - Create a free account at https://supabase.com
   - Create a new project
   - Go to Settings > API
   - Copy your Project URL and anon/public key

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your Supabase credentials:
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=your-anon-key-here
```

6. Run the application:
```bash
uvicorn main:app --reload --port 8000
```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Redis
REDIS_URL=redis://localhost:6379

# AI Services
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...  # Optional fallback

# Logging (Optional)
LOGFIRE_TOKEN=your-token
```

## API Usage

### WebSocket Connection

Connect to the WebSocket endpoint with a session ID:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?session_id=your-session-id');

ws.onopen = () => {
  // Send initial message
  ws.send(JSON.stringify({
    type: 'user_message',
    content: 'I need a presentation about AI'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

### Message Types

- `user_message`: User input
- `agent_message`: AI responses
- `clarifying_questions`: Questions from the AI
- `confirmation_plan`: Presentation plan for approval
- `strawman`: Initial presentation structure

## Project Structure

```
deckster/
├── config/           # Configuration files
├── src/
│   ├── agents/      # AI agent implementations
│   ├── handlers/    # WebSocket handlers
│   ├── models/      # Data models
│   ├── storage/     # Database interfaces
│   ├── utils/       # Utilities
│   └── workflows/   # State machine logic
├── main.py          # Application entry point
└── requirements.txt # Dependencies
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

This project uses standard Python conventions. Please ensure your code follows PEP 8 guidelines.

## Deployment

The application is configured for deployment on Railway. See `railway.json` for configuration details.

## Phase 1 Scope

This release includes core conversational functionality:
- Intent-based message routing
- Dynamic state management
- WebSocket API
- Session persistence
- Basic presentation structure generation

Future phases will add:
- Multi-agent orchestration
- Visual content generation
- Export functionality
- Advanced customization options

## Contributing

Please read our contributing guidelines before submitting pull requests.

## License

[License Type] - see LICENSE file for details