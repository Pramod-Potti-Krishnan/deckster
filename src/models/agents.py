"""
Agent-specific models for Deckster.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class UserIntent(BaseModel):
    """Classified user intent from router - directional intents that imply next state."""
    intent_type: Literal[
        "Submit_Initial_Topic",           # → ASK_CLARIFYING_QUESTIONS
        "Submit_Clarification_Answers",   # → CREATE_CONFIRMATION_PLAN
        "Accept_Plan",                    # → GENERATE_STRAWMAN
        "Reject_Plan",                    # → CREATE_CONFIRMATION_PLAN (loop)
        "Accept_Strawman",                # → END/Complete
        "Submit_Refinement_Request",      # → REFINE_STRAWMAN
        "Change_Topic",                   # → ASK_CLARIFYING_QUESTIONS (reset)
        "Change_Parameter",               # → CREATE_CONFIRMATION_PLAN (regen)
        "Ask_Help_Or_Question"            # → No state change
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_info: Dict[str, Any] = Field(default_factory=dict)


class StateContext(BaseModel):
    """Context for state-driven agent processing."""
    current_state: Literal[
        "PROVIDE_GREETING", 
        "ASK_CLARIFYING_QUESTIONS", 
        "CREATE_CONFIRMATION_PLAN", 
        "GENERATE_STRAWMAN", 
        "REFINE_STRAWMAN"
    ]
    user_intent: Optional[UserIntent] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    session_data: Dict[str, Any] = Field(default_factory=dict)


class ClarifyingQuestions(BaseModel):
    """Output for ASK_CLARIFYING_QUESTIONS state."""
    questions: List[str] = Field(min_items=3, max_items=5)


class ConfirmationPlan(BaseModel):
    """Output for CREATE_CONFIRMATION_PLAN state."""
    summary_of_user_request: str
    key_assumptions: List[str]
    proposed_slide_count: int = Field(ge=2, le=30)  # Allow as few as 2 slides for short presentations


class Slide(BaseModel):
    """Simplified slide model focused on content guidance."""
    slide_number: int
    slide_id: str = Field(description="Unique identifier like 'slide_001'")
    title: str
    
    # Slide type classification
    slide_type: Literal[
        "title_slide",
        "section_divider", 
        "content_heavy",
        "visual_heavy",
        "data_driven",
        "diagram_focused",
        "mixed_content",
        "conclusion_slide"
    ]
    
    # Core content
    narrative: str = Field(description="The story or key message of this slide")
    key_points: List[str]
    
    # Open-ended guidance for future agents
    analytics_needed: Optional[str] = Field(
        default=None, 
        description="Description of any data, charts, or analytics for this slide"
    )
    visuals_needed: Optional[str] = Field(
        default=None, 
        description="Description of images, icons, or visual elements that would help"
    )
    diagrams_needed: Optional[str] = Field(
        default=None, 
        description="Description of any process flows, hierarchies, or relationships to visualize"
    )
    structure_preference: Optional[str] = Field(
        default=None, 
        description="High-level layout preference like 'two-column' or 'visual-centered'"
    )
    
    # Optional
    speaker_notes: Optional[str] = None
    
    # For backward compatibility
    @property
    def visual_suggestions(self) -> Optional[List[str]]:
        """Backward compatible property for visual suggestions."""
        suggestions = []
        if self.visuals_needed:
            suggestions.append(self.visuals_needed)
        if self.analytics_needed:
            suggestions.append(self.analytics_needed)
        if self.diagrams_needed:
            suggestions.append(self.diagrams_needed)
        return suggestions if suggestions else None


class PresentationStrawman(BaseModel):
    """Simplified presentation strawman structure."""
    # Core elements
    main_title: str
    overall_theme: str  # e.g., "Informative and data-driven"
    slides: List[Slide]
    
    # Simplified metadata
    design_suggestions: str = Field(
        description="Overall design theme like 'Modern professional with blue tones'"
    )
    target_audience: str = Field(
        description="Who will be viewing this presentation"
    )
    presentation_duration: int = Field(
        description="Expected duration in minutes"
    )
    
    # Computed properties
    @property
    def total_slides(self) -> int:
        return len(self.slides)