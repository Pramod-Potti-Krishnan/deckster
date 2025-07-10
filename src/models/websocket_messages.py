"""
WebSocket Streamlined Message Protocol Models

This module defines the new streamlined message types for WebSocket communication.
Each message type has a single responsibility and maps directly to frontend UI components.
"""

from datetime import datetime
from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MessageType(str, Enum):
    """Enum for all message types in the streamlined protocol"""
    CHAT_MESSAGE = "chat_message"
    ACTION_REQUEST = "action_request"
    SLIDE_UPDATE = "slide_update"
    STATUS_UPDATE = "status_update"


class ChatPayload(BaseModel):
    """Payload for chat messages displayed in the chat interface"""
    text: str = Field(..., description="Main message text")
    sub_title: Optional[str] = Field(None, description="Optional subtitle")
    list_items: Optional[List[str]] = Field(None, description="Optional list of items")
    format: Literal["markdown", "plain"] = Field("markdown", description="Text format type")


class Action(BaseModel):
    """Individual action button configuration"""
    label: str = Field(..., description="Button label text")
    value: str = Field(..., description="Action value sent back when clicked")
    primary: bool = Field(False, description="Whether this is the primary action")
    requires_input: bool = Field(False, description="Whether action requires text input")


class ActionPayload(BaseModel):
    """Payload for action request messages"""
    prompt_text: str = Field(..., description="Text prompting user action")
    actions: List[Action] = Field(..., description="List of available actions")


class SlideMetadata(BaseModel):
    """Metadata about the entire presentation"""
    main_title: str = Field(..., description="Main presentation title")
    overall_theme: str = Field(..., description="Overall presentation theme")
    design_suggestions: str = Field(..., description="Design and styling suggestions")
    target_audience: str = Field(..., description="Target audience description")
    presentation_duration: int = Field(..., description="Estimated duration in minutes")


class SlideData(BaseModel):
    """Individual slide data with all planning fields"""
    slide_id: str = Field(..., description="Unique slide identifier")
    slide_number: int = Field(..., description="Slide position in presentation")
    slide_type: str = Field(..., description="Type of slide (title_slide, content_heavy, etc.)")
    title: str = Field(..., description="Slide title")
    narrative: str = Field(..., description="The story or key message of this slide")
    key_points: List[str] = Field(..., description="Key points for the slide")
    analytics_needed: Optional[str] = Field(None, description="Description of data/charts needed")
    visuals_needed: Optional[str] = Field(None, description="Description of images/graphics needed")
    diagrams_needed: Optional[str] = Field(None, description="Description of diagrams/flows needed")
    structure_preference: Optional[str] = Field(None, description="Layout preference for the slide")


class SlideUpdatePayload(BaseModel):
    """Payload for slide update messages"""
    operation: Literal["full_update", "partial_update"] = Field(..., description="Update type")
    metadata: SlideMetadata = Field(..., description="Presentation metadata")
    slides: List[SlideData] = Field(..., description="List of slides to update")
    affected_slides: Optional[List[str]] = Field(None, description="IDs of affected slides for partial updates")


class StatusLevel(str, Enum):
    """Status levels for status updates"""
    IDLE = "idle"
    THINKING = "thinking"
    GENERATING = "generating"
    COMPLETE = "complete"
    ERROR = "error"


class StatusPayload(BaseModel):
    """Payload for status update messages"""
    status: StatusLevel = Field(..., description="Current status level")
    text: str = Field(..., description="Status message text")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    estimated_time: Optional[int] = Field(None, description="Estimated time remaining in seconds")


class BaseMessage(BaseModel):
    """Base message envelope for all message types"""
    message_id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    type: MessageType = Field(..., description="Message type discriminator")
    
    class Config:
        use_enum_values = True


class ChatMessage(BaseMessage):
    """Chat message for conversational content"""
    type: Literal[MessageType.CHAT_MESSAGE] = MessageType.CHAT_MESSAGE
    payload: ChatPayload
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_001",
                "session_id": "session_abc",
                "timestamp": "2024-01-01T10:00:00Z",
                "type": "chat_message",
                "payload": {
                    "text": "Hello! I'm Deckster. What presentation would you like to create?",
                    "format": "markdown"
                }
            }
        }


class ActionRequest(BaseMessage):
    """Action request message for user interactions"""
    type: Literal[MessageType.ACTION_REQUEST] = MessageType.ACTION_REQUEST
    payload: ActionPayload
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_002",
                "session_id": "session_abc",
                "timestamp": "2024-01-01T10:01:00Z",
                "type": "action_request",
                "payload": {
                    "prompt_text": "Does this look correct?",
                    "actions": [
                        {"label": "Accept", "value": "accept_plan", "primary": True},
                        {"label": "Modify", "value": "reject_plan", "primary": False}
                    ]
                }
            }
        }


class SlideUpdate(BaseMessage):
    """Slide update message for presentation content"""
    type: Literal[MessageType.SLIDE_UPDATE] = MessageType.SLIDE_UPDATE
    payload: SlideUpdatePayload
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_003",
                "session_id": "session_abc",
                "timestamp": "2024-01-01T10:02:00Z",
                "type": "slide_update",
                "payload": {
                    "operation": "full_update",
                    "metadata": {
                        "main_title": "AI in Healthcare: Transforming Patient Care",
                        "overall_theme": "Data-driven and persuasive",
                        "design_suggestions": "Modern professional with blue color scheme",
                        "target_audience": "Healthcare executives",
                        "presentation_duration": 15
                    },
                    "slides": [
                        {
                            "slide_id": "slide_001",
                            "slide_number": 1,
                            "slide_type": "title_slide",
                            "title": "AI in Healthcare: Transforming Patient Care",
                            "narrative": "Setting the stage for how AI is revolutionizing healthcare delivery",
                            "key_points": ["Revolutionizing diagnostics", "Improving patient outcomes", "Reducing costs"],
                            "analytics_needed": None,
                            "visuals_needed": "**Goal:** Create an impactful opening visual. **Content:** A modern healthcare facility with AI elements. **Style:** Professional, futuristic, blue tones.",
                            "diagrams_needed": None,
                            "structure_preference": "Full-Bleed Visual"
                        }
                    ]
                }
            }
        }


class StatusUpdate(BaseMessage):
    """Status update message for progress indication"""
    type: Literal[MessageType.STATUS_UPDATE] = MessageType.STATUS_UPDATE
    payload: StatusPayload
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_004",
                "session_id": "session_abc",
                "timestamp": "2024-01-01T10:03:00Z",
                "type": "status_update",
                "payload": {
                    "status": "generating",
                    "text": "Creating your presentation...",
                    "progress": 45,
                    "estimated_time": 10
                }
            }
        }


# Union type for all message types
StreamlinedMessage = Union[ChatMessage, ActionRequest, SlideUpdate, StatusUpdate]


def create_chat_message(
    session_id: str,
    text: str,
    message_id: Optional[str] = None,
    sub_title: Optional[str] = None,
    list_items: Optional[List[str]] = None,
    format: Literal["markdown", "plain"] = "markdown"
) -> ChatMessage:
    """Helper function to create a chat message"""
    import uuid
    return ChatMessage(
        message_id=message_id or f"msg_{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        payload=ChatPayload(
            text=text,
            sub_title=sub_title,
            list_items=list_items,
            format=format
        )
    )


def create_action_request(
    session_id: str,
    prompt_text: str,
    actions: List[Dict[str, Any]],
    message_id: Optional[str] = None
) -> ActionRequest:
    """Helper function to create an action request"""
    import uuid
    return ActionRequest(
        message_id=message_id or f"msg_{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        payload=ActionPayload(
            prompt_text=prompt_text,
            actions=[Action(**action) for action in actions]
        )
    )


def create_slide_update(
    session_id: str,
    operation: Literal["full_update", "partial_update"],
    metadata: Dict[str, Any],
    slides: List[Dict[str, Any]],
    message_id: Optional[str] = None,
    affected_slides: Optional[List[str]] = None
) -> SlideUpdate:
    """Helper function to create a slide update"""
    import uuid
    return SlideUpdate(
        message_id=message_id or f"msg_{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        payload=SlideUpdatePayload(
            operation=operation,
            metadata=SlideMetadata(**metadata),
            slides=[SlideData(**slide) for slide in slides],
            affected_slides=affected_slides
        )
    )


def create_status_update(
    session_id: str,
    status: StatusLevel,
    text: str,
    message_id: Optional[str] = None,
    progress: Optional[int] = None,
    estimated_time: Optional[int] = None
) -> StatusUpdate:
    """Helper function to create a status update"""
    import uuid
    return StatusUpdate(
        message_id=message_id or f"msg_{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        payload=StatusPayload(
            status=status,
            text=text,
            progress=progress,
            estimated_time=estimated_time
        )
    )