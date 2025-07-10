# Deckster Director Agent Testing Tools

This directory contains testing tools for the Phase 1 Director agent implementation.

## Tools Available

### 1. Automated End-to-End Testing (`test_director_e2e.py`)

Runs predefined conversation scenarios through all Director states automatically.

**Usage:**
```bash
# List available scenarios
python test/test_director_e2e.py --list

# Run all scenarios
python test/test_director_e2e.py

# Run a specific scenario
python test/test_director_e2e.py --scenario executive
```

**Available Scenarios:**
- `default` - AI in Healthcare presentation
- `executive` - Q3 Financial Results for board
- `technical` - Microservices Architecture for engineers
- `educational` - Climate Change for high school students
- `sales` - SaaS Product Launch presentation

### 2. Interactive CLI Testing (`test_director_interactive.py`)

Manual testing tool with a command-line interface for exploring Director capabilities.

**Usage:**
```bash
python test/test_director_interactive.py
```

**Commands:**
- `/help` - Show available commands
- `/state` - Show current state and context
- `/history` - Show conversation history
- `/save` - Save current session to file
- `/load` - Load a saved session
- `/reset` - Reset to initial state
- `/debug` - Toggle debug mode (shows intent classification)
- `/export` - Export generated strawman to JSON
- `/quit` - Exit the tool

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Ensure you have either OpenAI or Anthropic API keys configured.

## Test Scenarios

Test scenarios are defined in `test_scenarios.json`. Each scenario includes:
- Initial topic
- Responses to clarifying questions
- Expected slide count
- Refinement requests

## Tips

- Use the automated tool for regression testing
- Use the interactive tool for exploring new conversation flows
- Save interesting sessions for later analysis
- Export strawman outputs to analyze the JSON structure
- Enable debug mode to see intent classification details