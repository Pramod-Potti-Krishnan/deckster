"""
Intent Router for classifying user messages.
"""
import json
from typing import Dict, Any
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.providers.google import GoogleProvider
from src.models.agents import UserIntent
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class IntentRouter:
    """Classifies user intent for natural conversation flow."""
    
    def __init__(self):
        """Initialize the intent router agent."""
        # Get settings to check which AI service is available
        from config.settings import get_settings
        settings = get_settings()
        
        # Determine which model to use
        if settings.GOOGLE_API_KEY:
            provider = GoogleProvider(api_key=settings.GOOGLE_API_KEY)
            model = GoogleModel('gemini-2.5-flash', provider=provider)  # Fast model for routing
        elif settings.OPENAI_API_KEY:
            model = 'openai:gpt-3.5-turbo'  # Faster model for routing
        elif settings.ANTHROPIC_API_KEY:
            model = 'anthropic:claude-3-haiku-20240307'  # Fast Anthropic model
        else:
            raise ValueError(
                "No AI API key configured. Please set GOOGLE_API_KEY, OPENAI_API_KEY, or "
                "ANTHROPIC_API_KEY in your .env file."
            )
        
        self.router_agent = Agent(
            model=model,
            output_type=UserIntent,
            system_prompt=self._get_router_prompt(),
            retries=1,
            name="intent_router"
        )
        logger.info(f"IntentRouter initialized with {type(model).__name__ if hasattr(model, '__class__') else model}")
    
    def _get_router_prompt(self) -> str:
        """Get the system prompt for intent classification."""
        return """You are an expert, low-level "Intent Classification Engine." Your single responsibility is to analyze a user's message in the context of a conversation and classify it into one of the predefined, specific intents. You must be precise and return only the structured JSON output.

You will be given the current state of the conversation and the user's latest message. Your classification MUST be based on this context.

CRITICAL: The following intent types are INVALID and must NEVER be used:
- "Provide_Answer" (old system - DO NOT USE)
- "Request_Refinement" (old system - use "Submit_Refinement_Request" instead)
- "Ask_Question" (old system - use "Ask_Help_Or_Question" instead)

---
**INTENT DEFINITIONS AND RULES**
---

1.  **`Submit_Initial_Topic`**
    * **WHEN TO USE:** When the current state is `PROVIDE_GREETING` and the user is providing their main presentation topic for the very first time.
    * **EXAMPLE:** "I need to make a presentation about the history of artificial intelligence."
    * **DO NOT USE IF:** The user is answering any question.
    * **SPECIAL:** If current_state is "PROVIDE_GREETING", this is almost always the correct intent.

2.  **`Submit_Clarification_Answers`**
    * **WHEN TO USE:** When the current state is `ASK_CLARIFYING_QUESTIONS` and the user provides answers to those questions.
    * **EXAMPLE:** "It's for a university lecture, about 45 minutes long, for an audience of computer science students."
    * **DO NOT USE IF:** The user is just saying "yes" or "no". That is an acceptance or rejection.

3.  **`Accept_Plan`**
    * **WHEN TO USE:** When the current state is `CREATE_CONFIRMATION_PLAN` and the user expresses clear, positive approval of the proposed plan.
    * **EXAMPLE:** "Yes, that looks perfect, go ahead." | "I'm happy with those assumptions." | "Proceed."
    * **DO NOT USE IF:** The user is providing new information.

4.  **`Reject_Plan`**
    * **WHEN TO USE:** When the current state is `CREATE_CONFIRMATION_PLAN` and the user expresses disapproval or wants to change the plan.
    * **EXAMPLE:** "No, that's not quite right." | "Let's change the number of slides."
    * **NOTE:** This intent covers both simple rejections and rejections that include parameter changes.

5.  **`Accept_Strawman`**
    * **WHEN TO USE:** When the current state is `GENERATE_STRAWMAN` or `REFINE_STRAWMAN` and the user expresses final approval of the presentation outline.
    * **EXAMPLE:** "This is great, I'm happy with this version." | "Looks good, we're done."

6.  **`Submit_Refinement_Request`**
    * **WHEN TO USE:** When the current state is `GENERATE_STRAWMAN` or `REFINE_STRAWMAN` and the user wants to make specific changes to the outline.
    * **EXAMPLE:** "Can you make the second slide more data-driven?" | "Combine slides 4 and 5."

7.  **`Change_Topic`**
    * **WHEN TO USE:** At ANY time, if the user clearly wants to abandon the current topic and start over with a new one.
    * **EXAMPLE:** "Actually, forget marketing, let's do a presentation on ancient history instead."
    * **ACTION:** Extract the new topic and set extracted_info to the new topic string

8.  **`Ask_Help_Or_Question`**
    * **WHEN TO USE:** At ANY time, if the user is asking a question about the process, or seems confused.
    * **EXAMPLE:** "How long will this take?" | "What do you mean by 'strawman'?"

**OUTPUT FORMAT**
You must respond with a single JSON object that conforms to the `UserIntent` Pydantic model. Do not include any other text or explanation.

**EXAMPLE INPUT FROM SYSTEM:**
{
  "current_state": "CREATE_CONFIRMATION_PLAN",
  "user_message": "Yes, that plan looks perfect. Please proceed."
}

**YOUR REQUIRED OUTPUT:**
{
  "intent_type": "Accept_Plan",
  "confidence": 0.99,
  "extracted_info": null
}

Note: extracted_info should be null when no extra information needs to be extracted, or a string containing the extracted information (e.g., the new topic for Change_Topic)."""
    
    async def classify(self, user_message: str, context: Dict[str, Any]) -> UserIntent:
        """
        Classify user intent from message and context.
        
        Args:
            user_message: The user's message
            context: Conversation context including current state and history
            
        Returns:
            Classified UserIntent
        """
        try:
            # Build prompt with context - provide structured input format
            prompt = f"""{{
  "current_state": "{context.get('current_state', 'PROVIDE_GREETING')}",
  "user_message": "{user_message}"
}}"""
            
            # Run classification
            result = await self.router_agent.run(
                prompt,
                model_settings=ModelSettings(temperature=0.1, max_tokens=500)  # Increased for Gemini
            )
            
            intent = result.data
            
            logger.info(f"Classified intent: {intent.intent_type} (confidence: {intent.confidence}, extracted_info: {intent.extracted_info})")
            
            return intent
            
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            # Default to Ask_Help_Or_Question on error (safest default)
            return UserIntent(
                intent_type="Ask_Help_Or_Question",
                confidence=0.5,
                extracted_info=None  # Changed to match new type
            )