"""
Prompt Manager for Modular Prompt System
Handles loading and caching of modular prompts with fallback support.
"""
import os
from typing import Dict, Optional
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PromptManager:
    """Manages loading and caching of modular prompts"""
    
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._base_path = Path(__file__).parent.parent.parent / "config/prompts"
        self._modular_path = self._base_path / "modular"
        self._fallback_path = self._base_path / "director_prompt.md"
        
    def get_modular_prompt(self, state: str) -> str:
        """Get the complete prompt for a given state"""
        cache_key = f"modular_{state}"
        
        if cache_key in self._cache:
            logger.debug(f"Using cached prompt for state: {state}")
            return self._cache[cache_key]
        
        try:
            # Load base prompt
            base = self._load_file("base_prompt.md")
            
            # Map state names to file names
            state_file_map = {
                "PROVIDE_GREETING": "provide_greeting.md",
                "ASK_CLARIFYING_QUESTIONS": "ask_clarifying_questions.md",
                "CREATE_CONFIRMATION_PLAN": "create_confirmation_plan.md",
                "GENERATE_STRAWMAN": "generate_strawman.md",
                "REFINE_STRAWMAN": "refine_strawman.md"
            }
            
            state_file = state_file_map.get(state)
            if not state_file:
                raise ValueError(f"Unknown state: {state}")
            
            # Load state-specific prompt
            state_prompt = self._load_file(state_file)
            
            # Combine prompts
            combined = f"{base}\n\n{state_prompt}"
            
            # Cache the result
            self._cache[cache_key] = combined
            logger.info(f"Loaded modular prompt for state: {state} ({len(combined)} chars)")
            
            return combined
            
        except Exception as e:
            logger.error(f"Failed to load modular prompt for {state}: {e}")
            return self._get_fallback_prompt()
    
    def _load_file(self, filename: str) -> str:
        """Load a prompt file from the modular directory"""
        file_path = self._modular_path / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    
    def _get_fallback_prompt(self) -> str:
        """Get the monolithic fallback prompt"""
        if "fallback" not in self._cache:
            try:
                with open(self._fallback_path, 'r', encoding='utf-8') as f:
                    self._cache["fallback"] = f.read()
            except Exception as e:
                logger.error(f"Failed to load fallback prompt: {e}")
                # Return minimal fallback
                return "You are Deckster, an AI presentation assistant."
        
        return self._cache["fallback"]
    
    def clear_cache(self):
        """Clear the prompt cache (useful for development)"""
        self._cache.clear()
        logger.info("Prompt cache cleared")