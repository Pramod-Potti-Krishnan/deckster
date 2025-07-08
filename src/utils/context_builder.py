"""
Context builder for LLM prompts.
"""
from typing import List, Dict, Any, Optional
import json
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ContextBuilder:
    """Builds context for LLM calls from conversation history and session data."""
    
    @staticmethod
    def build_conversation_context(
        history: List[Dict[str, Any]], 
        max_messages: int = 10
    ) -> str:
        """
        Build conversation context from history.
        
        Args:
            history: Conversation history
            max_messages: Maximum number of messages to include
            
        Returns:
            Formatted conversation context
        """
        if not history:
            return "No previous conversation history."
        
        # Take the most recent messages
        recent_history = history[-max_messages:]
        
        context_lines = []
        for msg in recent_history:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
            
            context_lines.append(f"{role.upper()}: {content}")
        
        return "\n".join(context_lines)
    
    @staticmethod
    def build_session_context(session_data: Dict[str, Any]) -> str:
        """
        Build context from session data.
        
        Args:
            session_data: Session data dictionary
            
        Returns:
            Formatted session context
        """
        context_parts = []
        
        if session_data.get('user_initial_request'):
            context_parts.append(f"Initial Request: {session_data['user_initial_request']}")
        
        if session_data.get('clarifying_answers'):
            context_parts.append("Clarifying Answers:")
            for key, value in session_data['clarifying_answers'].items():
                context_parts.append(f"  - {key}: {value}")
        
        if session_data.get('confirmation_plan'):
            plan = session_data['confirmation_plan']
            context_parts.append(f"Confirmed Plan: {plan.get('summary_of_user_request', 'N/A')}")
        
        return "\n".join(context_parts) if context_parts else "No session context available."
    
    @staticmethod
    def build_full_context(
        conversation_history: List[Dict[str, Any]],
        session_data: Dict[str, Any],
        current_state: str,
        user_intent: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build complete context for LLM.
        
        Args:
            conversation_history: Full conversation history
            session_data: Session data
            current_state: Current workflow state
            user_intent: Classified user intent (optional)
            
        Returns:
            Complete formatted context
        """
        context_parts = [
            f"Current State: {current_state}",
            "",
            "=== Session Context ===",
            ContextBuilder.build_session_context(session_data),
            "",
            "=== Recent Conversation ===",
            ContextBuilder.build_conversation_context(conversation_history),
        ]
        
        if user_intent:
            context_parts.extend([
                "",
                "=== User Intent ===",
                f"Type: {user_intent.get('intent_type', 'Unknown')}",
                f"Confidence: {user_intent.get('confidence', 0)}",
                f"Extracted Info: {json.dumps(user_intent.get('extracted_info', {}))}"
            ])
        
        return "\n".join(context_parts)