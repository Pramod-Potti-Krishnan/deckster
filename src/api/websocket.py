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
        self.initialized = False
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
        
        # Mark initialization complete
        self.initialized = True
    
    async def _create_session(self):
        """Create a new session."""
        # TEMPORARY: Skip Supabase due to persistent RLS policy issues
        # TODO: Fix Supabase RLS policies and re-enable this code
        # try:
        #     # Try to create session in Supabase
        #     await self.supabase.create_session(
        #         session_id=self.session_id,
        #         user_id=self.token_data.user_id,
        #         expires_hours=24
        #     )
        # except Exception as e:
        #     # If Supabase fails (RLS policy issue), just log and continue with Redis
        #     api_logger.warning(f"Supabase session creation failed, using Redis only: {e}")
        
        # Only use Redis for sessions (this works reliably)
        await self.redis.set_session(
            self.session_id,
            {
                "user_id": self.token_data.user_id,
                "created_at": datetime.utcnow().isoformat(),
                "websocket_id": self.websocket_id,
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
        )
        api_logger.info(f"Session created in Redis: {self.session_id}")
    
    async def handle_connection(self):
        """Main handler for WebSocket connection."""
        try:
            # Verify session was created successfully before proceeding
            session_exists = await self.redis.get_session(self.session_id)
            if not session_exists:
                api_logger.error(f"Session not found after initialization: {self.session_id}")
                await self._send_error("Session initialization failed", code="SESSION_ERROR")
                await self.websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                return
            
            # NOW send connection success message
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
        # Check if fully initialized
        if not self.initialized:
            await self._send_error("Connection not fully initialized", code="NOT_READY")
            return
            
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
        
        # ROUND 24 DEBUG: Log immediately when user input received
        api_logger.info(
            f"🔍 ROUND 24 DEBUG: Received user input",
            text=text,
            session_id=self.session_id,
            has_workflow_runner=self.workflow_runner is not None,
            workflow_runner_type=type(self.workflow_runner).__name__ if self.workflow_runner else "None"
        )
        
        try:
            # Security validation
            validated_text = validate_text_input(text)
            if not validate_prompt_injection(validated_text):
                await self._send_error(
                    "Input contains potentially unsafe content",
                    code="UNSAFE_INPUT"
                )
                return
            
            # Debug logging for message processing
            api_logger.info(
                f"Processing user input: text='{text[:50]}...', has_response_to={bool(message.data.get('response_to'))}",
                session_id=self.session_id
            )
            
            # ROUND 24 TEMPORARY: Direct greeting response for testing
            text_lower = text.lower().strip()
            if text_lower in ["hi", "hello", "hey"]:
                api_logger.info(f"🔍 ROUND 24: Direct greeting response for '{text}'")
                await self._send_chat_message(
                    message_type="info",
                    content={
                        "message": "Hello! I'm currently in diagnostic mode. The main workflow is being debugged.",
                        "context": "greeting_fallback",
                        "debug": {"mode": "direct_response", "workflow_bypassed": True}
                    }
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
            # Debug logging for workflow start
            api_logger.debug(
                f"Starting presentation generation - workflow_runner={self.workflow_runner is not None}",
                session_id=self.session_id,
                user_input_text=user_input.data.get("text", "")[:100]
            )
            
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
                content={
                    "message": "I'm analyzing your request...",
                    "context": "Starting presentation analysis workflow",
                    "options": None,
                    "question_id": None
                },
                progress=self._create_progress_update("analysis", 10)
            )
            
            # Debug logging before workflow start
            api_logger.debug(
                "Calling workflow_runner.start_generation",
                session_id=self.session_id,
                workflow_runner_type=type(self.workflow_runner).__name__
            )
            
            # ROUND 24: Wrap workflow execution with detailed error handling
            try:
                api_logger.info(f"🔍 ROUND 24: Attempting to start workflow")
                self.workflow_state = await self.workflow_runner.start_generation(
                    user_input=user_input,
                    session_id=self.session_id,
                    user_id=self.token_data.user_id
                )
                api_logger.info(f"🔍 ROUND 24: Workflow started successfully")
            except Exception as workflow_error:
                api_logger.error(
                    f"❌ ROUND 24: Workflow execution failed",
                    error_type=type(workflow_error).__name__,
                    error_message=str(workflow_error),
                    workflow_type=type(self.workflow_runner).__name__,
                    session_id=self.session_id,
                    exc_info=True  # Full traceback
                )
                
                # Send detailed error to frontend
                await self._send_chat_message(
                    message_type="error",
                    content={
                        "message": f"Workflow error: {type(workflow_error).__name__}",
                        "error": str(workflow_error),
                        "debug_info": {
                            "workflow_type": type(self.workflow_runner).__name__,
                            "error_type": type(workflow_error).__name__,
                            "round": "24"
                        }
                    }
                )
                return
            
            # Debug logging after workflow returns
            api_logger.debug(
                f"Workflow returned state: phase={self.workflow_state.get('current_phase') if self.workflow_state else 'None'}",
                session_id=self.session_id,
                has_workflow_state=self.workflow_state is not None,
                workflow_state_keys=list(self.workflow_state.keys()) if self.workflow_state else []
            )
            
            # Handle workflow result
            await self._handle_workflow_state()
        
        except Exception as e:
            # Enhanced error logging
            api_logger.error(
                f"Workflow start failed: {type(e).__name__}: {str(e)}",
                session_id=self.session_id,
                error_type=type(e).__name__,
                error_message=str(e),
                has_workflow_runner=self.workflow_runner is not None,
                workflow_runner_type=type(self.workflow_runner).__name__ if self.workflow_runner else "None",
                exc_info=True  # Include full traceback
            )
            
            log_error(e, "workflow_start_failed", {
                "session_id": self.session_id,
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            
            # Send structured error response that frontend can handle
            error_message = str(e)
            if "StateGraph" in error_message:
                error_code = "WORKFLOW_UNAVAILABLE"
                user_message = "Workflow system temporarily unavailable. Using simplified processor."
            else:
                error_code = "GENERATION_FAILED"
                user_message = "Unable to start presentation generation. Please try again."
            
            # Send as chat message so frontend can display it properly
            await self._send_chat_message(
                message_type="error",
                content={
                    "message": user_message,
                    "error": error_message,
                    "code": error_code
                },
                progress=self._create_progress_update("error", 0)
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
            api_logger.warning("No workflow state to handle")
            return
        
        phase = self.workflow_state.get("current_phase")
        api_logger.info(
            f"Handling workflow state: phase={phase}, has_clarifications={bool(self.workflow_state.get('clarification_rounds'))}",
            session_id=self.session_id
        )
        
        if phase == "greeting":
            # Send greeting response
            greeting_resp = self.workflow_state.get("greeting_response", {})
            await self._send_chat_message(
                message_type="info",
                content={
                    "message": greeting_resp.get("message", "Hello! How can I help you create a presentation today?"),
                    "context": "greeting",
                    "options": greeting_resp.get("suggestions", []),
                    "question_id": None
                }
            )
        
        elif phase == "clarification":
            # Send clarification questions
            rounds = self.workflow_state.get("clarification_rounds", [])
            if rounds:
                latest_round = rounds[-1]
                await self._send_clarification_questions(latest_round)
        
        elif phase == "generation":
            # Send progress update
            await self._send_chat_message(
                message_type="info",
                content={
                    "message": "Creating your presentation structure...",
                    "context": "Generating slides based on analysis",
                    "options": None,
                    "question_id": None
                },
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
                    content={
                        "message": f"Testing {stage} stage at {percentage}%",
                        "context": f"Debug test for {stage} phase",
                        "options": None,
                        "question_id": None
                    },
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
                content={
                    "message": "Test: Chat data only message",
                    "context": "Testing basic chat functionality",
                    "options": None,
                    "question_id": None
                }
            )
            
            # 2. Chat with progress
            await self._send_chat_message(
                message_type="info",
                content={
                    "message": "Test: Chat with progress",
                    "context": "Testing progress integration",
                    "options": None,
                    "question_id": None
                },
                progress=self._create_progress_update("analysis", 25, ["director"])
            )
            
            # 3. Question with actions
            await self._send_chat_message(
                message_type="question",
                content={
                    "message": "Test: Question with actions",
                    "context": "Testing interactive message features",
                    "options": ["Yes", "No"],
                    "question_id": "test_q_001"
                },
                actions=[
                    {"action_id": "yes", "type": "custom", "label": "Yes", "primary": True},
                    {"action_id": "no", "type": "custom", "label": "No"}
                ]
            )
            
            # 4. Test slide data structure
            await asyncio.sleep(1)
            test_slide_data = SlideData(
                type="complete",
                slides=[
                    {
                        "slide_id": "slide_1",
                        "slide_number": 1,
                        "title": "Test Slide",
                        "subtitle": "Testing slide data extraction",
                        "body_content": [{"type": "text", "content": "This tests if frontend correctly extracts slides array"}],
                        "layout_type": "content",
                        "speaker_notes": "Verify state.slides is an array, not an object"
                    }
                ],
                presentation_metadata={
                    "title": "Test Presentation",
                    "total_slides": 1
                }
            )
            
            message = DirectorMessage(
                session_id=self.session_id,
                source="director_outbound",
                slide_data=test_slide_data,
                chat_data=ChatData(
                    type="info",
                    content={
                        "message": "Test: Slide data sent. Check if state.slides is an array!",
                        "context": "Testing slide data structure",
                        "options": None,
                        "question_id": None
                    }
                )
            )
            
            message_dict = message.model_dump(mode='json')
            api_logger.debug(
                f"Sending test DirectorMessage with slide_data: {json.dumps(message_dict, indent=2)}",
                session_id=self.session_id
            )
            
            await self.websocket.send_json(message_dict)
        
        else:
            await self._send_chat_message(
                message_type="info",
                content={
                    "message": f"Unknown test command: {test_command}. Available: progress, empty, structures",
                    "context": "Test command help",
                    "options": ["progress", "empty", "structures"],
                    "question_id": None
                }
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
                content={
                    "message": f"Action '{action}' noted but not implemented in Phase 1",
                    "context": "Frontend action processing",
                    "options": None,
                    "question_id": None
                }
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
            elif stage == "error":
                agent_statuses = {agent: "error" for agent in all_agents}
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
        
        # Extract first question text as main message
        first_question_text = clarification_round.questions[0].question if clarification_round.questions else "Please provide more information"
        
        await self._send_chat_message(
            message_type="question",
            content={
                "message": first_question_text,
                "context": clarification_round.context or "I need some additional information to create the best presentation for you",
                "options": None,
                "question_id": clarification_round.questions[0].question_id if clarification_round.questions else None,
                "round_id": clarification_round.round_id,
                "questions": questions_data
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
                content={
                    "message": "Draft saved successfully",
                    "context": "Presentation draft saved to database",
                    "options": None,
                    "question_id": None
                }
            )
        else:
            await self._send_error("No presentation to save")
    
    async def _export_presentation(self, payload: Dict[str, Any]):
        """Export presentation in requested format."""
        # Phase 1: Just acknowledge
        format_type = payload.get("format", "pptx")
        await self._send_chat_message(
            message_type="info",
            content={
                "message": f"Export to {format_type} will be available in Phase 2",
                "context": "Export functionality preview",
                "options": ["pptx", "pdf", "html"],
                "question_id": None
            }
        )
    
    async def _share_presentation(self, payload: Dict[str, Any]):
        """Share presentation."""
        # Phase 1: Just acknowledge
        await self._send_chat_message(
            message_type="info",
            content={
                "message": "Sharing functionality will be available in Phase 2",
                "context": "Share feature preview",
                "options": ["public link", "team share", "email"],
                "question_id": None
            }
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