"""
Session models for Deckster.
"""
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class Session(BaseModel):
    """Session model matching Supabase schema."""
    id: str
    user_id: str  # Required field for user identification
    current_state: Literal[
        "PROVIDE_GREETING", 
        "ASK_CLARIFYING_QUESTIONS", 
        "CREATE_CONFIRMATION_PLAN", 
        "GENERATE_STRAWMAN", 
        "REFINE_STRAWMAN"
    ] = "PROVIDE_GREETING"
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    user_initial_request: Optional[str] = None
    clarifying_answers: Optional[Dict[str, str]] = None
    confirmation_plan: Optional[Dict[str, Any]] = None
    presentation_strawman: Optional[Dict[str, Any]] = None
    refinement_feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)