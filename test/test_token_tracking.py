"""
Test token usage tracking with Logfire.
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logfire_config import configure_logfire, instrument_agents
from src.agents.director import DirectorAgent
from src.models.agents import StateContext
import logfire

async def test_token_tracking():
    """Test that token usage is being tracked."""
    print("Testing token tracking...")
    
    # Configure and instrument
    if not configure_logfire():
        print("❌ Logfire configuration failed")
        return
    
    instrument_agents()
    
    # Create agent and context
    director = DirectorAgent()
    context = StateContext(
        current_state="PROVIDE_GREETING",
        conversation_history=[],
        session_data={}
    )
    
    # Track the operation
    with logfire.span("test_token_tracking") as span:
        # Run agent
        result = await director.process(context)
        
        # Log result
        logfire.info(
            "Director response generated",
            state="PROVIDE_GREETING",
            response_length=len(str(result))
        )
    
    print("✅ Token tracking test completed")
    print("Check Logfire dashboard for:")
    print("- Span named 'test_token_tracking'")
    print("- Token usage attributes (gen_ai.usage.*)")
    print("- Response time metrics")

if __name__ == "__main__":
    asyncio.run(test_token_tracking())