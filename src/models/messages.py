"""
WebSocket message models for communication between frontend and backend.
Defines all message types according to the communication protocol.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Literal, Union
from datetime import datetime
from uuid import UUID, uuid4


# Base message types
class BaseMessage(BaseModel):
    """Base model for all messages in the system."""
    message_id: str = Field(default_factory=lambda: f"msg_{uuid4().hex[:12]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


# User Input Messages (Section 5.1 & 5.2 from comms_protocol.md)
class UserInput(BaseMessage):
    """Raw user input from frontend."""
    type: Literal["user_input"] = "user_input"
    data: Dict[str, Any]
    
    @field_validator('data')
    def validate_data_structure(cls, v):
        """Ensure required fields are present in data."""
        required_fields = {"text"}
        if not all(field in v for field in required_fields):
            raise ValueError(f"Data must contain fields: {required_fields}")
        
        # Validate text length
        if len(v.get("text", "")) > 5000:
            raise ValueError("Text input cannot exceed 5000 characters")
        
        return v


class UserInputData(BaseModel):
    """Structured data within user input messages."""
    text: str = Field(..., max_length=5000)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    ui_references: List[Dict[str, Any]] = Field(default_factory=list)
    frontend_actions: List[Dict[str, Any]] = Field(default_factory=list)
    response_to: Optional[str] = None  # References previous message_id if responding


# Director Messages (Section 5.3 from comms_protocol.md)
class SlideContent(BaseModel):
    """Content for a single slide."""
    slide_id: str = Field(..., pattern=r"^slide_\d+$")
    slide_number: int = Field(..., ge=1)
    title: str = Field(..., max_length=200)
    subtitle: Optional[str] = Field(None, max_length=300)
    body_content: List[Dict[str, Any]]
    layout_type: Literal["hero", "content", "chart_focused", "comparison", "closing"]
    speaker_notes: Optional[str] = None
    animations: List[Dict[str, Any]] = Field(default_factory=list)
    transitions: Dict[str, Any] = Field(default_factory=dict)


class SlideData(BaseModel):
    """Complete slide data structure."""
    type: Literal["complete", "incremental"] = "complete"
    slides: List[SlideContent]
    presentation_metadata: Optional[Dict[str, Any]] = None


class ChatAction(BaseModel):
    """Interactive action for chat responses."""
    action_id: str
    type: Literal["accept_changes", "provide_feedback", "regenerate", "custom"]
    label: str
    payload: Optional[Dict[str, Any]] = None
    primary: bool = False
    requires_input: bool = False


class ChatData(BaseModel):
    """Chat response data from Director."""
    type: Literal["question", "suggestion", "summary", "error", "info"]
    content: Union[str, Dict[str, Any], List[Dict[str, Any]]]
    actions: Optional[List[ChatAction]] = None
    progress: Optional[Dict[str, Any]] = None
    references: Optional[List[Dict[str, Any]]] = None


class DirectorMessage(BaseMessage):
    """Message from Director agent to frontend."""
    type: Literal["director_message"] = "director_message"
    source: Literal["director_inbound", "director_outbound"]
    slide_data: Optional[SlideData] = None
    chat_data: Optional[ChatData] = None
    
    @field_validator('slide_data', 'chat_data')
    def validate_at_least_one_data(cls, v, info):
        """Ensure at least one of slide_data or chat_data is present."""
        if info.field_name == 'chat_data' and v is None and info.data.get('slide_data') is None:
            raise ValueError("Either slide_data or chat_data must be provided")
        return v


# Specialized Agent Messages (Section 5.4-5.9 from comms_protocol.md)
class AgentMessage(BaseMessage):
    """Base class for specialized agent messages."""
    type: Literal["agent_message"] = "agent_message"
    source: str  # Agent ID
    target: Literal["director", "frontend", "broadcast"]
    data: Dict[str, Any]
    correlation_id: str  # Links related messages
    status: Literal["processing", "completed", "failed"] = "processing"


class UXArchitectOutput(AgentMessage):
    """UX Architect agent output."""
    source: Literal["ux_architect"] = "ux_architect"
    data: Dict[str, Any]  # Contains layout specifications
    
    @field_validator('data')
    def validate_layout_data(cls, v):
        """Validate UX Architect output structure."""
        required_fields = {"layouts", "design_system", "responsive_rules"}
        if not all(field in v for field in required_fields):
            raise ValueError(f"UX Architect data must contain: {required_fields}")
        return v


class ResearcherOutput(AgentMessage):
    """Researcher agent output."""
    source: Literal["researcher"] = "researcher"
    data: Dict[str, Any]  # Contains research findings
    
    @field_validator('data')
    def validate_research_data(cls, v):
        """Validate Researcher output structure."""
        required_fields = {"findings", "sources", "key_insights"}
        if not all(field in v for field in required_fields):
            raise ValueError(f"Researcher data must contain: {required_fields}")
        return v


class VisualDesignerOutput(AgentMessage):
    """Visual Designer agent output."""
    source: Literal["visual_designer"] = "visual_designer"
    data: Dict[str, Any]  # Contains visual asset information
    
    @field_validator('data')
    def validate_visual_data(cls, v):
        """Validate Visual Designer output structure."""
        required_fields = {"asset_type", "url", "metadata"}
        if not all(field in v for field in required_fields):
            raise ValueError(f"Visual Designer data must contain: {required_fields}")
        return v


class DataAnalystOutput(AgentMessage):
    """Data Analyst agent output."""
    source: Literal["data_analyst"] = "data_analyst"
    data: Dict[str, Any]  # Contains chart/visualization data
    
    @field_validator('data')
    def validate_chart_data(cls, v):
        """Validate Data Analyst output structure."""
        required_fields = {"chart_type", "data_points", "config"}
        if not all(field in v for field in required_fields):
            raise ValueError(f"Data Analyst data must contain: {required_fields}")
        return v


class UXAnalystOutput(AgentMessage):
    """UX Analyst agent output."""
    source: Literal["ux_analyst"] = "ux_analyst"
    data: Dict[str, Any]  # Contains diagram specifications
    
    @field_validator('data')
    def validate_diagram_data(cls, v):
        """Validate UX Analyst output structure."""
        required_fields = {"diagram_type", "structure", "styling"}
        if not all(field in v for field in required_fields):
            raise ValueError(f"UX Analyst data must contain: {required_fields}")
        return v


# Frontend Actions (Section 5.10 from comms_protocol.md)
class FrontendAction(BaseMessage):
    """Actions initiated by frontend."""
    type: Literal["frontend_action"] = "frontend_action"
    action: Literal["undo", "redo", "save_draft", "export", "share", "settings"]
    payload: Optional[Dict[str, Any]] = None
    target_slides: Optional[List[str]] = None


# System Messages
class SystemMessage(BaseMessage):
    """System-level messages for errors, status, etc."""
    type: Literal["system"] = "system"
    level: Literal["info", "warning", "error", "debug"]
    code: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None


class ConnectionMessage(BaseModel):
    """WebSocket connection management messages."""
    type: Literal["connection"] = "connection"
    status: Literal["connected", "authenticated", "disconnected", "error"]
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Clarification Models
class ClarificationQuestion(BaseModel):
    """Single clarification question."""
    question_id: str = Field(default_factory=lambda: f"q_{uuid4().hex[:8]}")
    question: str
    question_type: Literal["text", "choice", "multi_choice", "scale"]
    options: Optional[List[str]] = None
    required: bool = True
    context: Optional[str] = None


class ClarificationRound(BaseModel):
    """Set of clarification questions from Director."""
    round_id: str = Field(default_factory=lambda: f"round_{uuid4().hex[:8]}")
    questions: List[ClarificationQuestion]
    context: Optional[str] = None
    max_rounds: int = 3
    current_round: int = 1


class ClarificationResponse(BaseModel):
    """User's response to clarification questions."""
    round_id: str
    responses: Dict[str, Any]  # question_id -> answer
    skipped_questions: List[str] = Field(default_factory=list)


# Presentation Structure Models (for message payloads)
class PresentationMetadata(BaseModel):
    """Metadata about the presentation."""
    title: str
    description: Optional[str] = None
    presentation_type: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    estimated_duration: Optional[int] = None  # in minutes
    tags: List[str] = Field(default_factory=list)


class PresentationStructure(BaseModel):
    """Complete presentation structure."""
    presentation_id: str = Field(default_factory=lambda: f"pres_{uuid4().hex[:12]}")
    metadata: PresentationMetadata
    slides: List[SlideContent]
    theme: Optional[Dict[str, Any]] = None
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Request/Response Models for Director Agent
class PresentationRequest(BaseModel):
    """Initial request to create a presentation."""
    session_id: str
    topic: str
    presentation_type: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    reference_materials: Optional[List[Dict[str, Any]]] = None
    constraints: Optional[Dict[str, Any]] = None


class DirectorResponse(BaseModel):
    """Structured response from Director agent."""
    request_id: str
    status: Literal["clarification_needed", "processing", "completed", "failed"]
    clarification_round: Optional[ClarificationRound] = None
    presentation_structure: Optional[PresentationStructure] = None
    chat_message: Optional[ChatData] = None
    next_steps: Optional[List[str]] = None


# Session Management
class SessionState(BaseModel):
    """Current state of a user session."""
    session_id: str
    user_id: str
    current_phase: Literal["gathering", "clarifying", "generating", "refining", "completed"]
    conversation_history: List[BaseMessage] = Field(default_factory=list)
    presentation_structure: Optional[PresentationStructure] = None
    active_agents: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Validation Helpers
def validate_message(message_dict: Dict[str, Any]) -> BaseMessage:
    """
    Validate and parse a message dictionary into appropriate message type.
    
    Args:
        message_dict: Raw message dictionary
        
    Returns:
        Parsed message object
        
    Raises:
        ValueError: If message type is invalid or structure is incorrect
    """
    message_type = message_dict.get("type")
    
    type_mapping = {
        "user_input": UserInput,
        "director_message": DirectorMessage,
        "agent_message": AgentMessage,
        "frontend_action": FrontendAction,
        "system": SystemMessage,
        "connection": ConnectionMessage
    }
    
    if message_type not in type_mapping:
        raise ValueError(f"Unknown message type: {message_type}")
    
    return type_mapping[message_type](**message_dict)