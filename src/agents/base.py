"""
Base agent class for Deckster (simplified for Phase 1).
"""
from typing import Optional
from pydantic import BaseModel
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseAgent:
    """
    Simplified base agent class for Phase 1.
    
    In future phases, this could be enhanced with:
    - Multiple LLM fallbacks
    - Retry logic
    - Caching
    - Metrics tracking
    """
    
    def __init__(self, name: str):
        """
        Initialize base agent.
        
        Args:
            name: Agent name for logging
        """
        self.name = name
        logger.info(f"Initialized {name} agent")
    
    async def log_interaction(self, prompt: str, response: str):
        """
        Log LLM interaction for debugging.
        
        Args:
            prompt: Input prompt
            response: LLM response
        """
        logger.debug(f"{self.name} - Prompt length: {len(prompt)} chars")
        logger.debug(f"{self.name} - Response length: {len(response)} chars")