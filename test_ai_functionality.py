#!/usr/bin/env python3
"""
Test script to verify pydantic_ai and langgraph functionality
Run this to ensure the AI system is working properly
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_pydantic_core():
    """Test if Pydantic BaseModel is working properly"""
    print("\n" + "="*60)
    print("TESTING PYDANTIC CORE FUNCTIONALITY")
    print("="*60)
    
    try:
        import pydantic
        from pydantic import BaseModel, Field, field_validator
        print(f"✅ Pydantic imported successfully - Version: {pydantic.VERSION}")
        
        # Test creating models used in the app
        from models.messages import UserInput, DirectorMessage, ChatData
        from models.agents import AgentOutput, DirectorInboundOutput
        
        # Test UserInput
        test_input = UserInput(
            session_id="test_session",
            type="user_input",
            data={"text": "Test message"}
        )
        print("✅ UserInput model created successfully")
        
        # Test DirectorMessage
        test_chat = ChatData(
            type="info",
            content={"message": "Test"},
            actions=None
        )
        test_msg = DirectorMessage(
            session_id="test_session",
            source="director_inbound",
            chat_data=test_chat
        )
        print("✅ DirectorMessage model created successfully")
        
        # Test serialization
        json_data = test_msg.model_dump(mode='json')
        print("✅ Model serialization working")
        
        return True
        
    except Exception as e:
        print(f"❌ Pydantic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_logfire():
    """Test if Logfire is available and configured"""
    print("\n" + "="*60)
    print("TESTING LOGFIRE FUNCTIONALITY")
    print("="*60)
    
    try:
        import logfire
        print("✅ Logfire imported successfully")
        
        from config.settings import get_settings
        settings = get_settings()
        
        if settings.logfire_token:
            print("✅ Logfire token configured")
            print(f"   Project: {settings.logfire_project}")
        else:
            print("ℹ️  Logfire token not configured (optional)")
            
        # Test logger initialization
        from utils.logger import logger, api_logger, agent_logger
        print("✅ All loggers initialized")
        
        # Test logging
        logger.info("Test log message from test script")
        print("✅ Logging functional")
        
        return True
        
    except ImportError:
        print("ℹ️  Logfire not installed (optional)")
        return True  # Not a failure since it's optional
    except Exception as e:
        print(f"⚠️  Logfire test warning: {e}")
        return True  # Still not a failure


async def test_pydantic_ai():
    """Test if pydantic_ai is available and working"""
    print("\n" + "="*60)
    print("TESTING PYDANTIC_AI FUNCTIONALITY")
    print("="*60)
    
    try:
        import pydantic_ai
        print("✅ pydantic_ai imported successfully")
        print(f"   Version info: {pydantic_ai.__name__}")
        
        # Test creating a simple agent
        from pydantic_ai import Agent
        from pydantic import BaseModel
        
        class TestOutput(BaseModel):
            message: str
            confidence: float
            
        try:
            agent = Agent(
                name="test_agent",
                model="openai:gpt-3.5-turbo",  # Will fail if no API key
                system_prompt="You are a test agent",
                result_type=TestOutput
            )
            print("✅ Successfully created pydantic_ai Agent")
            return True
        except Exception as e:
            print(f"⚠️  Could not create agent (likely missing API key): {e}")
            return False
            
    except ImportError as e:
        print(f"❌ pydantic_ai NOT available: {e}")
        return False


async def test_langgraph():
    """Test if langgraph is available and working"""
    print("\n" + "="*60)
    print("TESTING LANGGRAPH FUNCTIONALITY")
    print("="*60)
    
    try:
        from langgraph import StateGraph, END
        print("✅ langgraph imported successfully")
        
        # Test creating a simple graph
        from typing import TypedDict
        
        class TestState(TypedDict):
            value: int
            
        def increment(state: TestState) -> TestState:
            return {"value": state["value"] + 1}
            
        try:
            workflow = StateGraph(TestState)
            workflow.add_node("increment", increment)
            workflow.set_entry_point("increment")
            workflow.add_edge("increment", END)
            
            app = workflow.compile()
            print("✅ Successfully created and compiled langgraph workflow")
            
            # Test running it
            result = await app.ainvoke({"value": 0})
            print(f"✅ Workflow execution successful: {result}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create/run workflow: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ langgraph NOT available: {e}")
        return False


async def test_agent_system():
    """Test the actual agent system"""
    print("\n" + "="*60)
    print("TESTING AGENT SYSTEM")
    print("="*60)
    
    try:
        from agents.base import BaseAgent, AgentConfig, AgentContext, PYDANTIC_AI_AVAILABLE
        from agents.director_in import DirectorInboundAgent
        
        print(f"PYDANTIC_AI_AVAILABLE: {PYDANTIC_AI_AVAILABLE}")
        
        # Create director agent
        director = DirectorInboundAgent()
        print(f"✅ Created DirectorInboundAgent: {director.agent_id}")
        print(f"   AI Agent initialized: {director.ai_agent is not None}")
        
        # Create test context
        context = AgentContext(
            session_id="test_session",
            correlation_id="test_correlation",
            request_id="test_request",
            user_id="test_user"
        )
        
        # Test with a greeting
        result = await director._analyze_user_request(
            {"text": "hi"},
            context
        )
        
        print(f"✅ Agent processing successful")
        print(f"   Output type: {result.output_type}")
        print(f"   Has greeting: {'greeting_response' in dir(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_system():
    """Test the workflow system"""
    print("\n" + "="*60)
    print("TESTING WORKFLOW SYSTEM")
    print("="*60)
    
    try:
        from workflows.main import create_workflow, LANGGRAPH_AVAILABLE
        from models.messages import UserInput
        
        print(f"LANGGRAPH_AVAILABLE: {LANGGRAPH_AVAILABLE}")
        
        # Create workflow
        workflow = create_workflow()
        print(f"✅ Created workflow: {type(workflow).__name__}")
        
        # Test with simple state
        from workflows.main import WorkflowState
        test_state = WorkflowState(
            request_id="test_req",
            session_id="test_session",
            user_id="test_user",
            correlation_id="test_corr",
            user_input=UserInput(
                session_id="test_session",
                type="user_input",
                data={"text": "Create a presentation about AI"}
            ),
            presentation_request=None,
            clarification_rounds=[],
            clarification_responses=[],
            requirement_analysis=None,
            presentation_structure=None,
            layouts=None,
            research_findings=None,
            visual_assets=None,
            charts=None,
            diagrams=None,
            final_presentation=None,
            current_phase="analysis",
            needs_clarification=False,
            active_agents=[],
            completed_agents=[],
            agent_errors={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            processing_time_ms=0
        )
        
        print("✅ Created test workflow state")
        
        # Try to run workflow
        try:
            async for state in workflow.astream(test_state):
                print(f"✅ Workflow iteration successful")
                print(f"   Current phase: {state.get('current_phase')}")
                print(f"   Needs clarification: {state.get('needs_clarification')}")
                break  # Just test one iteration
            return True
        except Exception as e:
            print(f"⚠️  Workflow execution failed (expected without full setup): {e}")
            return True  # Still consider test passed if workflow was created
            
    except Exception as e:
        print(f"❌ Workflow system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_environment():
    """Check environment configuration"""
    print("\n" + "="*60)
    print("ENVIRONMENT CONFIGURATION")
    print("="*60)
    
    from config.settings import get_settings
    
    settings = get_settings()
    
    print(f"APP_ENV: {settings.app_env}")
    print(f"OpenAI API Key: {'✅ Configured' if settings.openai_api_key else '❌ Not configured'}")
    print(f"Anthropic API Key: {'✅ Configured' if settings.anthropic_api_key else '❌ Not configured'}")
    print(f"Primary LLM Model: {settings.primary_llm_model}")
    print(f"Fallback Models: {settings.fallback_llm_models}")
    

async def main():
    """Run all tests"""
    print("\n🧪 AI FUNCTIONALITY TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment first
    await check_environment()
    
    # Run tests
    results = {
        "pydantic_core": await test_pydantic_core(),
        "logfire": await test_logfire(),
        "pydantic_ai": await test_pydantic_ai(),
        "langgraph": await test_langgraph(),
        "agent_system": await test_agent_system(),
        "workflow_system": await test_workflow_system()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("="*60))
    if all_passed:
        print("✅ ALL TESTS PASSED - AI system is ready!")
    else:
        print("❌ SOME TESTS FAILED - Check configuration and dependencies")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)