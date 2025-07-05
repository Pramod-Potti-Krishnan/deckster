#!/usr/bin/env python3
"""
Command-line interface to test the AI backend directly.
Usage: python test_cli_chat.py

This bypasses the WebSocket layer to test agent functionality directly.
"""
import asyncio
import json
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Direct imports to bypass API layer
from src.agents.director_in import DirectorInboundAgent
from src.agents.base import AgentContext
from src.models.messages import UserInput
from src.utils.logger import logger, set_session_id

async def test_agent_directly():
    """Test the AI agent without WebSocket/API layers."""
    print("🤖 Deckster CLI Test Interface")
    print("=" * 50)
    print("Type 'quit' to exit")
    print("Responses will be in raw JSON format")
    print("=" * 50)
    
    # Initialize agent
    print("\n📦 Initializing DirectorInboundAgent...")
    try:
        agent = DirectorInboundAgent()
        print(f"✅ Agent initialized: {agent.agent_id}")
        print(f"   Has AI agent: {agent.ai_agent is not None}")
        
        # Check if we're in mock mode
        if agent.ai_agent is None:
            print("⚠️  WARNING: Agent is in MOCK mode - real AI not available")
        else:
            print("✅ Real AI agent available")
            
    except Exception as e:
        print(f"❌ Failed to initialize agent: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Create test context
    session_id = f"cli_session_{uuid4().hex[:8]}"
    set_session_id(session_id)
    
    context = AgentContext(
        session_id=session_id,
        correlation_id=f"cli_corr_{uuid4().hex[:8]}",
        request_id=f"cli_req_{uuid4().hex[:8]}",
        user_id="cli_test_user"
    )
    
    print(f"\n📝 Session ID: {session_id}")
    print("-" * 50)
    
    while True:
        # Get user input
        try:
            user_text = input("\n👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break
        
        if user_text.lower() == 'quit':
            print("👋 Goodbye!")
            break
        
        if not user_text:
            continue
            
        # Create user input object
        user_input = UserInput(
            type="user_input",
            data={"text": user_text},
            id=f"msg_{uuid4().hex[:8]}",
            timestamp=datetime.utcnow().isoformat(),
            session_id=session_id
        )
        
        # Process through agent
        print("\n🔄 Processing...")
        try:
            # Update context for new request
            context.request_id = f"cli_req_{uuid4().hex[:8]}"
            
            result = await agent.execute(
                action="analyze_request",
                parameters={"user_input": user_input.model_dump(mode='json')},
                context=context
            )
            
            # Display result
            print("\n🤖 Agent Response (JSON):")
            print("-" * 50)
            result_dict = result.model_dump(mode='json')
            print(json.dumps(result_dict, indent=2))
            print("-" * 50)
            
            # Extract human-readable message if available
            if result.output_type == "greeting" and result.greeting_response:
                print(f"\n💬 Message: {result.greeting_response.get('message', 'No message')}")
                suggestions = result.greeting_response.get('suggestions', [])
                if suggestions:
                    print("   Suggestions:")
                    for s in suggestions:
                        print(f"   - {s}")
                        
            elif result.output_type == "clarification" and result.clarification_questions:
                print(f"\n❓ Questions needed:")
                for q in result.clarification_questions:
                    print(f"   - {q.question}")
                    if q.options:
                        print(f"     Options: {', '.join(q.options)}")
                        
            elif result.output_type == "structure":
                print(f"\n📋 Ready to create structure")
                if result.initial_structure:
                    print(f"   Title: {result.initial_structure.get('title', 'Untitled')}")
                    print(f"   Slides: {result.initial_structure.get('estimated_slides', 'Unknown')}")
                    
            elif result.output_type == "error":
                print(f"\n❌ Error occurred: {result.status}")
                
        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            
        # Show agent mode after each interaction
        if agent.ai_agent is None:
            print("\n[Running in MOCK mode]")

if __name__ == "__main__":
    print("Starting CLI test interface...")
    try:
        asyncio.run(test_agent_directly())
    except Exception as e:
        print(f"Failed to start: {e}")
        import traceback
        traceback.print_exc()