"""
WebSocket handler for real-time communication with clients.
Implements the communication protocol defined in comms_protocol.md.
"""

import json
import asyncio
from typing import Dict, Any, Optional, Set, List
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from fastapi.websockets import WebSocketState

from ..models.messages import (
    BaseMessage, UserInput, DirectorMessage, SystemMessage,
    ConnectionMessage, FrontendAction, ClarificationResponse,
    SlideData, ChatData, validate_message
)
from ..models.presentation import Presentation
from ..utils.auth import authenticate_websocket, TokenData
from ..utils.validators import validate_text_input, validate_prompt_injection
from ..utils.logger import (
    api_logger, set_request_id, set_session_id, set_user_id,
    log_api_request, log_api_response, log_error, clear_context
)
from ..storage import get_redis, get_supabase
from ..workflows import get_workflow_runner, WorkflowState


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_mapping: Dict[str, str] = {}  # websocket_id -> session_id
    
    async def connect(self, websocket_id: str, websocket: WebSocket):
        """Add a new connection."""
        self.active_connections[websocket_id] = websocket
        api_logger.info(f"WebSocket connected: {websocket_id}")
    
    async def disconnect(self, websocket_id: str):
        """Remove a connection."""
        if websocket_id in self.active_connections:
            del self.active_connections[websocket_id]
            
            # Clean up session mapping
            if websocket_id in self.session_mapping:
                del self.session_mapping[websocket_id]
            
            api_logger.info(f"WebSocket disconnected: {websocket_id}")
    
    async def send_message(self, websocket_id: str, message: BaseMessage):
        """Send a message to a specific connection."""
        if websocket_id in self.active_connections:
            websocket = self.active_connections[websocket_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message.model_dump(mode='json'))
    
    async def broadcast_to_session(self, session_id: str, message: BaseMessage):
        """Broadcast a message to all connections in a session."""
        for ws_id, sess_id in self.session_mapping.items():
            if sess_id == session_id:
                await self.send_message(ws_id, message)
    
    def map_session(self, websocket_id: str, session_id: str):
        """Map a WebSocket connection to a session."""
        self.session_mapping[websocket_id] = session_id


# Global connection manager
connection_manager = ConnectionManager()


class WebSocketHandler:
    """Handles WebSocket communication for a single connection."""
    
    def __init__(
        self,
        websocket: WebSocket,
        websocket_id: str,
        token_data: TokenData
    ):
        self.websocket = websocket
        self.websocket_id = websocket_id
        self.token_data = token_data
        self.session_id: Optional[str] = token_data.session_id
        self.workflow_state: Optional[WorkflowState] = None
        self.redis = None
        self.supabase = None
        try:
            self.workflow_runner = get_workflow_runner()
        except Exception as e:
            api_logger.error(f"Failed to initialize workflow runner: {e}")
            self.workflow_runner = None
    
    async def initialize(self):
        """Initialize handler resources."""
        self.redis = await get_redis()
        self.supabase = get_supabase()
        
        # Create or restore session
        if not self.session_id:
            self.session_id = f"session_{uuid4().hex[:12]}"
            await self._create_session()
        else:
            # Try Redis first, then Supabase
            session_data = await self.redis.get_session(self.session_id)
            if not session_data:
                try:
                    session_data = await self.supabase.get_session(self.session_id)
                except Exception as e:
                    api_logger.warning(f"Supabase session lookup failed: {e}")
                    session_data = None
                    
            if not session_data:
                await self._create_session()
        
        # Map connection to session
        connection_manager.map_session(self.websocket_id, self.session_id)
        
        # Set logging context
        set_session_id(self.session_id)
        set_user_id(self.token_data.user_id)
    
    async def _create_session(self):
        """Create a new session."""
        try:
            # Try to create session in Supabase
            await self.supabase.create_session(
                session_id=self.session_id,
                user_id=self.token_data.user_id,
                expires_hours=24
            )
        except Exception as e:
            # If Supabase fails (RLS policy issue), just log and continue with Redis
            api_logger.warning(f"Supabase session creation failed, using Redis only: {e}")
        
        # Always cache in Redis (this is our primary session store for now)
        await self.redis.set_session(
            self.session_id,
            {
                "user_id": self.token_data.user_id,
                "created_at": datetime.utcnow().isoformat(),
                "websocket_id": self.websocket_id,
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
        )
    
    async def handle_connection(self):
        """Main handler for WebSocket connection."""
        try:
            # Send connection success message
            await self._send_connection_message("connected")
            
            # Main message loop
            while self.websocket.client_state == WebSocketState.CONNECTED:
                # Receive message
                try:
                    raw_message = await self.websocket.receive_json()
                    await self._process_message(raw_message)
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    await self._send_error("Invalid JSON format")
                except Exception as e:
                    api_logger.error(f"Message processing error: {e}")
                    await self._send_error(f"Processing error: {str(e)}")
        
        except Exception as e:
            log_error(e, "websocket_handler_error", {
                "websocket_id": self.websocket_id,
                "session_id": self.session_id
            })
        
        finally:
            # Cleanup
            await connection_manager.disconnect(self.websocket_id)
            clear_context()
    
    async def _process_message(self, raw_message: Dict[str, Any]):
        """Process incoming message."""
        request_id = f"req_{uuid4().hex[:12]}"
        set_request_id(request_id)
        
        # Log request
        log_api_request(
            method="WEBSOCKET",
            path="/ws",
            headers={},
            body_size=len(json.dumps(raw_message))
        )
        
        try:
            # Validate message structure
            message = validate_message(raw_message)
            
            # Route based on message type
            if message.type == "user_input":
                await self._handle_user_input(message)
            elif message.type == "frontend_action":
                await self._handle_frontend_action(message)
            elif message.type == "connection":
                await self._handle_connection_message(message)
            else:
                await self._send_error(f"Unknown message type: {message.type}")
            
            # Log successful response
            log_api_response(
                status_code=200,
                response_time_ms=10  # Placeholder
            )
            
        except ValueError as e:
            await self._send_error(f"Invalid message: {str(e)}")
            log_api_response(
                status_code=400,
                response_time_ms=5,
                error=str(e)
            )
        except Exception as e:
            await self._send_error(f"Processing error: {str(e)}")
            log_api_response(
                status_code=500,
                response_time_ms=5,
                error=str(e)
            )
    
    async def _handle_user_input(self, message: UserInput):
        """Handle user input message."""
        # Validate input
        text = message.data.get("text", "")
        
        try:
            # Security validation
            validated_text = validate_text_input(text)
            if not validate_prompt_injection(validated_text):
                await self._send_error(
                    "Input contains potentially unsafe content",
                    code="UNSAFE_INPUT"
                )
                return
            
            # Check for test messages
            if text.lower().startswith("test:"):
                await self._handle_test_message(text)
            # Check if this is a clarification response
            elif message.data.get("response_to"):
                await self._handle_clarification_response(message)
            else:
                # New presentation request
                await self._start_presentation_generation(message)
        
        except ValueError as e:
            await self._send_error(str(e), code="VALIDATION_ERROR")
    
    async def _start_presentation_generation(self, user_input: UserInput):
        """Start a new presentation generation workflow."""
        try:
            # Check if workflow runner is available
            if not self.workflow_runner:
                await self._send_error(
                    "Presentation generation system is currently unavailable",
                    code="WORKFLOW_UNAVAILABLE"
                )
                return
            
            # Send acknowledgment
            await self._send_chat_message(
                message_type="info",
                content="I'm analyzing your request...",
                progress=self._create_progress_update("analysis", 10)
            )
            
            # Start workflow
            self.workflow_state = await self.workflow_runner.start_generation(
                user_input=user_input,
                session_id=self.session_id,
                user_id=self.token_data.user_id
            )
            
            # Handle workflow result
            await self._handle_workflow_state()
        
        except Exception as e:
            log_error(e, "workflow_start_failed", {
                "session_id": self.session_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            
            # Handle specific LangGraph errors
            if "StateGraph" in str(e):
                await self._send_error(
                    "Workflow system temporarily unavailable. We're using a simplified processor for now.",
                    code="WORKFLOW_FALLBACK"
                )
            else:
                await self._send_error(
                    "Failed to start presentation generation",
                    code="WORKFLOW_ERROR"
                )
    
    async def _handle_clarification_response(self, message: UserInput):
        """Handle clarification response from user."""
        if not self.workflow_state:
            await self._send_error("No active workflow", code="NO_WORKFLOW")
            return
        
        # Create clarification response
        response = ClarificationResponse(
            round_id=message.data.get("response_to"),
            responses=message.data.get("responses", {})
        )
        
        # Process through workflow
        self.workflow_state = await self.workflow_runner.process_clarification(
            self.workflow_state,
            response
        )
        
        # Handle updated state
        await self._handle_workflow_state()
    
    async def _handle_workflow_state(self):
        """Handle workflow state and send appropriate messages."""
        if not self.workflow_state:
            return
        
        phase = self.workflow_state.get("current_phase")
        
        if phase == "clarification":
            # Send clarification questions
            rounds = self.workflow_state.get("clarification_rounds", [])
            if rounds:
                latest_round = rounds[-1]
                await self._send_clarification_questions(latest_round)
        
        elif phase == "generation":
            # Send progress update
            await self._send_chat_message(
                message_type="info",
                content="Creating your presentation structure...",
                progress=self._create_progress_update("generation", 30)
            )
        
        elif phase == "completed":
            # Send final presentation
            presentation = self.workflow_state.get("final_presentation")
            if presentation:
                await self._send_presentation(presentation)
            else:
                await self._send_error("Presentation generation failed")
    
    async def _handle_test_message(self, text: str):
        """Handle test messages for debugging message structures."""
        test_command = text[5:].strip().lower()  # Remove "test:" prefix
        
        if test_command == "progress":
            # Test progress updates
            stages = [
                ("analysis", 10, None),
                ("generation", 30, ["researcher", "ux_architect"]),
                ("generation", 60, ["visual_designer", "data_analyst"]),
                ("completed", 100, None)
            ]
            
            for stage, percentage, agents in stages:
                await self._send_chat_message(
                    message_type="info",
                    content=f"Testing {stage} stage at {percentage}%",
                    progress=self._create_progress_update(stage, percentage, agents)
                )
                await asyncio.sleep(1)  # Small delay between messages
        
        elif test_command == "empty":
            # Test empty DirectorMessage (should get default chat_data)
            try:
                message = DirectorMessage(
                    session_id=self.session_id,
                    source="director_inbound"
                    # Intentionally not providing chat_data or slide_data
                )
                await self.websocket.send_json(message.model_dump(mode='json'))
            except Exception as e:
                await self._send_error(f"Empty message test failed: {str(e)}")
        
        elif test_command == "structures":
            # Test various message structures
            # 1. Chat only
            await self._send_chat_message(
                message_type="info",
                content="Test: Chat data only message"
            )
            
            # 2. Chat with progress
            await self._send_chat_message(
                message_type="info",
                content="Test: Chat with progress",
                progress=self._create_progress_update("analysis", 25, ["director"])
            )
            
            # 3. Question with actions
            await self._send_chat_message(
                message_type="question",
                content="Test: Question with actions",
                actions=[
                    {"action_id": "yes", "type": "custom", "label": "Yes", "primary": True},
                    {"action_id": "no", "type": "custom", "label": "No"}
                ]
            )
        
        else:
            await self._send_chat_message(
                message_type="info",
                content=f"Unknown test command: {test_command}. Available: progress, empty, structures"
            )
    
    async def _handle_frontend_action(self, message: FrontendAction):
        """Handle frontend action message."""
        action = message.action
        
        if action == "save_draft":
            await self._save_draft()
        elif action == "export":
            await self._export_presentation(message.payload)
        elif action == "share":
            await self._share_presentation(message.payload)
        else:
            await self._send_chat_message(
                message_type="info",
                content=f"Action '{action}' noted but not implemented in Phase 1"
            )
    
    async def _handle_connection_message(self, message: ConnectionMessage):
        """Handle connection control message."""
        if message.status == "ping":
            # Respond with pong
            await self._send_connection_message("pong")
    
    async def _send_connection_message(self, status: str):
        """Send connection status message."""
        message = ConnectionMessage(
            status=status,
            session_id=self.session_id,
            user_id=self.token_data.user_id,
            metadata={
                "server_time": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
        )
        await self.websocket.send_json(message.model_dump(mode='json'))
    
    async def _send_chat_message(
        self,
        message_type: str,
        content: Any,
        actions: Optional[List[Dict]] = None,
        progress: Optional[Dict] = None
    ):
        """Send chat message to client."""
        chat_data = ChatData(
            type=message_type,
            content=content,
            actions=actions,
            progress=progress
        )
        
        message = DirectorMessage(
            session_id=self.session_id,
            source="director_inbound",
            chat_data=chat_data
        )
        
        # Debug logging for frontend team
        message_dict = message.model_dump(mode='json')
        api_logger.debug(
            f"Sending DirectorMessage to frontend: {json.dumps(message_dict, indent=2)}",
            session_id=self.session_id,
            message_type="director_inbound",
            has_chat_data=bool(chat_data),
            has_slide_data=False
        )
        
        await self.websocket.send_json(message_dict)
    
    def _create_progress_update(
        self, 
        stage: str, 
        percentage: int,
        active_agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a progress update with agent statuses."""
        # Default agent list if none provided
        all_agents = ["director", "researcher", "ux_architect", "visual_designer", "data_analyst", "ux_analyst"]
        
        # Build agent statuses
        agent_statuses = {}
        if active_agents:
            for agent in all_agents:
                if agent in active_agents:
                    agent_statuses[agent] = "active"
                elif all_agents.index(agent) < all_agents.index(active_agents[0]):
                    agent_statuses[agent] = "completed"
                else:
                    agent_statuses[agent] = "pending"
        else:
            # Default status based on stage
            if stage == "analysis":
                agent_statuses = {agent: "pending" for agent in all_agents}
                agent_statuses["director"] = "active"
            elif stage == "generation":
                agent_statuses["director"] = "completed"
                agent_statuses["researcher"] = "active"
                agent_statuses["ux_architect"] = "active"
                for agent in ["visual_designer", "data_analyst", "ux_analyst"]:
                    agent_statuses[agent] = "pending"
            else:
                agent_statuses = {agent: "completed" for agent in all_agents}
        
        return {
            "stage": stage,
            "percentage": percentage,
            "agentStatuses": agent_statuses
        }
    
    async def _send_clarification_questions(self, clarification_round):
        """Send clarification questions to client."""
        questions_data = []
        for q in clarification_round.questions:
            questions_data.append({
                "id": q.question_id,
                "question": q.question,
                "type": q.question_type,
                "options": q.options,
                "required": q.required
            })
        
        await self._send_chat_message(
            message_type="question",
            content={
                "round_id": clarification_round.round_id,
                "questions": questions_data,
                "context": clarification_round.context
            },
            actions=[{
                "action_id": "submit_answers",
                "type": "custom",
                "label": "Submit Answers",
                "primary": True,
                "requires_input": True
            }]
        )
    
    async def _send_presentation(self, presentation: Presentation):
        """Send complete presentation to client."""
        # Convert to slide data format
        slides = []
        for slide in presentation.slides:
            slides.append({
                "slide_id": slide.slide_id,
                "slide_number": slide.slide_number,
                "title": slide.title,
                "subtitle": slide.subtitle,
                "body_content": [
                    comp.model_dump() for comp in slide.components
                ],
                "layout_type": slide.layout_type,
                "speaker_notes": slide.speaker_notes
            })
        
        slide_data = SlideData(
            type="complete",
            slides=slides,
            presentation_metadata={
                "title": presentation.title,
                "total_slides": len(presentation.slides),
                "theme": presentation.theme.name
            }
        )
        
        # Send presentation
        message = DirectorMessage(
            session_id=self.session_id,
            source="director_outbound",
            slide_data=slide_data,
            chat_data=ChatData(
                type="summary",
                content={
                    "message": "Your presentation is ready!",
                    "title": presentation.title,
                    "slides": len(presentation.slides)
                },
                actions=[
                    {
                        "action_id": "download",
                        "type": "custom",
                        "label": "Download",
                        "primary": True
                    },
                    {
                        "action_id": "edit",
                        "type": "custom",
                        "label": "Make Changes"
                    }
                ],
                progress=self._create_progress_update("completed", 100)
            )
        )
        
        # Debug logging for frontend team
        message_dict = message.model_dump(mode='json')
        api_logger.debug(
            f"Sending DirectorMessage to frontend: {json.dumps(message_dict, indent=2)}",
            session_id=self.session_id,
            message_type="director_outbound",
            has_chat_data=bool(message.chat_data),
            has_slide_data=bool(message.slide_data)
        )
        
        await self.websocket.send_json(message_dict)
    
    async def _send_error(self, message: str, code: Optional[str] = None):
        """Send error message to client."""
        error_message = SystemMessage(
            session_id=self.session_id,
            level="error",
            code=code or "ERROR",
            message=message
        )
        await self.websocket.send_json(error_message.model_dump(mode='json'))
    
    async def _save_draft(self):
        """Save current presentation as draft."""
        if self.workflow_state and self.workflow_state.get("presentation_structure"):
            # Save to database
            # Implementation would save the current state
            await self._send_chat_message(
                message_type="info",
                content="Draft saved successfully"
            )
        else:
            await self._send_error("No presentation to save")
    
    async def _export_presentation(self, payload: Dict[str, Any]):
        """Export presentation in requested format."""
        # Phase 1: Just acknowledge
        format_type = payload.get("format", "pptx")
        await self._send_chat_message(
            message_type="info",
            content=f"Export to {format_type} will be available in Phase 2"
        )
    
    async def _share_presentation(self, payload: Dict[str, Any]):
        """Share presentation."""
        # Phase 1: Just acknowledge
        await self._send_chat_message(
            message_type="info",
            content="Sharing functionality will be available in Phase 2"
        )


async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint."""
    websocket_id = f"ws_{uuid4().hex[:12]}"
    
    try:
        # Accept connection
        await websocket.accept()
        await connection_manager.connect(websocket_id, websocket)
        
        # Authenticate
        try:
            token_data = await authenticate_websocket(websocket)
        except Exception as e:
            api_logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Create handler
        handler = WebSocketHandler(websocket, websocket_id, token_data)
        await handler.initialize()
        
        # Handle connection
        await handler.handle_connection()
    
    except WebSocketDisconnect:
        api_logger.info(f"WebSocket disconnected: {websocket_id}")
    except Exception as e:
        api_logger.error(f"WebSocket error: {e}")
    finally:
        await connection_manager.disconnect(websocket_id)


# Export
__all__ = [
    'websocket_endpoint',
    'ConnectionManager',
    'WebSocketHandler'
]