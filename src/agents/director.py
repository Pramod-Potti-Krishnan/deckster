"""
Director Agent for managing presentation creation workflow.
"""
import os
import json
from typing import Union
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.providers.google import GoogleProvider
from src.models.agents import (
    StateContext, ClarifyingQuestions, ConfirmationPlan, 
    PresentationStrawman, Slide
)
from src.utils.logger import setup_logger
from src.utils.logfire_config import instrument_agents
from src.utils.context_builder import ContextBuilder
from src.utils.token_tracker import TokenTracker
from src.utils.asset_formatter import AssetFormatter

logger = setup_logger(__name__)


class DirectorAgent:
    """Main agent for handling presentation creation states."""
    
    def __init__(self):
        """Initialize state-specific agents with embedded modular prompts."""
        # Instrument agents for token tracking
        instrument_agents()
        
        # Get settings to check which AI service is available
        from config.settings import get_settings
        settings = get_settings()
        
        # Determine which model to use
        if settings.GOOGLE_API_KEY:
            provider = GoogleProvider(api_key=settings.GOOGLE_API_KEY)
            # Use GoogleModel with explicit settings for better control
            model = GoogleModel('gemini-2.5-flash', provider=provider)
            model_turbo = GoogleModel('gemini-2.5-pro', provider=provider)
        elif settings.OPENAI_API_KEY:
            model = 'openai:gpt-4'
            model_turbo = 'openai:gpt-4-turbo'
        elif settings.ANTHROPIC_API_KEY:
            model = 'anthropic:claude-3-sonnet-20240229'
            model_turbo = 'anthropic:claude-3-opus-20240229'
        else:
            raise ValueError(
                "No AI API key configured. Please set GOOGLE_API_KEY, OPENAI_API_KEY, or "
                "ANTHROPIC_API_KEY in your .env file."
            )
        
        # Initialize agents with embedded modular prompts
        logger.info("DirectorAgent initializing with embedded modular prompts")
        self._init_agents_with_embedded_prompts(model, model_turbo)
        
        # Initialize context builder and token tracker
        self.context_builder = ContextBuilder()
        self.token_tracker = TokenTracker()
        
        logger.info(f"DirectorAgent initialized with {type(model).__name__ if hasattr(model, '__class__') else model} model")
    
    def _load_modular_prompt(self, state: str) -> str:
        """Load and combine base prompt with state-specific prompt."""
        prompt_dir = os.path.join(os.path.dirname(__file__), '../../config/prompts/modular')
        
        # Load base prompt
        base_path = os.path.join(prompt_dir, 'base_prompt.md')
        with open(base_path, 'r') as f:
            base_prompt = f.read()
        
        # Load state-specific prompt
        state_prompt_map = {
            'PROVIDE_GREETING': 'provide_greeting.md',
            'ASK_CLARIFYING_QUESTIONS': 'ask_clarifying_questions.md',
            'CREATE_CONFIRMATION_PLAN': 'create_confirmation_plan.md',
            'GENERATE_STRAWMAN': 'generate_strawman.md',
            'REFINE_STRAWMAN': 'refine_strawman.md'
        }
        
        state_file = state_prompt_map.get(state)
        if not state_file:
            raise ValueError(f"Unknown state for prompt loading: {state}")
        
        state_path = os.path.join(prompt_dir, state_file)
        with open(state_path, 'r') as f:
            state_prompt = f.read()
        
        # Combine prompts
        return f"{base_prompt}\n\n{state_prompt}"
    
    def _init_agents_with_embedded_prompts(self, model, model_turbo):
        """Initialize agents with embedded modular prompts."""
        # Load state-specific combined prompts (base + state instructions)
        greeting_prompt = self._load_modular_prompt("PROVIDE_GREETING")
        questions_prompt = self._load_modular_prompt("ASK_CLARIFYING_QUESTIONS")
        plan_prompt = self._load_modular_prompt("CREATE_CONFIRMATION_PLAN")
        strawman_prompt = self._load_modular_prompt("GENERATE_STRAWMAN")
        refine_prompt = self._load_modular_prompt("REFINE_STRAWMAN")
        
        # Store system prompt tokens for each state (for tracking)
        self.state_prompt_tokens = {
            "PROVIDE_GREETING": len(greeting_prompt) // 4,
            "ASK_CLARIFYING_QUESTIONS": len(questions_prompt) // 4,
            "CREATE_CONFIRMATION_PLAN": len(plan_prompt) // 4,
            "GENERATE_STRAWMAN": len(strawman_prompt) // 4,
            "REFINE_STRAWMAN": len(refine_prompt) // 4
        }
        
        # Initialize greeting agent
        self.greeting_agent = Agent(
            model=model,
            output_type=str,
            system_prompt=greeting_prompt,
            retries=2,
            name="director_greeting"
        )
        
        # Initialize questions agent
        self.questions_agent = Agent(
            model=model,
            output_type=ClarifyingQuestions,
            system_prompt=questions_prompt,
            retries=2,
            name="director_questions"
        )
        
        # Initialize plan agent
        self.plan_agent = Agent(
            model=model,
            output_type=ConfirmationPlan,
            system_prompt=plan_prompt,
            retries=2,
            name="director_plan"
        )
        
        # Initialize strawman agent
        self.strawman_agent = Agent(
            model=model_turbo,
            output_type=PresentationStrawman,
            system_prompt=strawman_prompt,
            retries=2,
            name="director_strawman"
        )
        
        # Initialize refine strawman agent (NEW)
        self.refine_strawman_agent = Agent(
            model=model_turbo,
            output_type=PresentationStrawman,
            system_prompt=refine_prompt,
            retries=2,
            name="director_refine_strawman"
        )
    
    async def process(self, state_context: StateContext) -> Union[str, ClarifyingQuestions, 
                                                                   ConfirmationPlan, PresentationStrawman]:
        """
        Process based on current state following PydanticAI best practices.
        
        Args:
            state_context: The current state context
            
        Returns:
            Response appropriate for the current state
        """
        try:
            session_id = state_context.session_data.get("id", "unknown")
            
            # Build context for the user prompt (system prompts are already embedded in agents)
            context, user_prompt = self.context_builder.build_context(
                state=state_context.current_state,
                session_data={
                    "id": session_id,
                    "user_initial_request": state_context.session_data.get("user_initial_request"),
                    "clarifying_answers": state_context.session_data.get("clarifying_answers"),
                    "conversation_history": state_context.conversation_history
                },
                user_intent=state_context.user_intent.dict() if hasattr(state_context, 'user_intent') and state_context.user_intent else None
            )
            
            # Track token usage
            user_tokens = len(user_prompt) // 4
            system_tokens = self.state_prompt_tokens.get(state_context.current_state, 0)
            
            await self.token_tracker.track_modular(
                session_id,
                state_context.current_state,
                user_tokens,
                system_tokens
            )
            
            logger.info(
                f"Processing - State: {state_context.current_state}, "
                f"User Tokens: {user_tokens}, System Tokens: {system_tokens}, "
                f"Total: {user_tokens + system_tokens}"
            )
            
            # Route to appropriate agent based on state
            if state_context.current_state == "PROVIDE_GREETING":
                result = await self.greeting_agent.run(
                    user_prompt,
                    model_settings=ModelSettings(temperature=0.7, max_tokens=500)
                )
                response = result.data  # Simple string
                logger.info("Generated greeting")
                
            elif state_context.current_state == "ASK_CLARIFYING_QUESTIONS":
                result = await self.questions_agent.run(
                    user_prompt,
                    model_settings=ModelSettings(temperature=0.5, max_tokens=1000)
                )
                response = result.data  # ClarifyingQuestions object
                logger.info(f"Generated {len(response.questions)} clarifying questions")
                
            elif state_context.current_state == "CREATE_CONFIRMATION_PLAN":
                result = await self.plan_agent.run(
                    user_prompt,
                    model_settings=ModelSettings(temperature=0.3, max_tokens=2000)
                )
                response = result.data  # ConfirmationPlan object
                logger.info(f"Generated confirmation plan with {response.proposed_slide_count} slides")
                
            elif state_context.current_state == "GENERATE_STRAWMAN":
                logger.info("Generating strawman presentation")
                result = await self.strawman_agent.run(
                    user_prompt,
                    model_settings=ModelSettings(temperature=0.4, max_tokens=8000)
                )
                response = result.data  # PresentationStrawman object
                logger.info(f"Generated strawman with {len(response.slides)} slides")
                logger.debug(f"First slide: {response.slides[0].slide_id if response.slides else 'No slides'}")
                
                # Post-process to ensure asset fields are in correct format
                response = AssetFormatter.format_strawman(response)
                logger.info("Applied asset field formatting to strawman")
                
            elif state_context.current_state == "REFINE_STRAWMAN":
                logger.info("Refining strawman presentation")
                result = await self.refine_strawman_agent.run(
                    user_prompt,
                    model_settings=ModelSettings(temperature=0.4, max_tokens=8000)
                )
                response = result.data  # PresentationStrawman object
                logger.info(f"Refined strawman with {len(response.slides)} slides")
                
                # Post-process to ensure asset fields are in correct format
                response = AssetFormatter.format_strawman(response)
                logger.info("Applied asset field formatting to refined strawman")
                
            else:
                raise ValueError(f"Unknown state: {state_context.current_state}")
            
            return response
                
        except ModelHTTPError as e:
            logger.error(f"API error in state {state_context.current_state}: {e}")
            raise
        except Exception as e:
            error_msg = str(e)
            # Handle Gemini-specific errors
            if "MALFORMED_FUNCTION_CALL" in error_msg:
                logger.error(f"Gemini function call error in state {state_context.current_state}. This may be due to complex output structure.")
                logger.error(f"Full error: {error_msg}")
            elif "MAX_TOKENS" in error_msg:
                logger.error(f"Token limit exceeded in state {state_context.current_state}. Consider increasing max_tokens.")
            elif "Connection error" in error_msg:
                logger.error(f"Connection error in state {state_context.current_state} - Please check your API key is set in .env file")
            else:
                logger.error(f"Error processing state {state_context.current_state}: {error_msg}")
            raise
    
    def get_token_report(self, session_id: str) -> dict:
        """Get token usage report for a specific session."""
        return self.token_tracker.get_savings_report(session_id)
    
    def print_token_report(self, session_id: str) -> None:
        """Print formatted token usage report for a session."""
        self.token_tracker.print_session_report(session_id)
    
    def get_aggregate_token_report(self) -> dict:
        """Get aggregate token usage report across all sessions."""
        return self.token_tracker.get_aggregate_report()
    
    def print_aggregate_token_report(self) -> None:
        """Print formatted aggregate token usage report."""
        self.token_tracker.print_aggregate_report()