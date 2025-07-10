"""
Message Adapter Layer

This module provides conversion between the legacy DirectorMessage format
and the new streamlined message protocol. Enables gradual migration and
backward compatibility.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json

from src.models.websocket_messages import (
    StreamlinedMessage,
    ChatMessage,
    ActionRequest,
    SlideUpdate,
    StatusUpdate,
    create_chat_message,
    create_action_request,
    create_slide_update,
    create_status_update,
    StatusLevel,
    Action
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class MessageAdapter:
    """Converts between legacy and streamlined message formats."""
    
    @staticmethod
    def legacy_to_streamlined(legacy_message: Dict[str, Any]) -> List[StreamlinedMessage]:
        """
        Convert a legacy DirectorMessage to streamlined messages.
        
        Args:
            legacy_message: Legacy format message
            
        Returns:
            List of streamlined messages
        """
        messages = []
        session_id = legacy_message.get("session_id", "")
        
        # Extract chat data if present
        chat_data = legacy_message.get("chat_data")
        if chat_data:
            messages.extend(MessageAdapter._convert_chat_data(chat_data, session_id))
        
        # Extract slide data if present
        slide_data = legacy_message.get("slide_data")
        if slide_data:
            messages.extend(MessageAdapter._convert_slide_data(slide_data, session_id))
        
        return messages
    
    @staticmethod
    def streamlined_to_legacy(
        messages: List[StreamlinedMessage],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Convert streamlined messages to legacy DirectorMessage format.
        This is primarily for testing and backward compatibility.
        
        Args:
            messages: List of streamlined messages
            session_id: Session identifier
            
        Returns:
            Legacy format message
        """
        from uuid import uuid4
        
        legacy_message = {
            "id": f"msg_{uuid4().hex[:12]}",
            "type": "director_message",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": session_id,
            "source": "director_inbound",
            "slide_data": None,
            "chat_data": None
        }
        
        # Process each message
        for msg in messages:
            if msg.type == "chat_message":
                legacy_message["chat_data"] = MessageAdapter._chat_to_legacy(msg)
            elif msg.type == "action_request":
                # Merge actions into chat_data if it exists
                if legacy_message["chat_data"] is None:
                    legacy_message["chat_data"] = {"type": "info", "content": ""}
                legacy_message["chat_data"]["actions"] = MessageAdapter._actions_to_legacy(msg)
            elif msg.type == "slide_update":
                legacy_message["slide_data"] = MessageAdapter._slides_to_legacy(msg)
            elif msg.type == "status_update":
                # Status updates map to progress in chat_data
                if legacy_message["chat_data"] is None:
                    legacy_message["chat_data"] = {"type": "progress"}
                legacy_message["chat_data"]["content"] = msg.payload.text
                legacy_message["chat_data"]["progress"] = {
                    "status": "processing" if msg.payload.status == StatusLevel.GENERATING else "idle",
                    "percentage": msg.payload.progress
                }
        
        return legacy_message
    
    @staticmethod
    def _convert_chat_data(chat_data: Dict[str, Any], session_id: str) -> List[StreamlinedMessage]:
        """Convert legacy chat_data to streamlined messages."""
        messages = []
        
        chat_type = chat_data.get("type", "info")
        content = chat_data.get("content")
        actions = chat_data.get("actions")
        progress = chat_data.get("progress")
        
        # Handle progress updates
        if chat_type == "progress" or progress:
            status_text = content if isinstance(content, str) else "Processing..."
            status_level = StatusLevel.GENERATING if progress and progress.get("status") == "processing" else StatusLevel.IDLE
            
            messages.append(create_status_update(
                session_id=session_id,
                status=status_level,
                text=status_text,
                progress=progress.get("percentage") if progress else None
            ))
        
        # Handle questions
        elif chat_type == "question" and isinstance(content, dict):
            questions = content.get("questions", [])
            messages.append(create_chat_message(
                session_id=session_id,
                text="Great topic! To create the perfect presentation for you, I need to understand your needs better:",
                list_items=questions
            ))
        
        # Handle summary (confirmation plan)
        elif chat_type == "summary" and isinstance(content, dict):
            summary = content.get("summary_of_user_request", "")
            assumptions = content.get("key_assumptions", [])
            slide_count = content.get("proposed_slide_count", 10)
            
            messages.append(create_chat_message(
                session_id=session_id,
                text=f"Perfect! Based on your input, I'll create a {slide_count}-slide presentation.",
                sub_title="Key assumptions I'm making:",
                list_items=assumptions
            ))
        
        # Handle regular chat messages
        elif content:
            text = content if isinstance(content, str) else str(content)
            messages.append(create_chat_message(
                session_id=session_id,
                text=text
            ))
        
        # Handle actions separately
        if actions:
            action_objs = []
            for action in actions:
                action_objs.append({
                    "label": action.get("label", ""),
                    "value": action.get("action_id", action.get("type", "")),
                    "primary": action.get("primary", False),
                    "requires_input": action.get("requires_input", False)
                })
            
            # Determine prompt text based on context
            prompt_text = "What would you like to do?"
            if chat_type == "summary":
                prompt_text = "Does this structure work for you?"
            elif any("refine" in a.get("type", "") for a in actions):
                prompt_text = "Your presentation is ready! What would you like to do?"
            
            messages.append(create_action_request(
                session_id=session_id,
                prompt_text=prompt_text,
                actions=action_objs
            ))
        
        return messages
    
    @staticmethod
    def _convert_slide_data(slide_data: Dict[str, Any], session_id: str) -> List[StreamlinedMessage]:
        """Convert legacy slide_data to streamlined slide update."""
        messages = []
        
        slides = slide_data.get("slides", [])
        metadata = slide_data.get("presentation_metadata", {})
        
        # Convert slides to new format
        converted_slides = []
        for slide in slides:
            # Note: In production, this would trigger HTML generation
            converted_slides.append({
                "slide_id": slide.get("slide_id", f"slide_{slide.get('slide_number', 0):03d}"),
                "slide_number": slide.get("slide_number", 0),
                "html_content": MessageAdapter._generate_placeholder_html(slide)
            })
        
        messages.append(create_slide_update(
            session_id=session_id,
            operation="full_update",
            metadata={
                "main_title": metadata.get("title", "Untitled Presentation"),
                "overall_theme": metadata.get("theme", "Professional"),
                "design_suggestions": metadata.get("design_suggestions", "Modern design"),
                "target_audience": metadata.get("target_audience", "General audience"),
                "presentation_duration": metadata.get("presentation_duration", 10)
            },
            slides=converted_slides
        ))
        
        return messages
    
    @staticmethod
    def _generate_placeholder_html(slide: Dict[str, Any]) -> str:
        """Generate placeholder HTML for a slide (for adapter only)."""
        slide_type = slide.get("slide_type", "content")
        title = slide.get("title", "")
        
        if slide_type == "title_slide":
            return f"""
            <div class="slide-container" data-slide-id="{slide.get('slide_id', '')}" data-slide-type="title_slide">
                <div class="hero-section">
                    <h1 class="slide-title">{title}</h1>
                    <p class="slide-subtitle">{slide.get('narrative', '')}</p>
                </div>
            </div>
            """
        else:
            key_points = slide.get("key_points", [])
            points_html = "\n".join(f"<li>{point}</li>" for point in key_points)
            
            return f"""
            <div class="slide-container" data-slide-id="{slide.get('slide_id', '')}" data-slide-type="{slide_type}">
                <h2 class="slide-title">{title}</h2>
                <div class="slide-body">
                    <p>{slide.get('narrative', '')}</p>
                    <ul class="key-points">{points_html}</ul>
                </div>
            </div>
            """
    
    @staticmethod
    def _chat_to_legacy(msg: ChatMessage) -> Dict[str, Any]:
        """Convert chat message to legacy format."""
        chat_data = {
            "type": "info",
            "content": msg.payload.text,
            "actions": None,
            "progress": None,
            "references": None
        }
        
        # Handle questions format
        if msg.payload.list_items:
            chat_data["type"] = "question"
            chat_data["content"] = {"questions": msg.payload.list_items}
        
        return chat_data
    
    @staticmethod
    def _actions_to_legacy(msg: ActionRequest) -> List[Dict[str, Any]]:
        """Convert action request to legacy format."""
        actions = []
        for action in msg.payload.actions:
            actions.append({
                "action_id": action.value,
                "type": action.value,
                "label": action.label,
                "primary": action.primary,
                "requires_input": action.requires_input
            })
        return actions
    
    @staticmethod
    def _slides_to_legacy(msg: SlideUpdate) -> Dict[str, Any]:
        """Convert slide update to legacy format."""
        # Note: This loses HTML content as legacy format doesn't support it
        slides = []
        for slide in msg.payload.slides:
            # Extract basic info from HTML if needed
            slides.append({
                "slide_id": slide.slide_id,
                "slide_number": slide.slide_number,
                "slide_type": "content",  # Default as we can't extract from HTML
                "title": f"Slide {slide.slide_number}",
                "narrative": "",
                "key_points": [],
                "body_content": [],
                "layout_type": "content",
                "animations": [],
                "transitions": {}
            })
        
        return {
            "type": "complete",
            "slides": slides,
            "presentation_metadata": {
                "title": msg.payload.metadata.main_title,
                "total_slides": len(slides),
                "theme": msg.payload.metadata.overall_theme,
                "design_suggestions": msg.payload.metadata.design_suggestions,
                "target_audience": msg.payload.metadata.target_audience,
                "presentation_duration": msg.payload.metadata.presentation_duration
            }
        }
    
    @staticmethod
    def validate_conversion(
        original: Union[Dict[str, Any], List[StreamlinedMessage]],
        converted: Union[List[StreamlinedMessage], Dict[str, Any]]
    ) -> bool:
        """
        Validate that conversion preserved essential information.
        
        Args:
            original: Original message(s)
            converted: Converted message(s)
            
        Returns:
            True if conversion is valid
        """
        try:
            # Basic validation - ensure we have output
            if not converted:
                return False
            
            # More detailed validation could be added here
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False