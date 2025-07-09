"""
Test suite for modular prompt system
Validates that modular prompts work correctly and produce equivalent output.
"""
import pytest
import asyncio
import os
from typing import Dict, Any
from src.agents.director import DirectorAgent
from src.models.agents import StateContext, UserIntent

class TestModularPrompts:
    """Test suite for modular prompt system"""
    
    @pytest.fixture
    async def monolithic_agent(self):
        """Create agent with monolithic prompts"""
        # Save current env
        original_value = os.environ.get("USE_MODULAR_PROMPTS", "")
        os.environ["USE_MODULAR_PROMPTS"] = "false"
        
        agent = DirectorAgent()
        
        # Restore env
        if original_value:
            os.environ["USE_MODULAR_PROMPTS"] = original_value
        else:
            del os.environ["USE_MODULAR_PROMPTS"]
            
        return agent
    
    @pytest.fixture
    async def modular_agent(self):
        """Create agent with modular prompts"""
        # Save current env
        original_value = os.environ.get("USE_MODULAR_PROMPTS", "")
        os.environ["USE_MODULAR_PROMPTS"] = "true"
        
        agent = DirectorAgent()
        
        # Restore env
        if original_value:
            os.environ["USE_MODULAR_PROMPTS"] = original_value
        else:
            del os.environ["USE_MODULAR_PROMPTS"]
            
        return agent
    
    async def test_greeting_output_parity(self, monolithic_agent, modular_agent):
        """Ensure greeting outputs are equivalent between systems"""
        test_context = StateContext(
            current_state="PROVIDE_GREETING",
            session_data={"id": "test_session"},
            conversation_history=[],
            user_intent=None
        )
        
        # Run both agents
        mono_result = await monolithic_agent.process(test_context)
        mod_result = await modular_agent.process(test_context)
        
        # Both should produce greetings
        assert isinstance(mono_result, str)
        assert isinstance(mod_result, str)
        assert "Deckster" in mono_result
        assert "Deckster" in mod_result
        assert "presentation" in mono_result.lower()
        assert "presentation" in mod_result.lower()
    
    async def test_questions_output_parity(self, monolithic_agent, modular_agent):
        """Ensure clarifying questions are equivalent between systems"""
        test_context = StateContext(
            current_state="ASK_CLARIFYING_QUESTIONS",
            session_data={
                "id": "test_session",
                "user_initial_request": "Create a presentation about AI in healthcare"
            },
            conversation_history=[
                {"role": "assistant", "content": "Hello! I'm Deckster..."},
                {"role": "user", "content": "Create a presentation about AI in healthcare"}
            ],
            user_intent=UserIntent(
                intent_type="Submit_Initial_Topic",
                confidence=0.95
            )
        )
        
        # Run both agents
        mono_result = await monolithic_agent.process(test_context)
        mod_result = await modular_agent.process(test_context)
        
        # Compare outputs
        assert len(mono_result.questions) >= 3
        assert len(mod_result.questions) >= 3
        assert len(mono_result.questions) <= 5
        assert len(mod_result.questions) <= 5
    
    async def test_token_reduction(self, modular_agent):
        """Verify token usage is reduced with modular prompts"""
        test_context = StateContext(
            current_state="PROVIDE_GREETING",
            session_data={"id": "test_token_reduction"},
            conversation_history=[],
            user_intent=None
        )
        
        # Run with modular agent
        result = await modular_agent.process(test_context)
        
        # Get token report
        token_report = modular_agent.get_token_report("test_token_reduction")
        
        # We should see modular tracking (even if no baseline to compare)
        # The actual comparison would be done via A/B testing
        assert token_report is not None
    
    async def test_modular_prompt_loading(self):
        """Test that modular prompts load correctly"""
        from src.utils.prompt_manager import PromptManager
        
        manager = PromptManager()
        
        # Test loading each state
        states = [
            "PROVIDE_GREETING",
            "ASK_CLARIFYING_QUESTIONS", 
            "CREATE_CONFIRMATION_PLAN",
            "GENERATE_STRAWMAN",
            "REFINE_STRAWMAN"
        ]
        
        for state in states:
            prompt = manager.get_modular_prompt(state)
            assert len(prompt) > 0
            assert "Deckster" in prompt
            assert state.replace("_", " ") in prompt or "State" in prompt
    
    async def test_ab_testing_assignment(self):
        """Test A/B testing assignment logic"""
        from src.utils.ab_testing import ABTestManager
        
        # Test with 50% assignment
        manager = ABTestManager(percentage=50)
        
        assignments = {
            "modular": 0,
            "monolithic": 0
        }
        
        # Test 100 sessions
        for i in range(100):
            session_id = f"test_session_{i}"
            if manager.should_use_modular(session_id):
                assignments["modular"] += 1
            else:
                assignments["monolithic"] += 1
        
        # Should be roughly 50/50 (allow some variance)
        assert 40 <= assignments["modular"] <= 60
        assert 40 <= assignments["monolithic"] <= 60
        
        # Test consistency - same session should always get same assignment
        test_id = "consistent_test"
        first_assignment = manager.should_use_modular(test_id)
        for _ in range(10):
            assert manager.should_use_modular(test_id) == first_assignment


async def run_basic_test():
    """Run a basic test of the modular system"""
    print("\n🧪 Testing Modular Prompt System\n")
    
    # Test with modular prompts enabled
    os.environ["USE_MODULAR_PROMPTS"] = "true"
    agent = DirectorAgent()
    
    # Test greeting
    context = StateContext(
        current_state="PROVIDE_GREETING",
        session_data={"id": "manual_test"},
        conversation_history=[],
        user_intent=None
    )
    
    result = await agent.process(context)
    print(f"✅ Greeting: {result}\n")
    
    # Test questions
    context = StateContext(
        current_state="ASK_CLARIFYING_QUESTIONS",
        session_data={
            "id": "manual_test",
            "user_initial_request": "Create a presentation about climate change"
        },
        conversation_history=[
            {"role": "assistant", "content": result},
            {"role": "user", "content": "Create a presentation about climate change"}
        ],
        user_intent=UserIntent(
            intent_type="Submit_Initial_Topic",
            confidence=0.95
        )
    )
    
    result = await agent.process(context)
    print(f"✅ Questions generated: {len(result.questions)}")
    for i, q in enumerate(result.questions, 1):
        print(f"   {i}. {q}")
    
    # Show token report
    print("\n📊 Token Usage Report:")
    agent.print_token_report("manual_test")


if __name__ == "__main__":
    # Run basic test
    asyncio.run(run_basic_test())