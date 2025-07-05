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
            # Inject session_id into the raw message before validation
            raw_message['session_id'] = self.session_id
            
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
            
            # Removed ROUND 24 temporary bypass - let all messages go through the workflow
            
            # Check for test messages
            if text.lower().startswith("test:"):
                await self._handle_test_message(text)
            # Check if this is a clarification response
            elif message.data.get("response_to") or (self.workflow_state and self.workflow_state.get("current_phase") == "clarification"):
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
                # User requested simple message when AI isn't working
                await self._send_chat_message(
                    message_type="error",
                    content={
                        "message": "Sorry, We're still working on the AI Agent",
                        "context": "AI presentation generation is temporarily unavailable",
                        "options": None,
                        "question_id": None
                    }
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
            
            # ROUND 24: Stream workflow updates
            try:
                api_logger.info(f"🔍 ROUND 24: Starting workflow stream")
                
                # Create initial state
                initial_state = {
                    "request_id": f"req_{uuid4().hex[:12]}",
                    "session_id": self.session_id,
                    "user_id": self.token_data.user_id,
                    "correlation_id": f"corr_{uuid4().hex[:12]}",
                    "user_input": user_input,
                    "presentation_request": None,
                    "clarification_rounds": [],
                    "clarification_responses": [],
                    "requirement_analysis": None,
                    "presentation_structure": None,
                    "layouts": None,
                    "research_findings": None,
                    "visual_assets": None,
                    "chart_data": None,
                    "diagrams": None,
                    "slides_data": None,
                    "final_presentation": None,
                    "current_phase": "analysis",
                    "needs_clarification": False,
                    "agent_outputs": {},
                    "agent_errors": {},
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "processing_time_ms": 0
                }
                
                # Stream workflow updates
                async for state in self.workflow_runner.workflow.astream(initial_state):
                    api_logger.info(
                        f"🔍 ROUND 24: Workflow state update",
                        phase=state.get("current_phase"),
                        session_id=self.session_id
                    )
                    
                    # Update our state
                    self.workflow_state = state
                    
                    # ROUND 24 FIX: Log the actual state structure
                    api_logger.info(
                        f"🔍 ROUND 24 FIX: Workflow state structure",
                        session_id=self.session_id,
                        state_keys=list(state.keys()) if isinstance(state, dict) else "Not a dict",
                        current_phase=state.get("current_phase") if isinstance(state, dict) else "N/A",
                        state_type=type(state).__name__
                    )
                    
                    # Handle the updated state immediately
                    await self._handle_workflow_state()
                    
                    # If we need clarification, break the loop
                    if state.get("needs_clarification"):
                        api_logger.info(f"🔍 ROUND 24: Breaking for clarification")
                        break
                
                api_logger.info(f"🔍 ROUND 24: Workflow stream completed")
                
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
        
        api_logger.info(
            f"Processing clarification response: '{message.data.get('text', '')[:50]}...'",
            session_id=self.session_id,
            current_phase=self.workflow_state.get("current_phase")
        )
        
        # Store the user's response in the session context
        redis = await get_redis()
        session_data = await redis.get_session(self.session_id) or {}
        
        # Add this response to the accumulated clarifications
        clarifications = session_data.get("clarification_responses", [])
        clarifications.append({
            "text": message.data.get("text", ""),
            "timestamp": message.timestamp.isoformat() if message.timestamp else datetime.utcnow().isoformat()
        })
        
        session_data["clarification_responses"] = clarifications
        await redis.set_session(self.session_id, session_data)
        
        # Check if user indicates they're done answering
        user_text = message.data.get("text", "").lower()
        done_keywords = ["done", "that's all", "finished", "continue", "proceed", "go ahead", "next"]
        
        if any(keyword in user_text for keyword in done_keywords) or len(clarifications) >= 3:
            # User is done answering, process all clarifications and continue workflow
            await self._process_accumulated_clarifications()
        else:
            # Acknowledge the response and continue waiting for more
            await self._send_chat_message(
                message_type="info",
                content={
                    "message": f"Got it: '{message.data.get('text', '')[:50]}...' Anything else about your presentation?",
                    "context": "Collecting additional details. Say 'done' when you're ready to continue.",
                    "options": ["I'm done", "Tell you more"],
                    "question_id": None
                },
                progress=self._create_progress_update("clarification", min(20 + len(clarifications) * 15, 80))
            )
    
    async def _process_accumulated_clarifications(self):
        """Process all accumulated clarification responses and continue workflow."""
        try:
            api_logger.info(f"Processing accumulated clarifications", session_id=self.session_id)
            
            # Get all clarification responses
            redis = await get_redis()
            session_data = await redis.get_session(self.session_id) or {}
            clarifications = session_data.get("clarification_responses", [])
            
            # Combine all responses into a single text
            combined_responses = " ".join([resp["text"] for resp in clarifications])
            
            # Send processing message
            await self._send_chat_message(
                message_type="info", 
                content={
                    "message": "Perfect! I have all the information I need. Let me create your presentation now...",
                    "context": "Processing your requirements and creating presentation structure",
                    "options": None,
                    "question_id": None
                },
                progress=self._create_progress_update("generation", 50)
            )
            
            # Continue the workflow with a new analysis that incorporates the clarifications
            from ..models.messages import UserInput
            from datetime import datetime
            from uuid import uuid4
            
            # Create a comprehensive input that includes original request + clarifications
            original_input = self.workflow_state.get("user_input", {})
            if hasattr(original_input, 'data'):
                original_text = original_input.data.get("text", "") if original_input.data else ""
            else:
                original_text = original_input.get("data", {}).get("text", "") if isinstance(original_input, dict) else ""
            
            comprehensive_input = UserInput(
                id=f"msg_{uuid4().hex[:8]}",
                timestamp=datetime.utcnow(),
                session_id=self.session_id,
                type="user_input",
                data={
                    "text": f"{original_text}. Additional details: {combined_responses}",
                    "is_clarification_summary": True
                }
            )
            
            # Update workflow state to indicate we have enough information
            self.workflow_state["current_phase"] = "generation"
            self.workflow_state["needs_clarification"] = False
            self.workflow_state["user_input"] = comprehensive_input
            
            # Clear clarification responses from session
            session_data["clarification_responses"] = []
            await redis.set_session(self.session_id, session_data)
            
            # Continue to next phase
            await self._continue_workflow_after_clarification()
            
        except Exception as e:
            api_logger.error(f"Error processing accumulated clarifications: {e}", exc_info=True)
            await self._send_error("Error processing your responses. Please try again.")
    
    async def _continue_workflow_after_clarification(self):
        """Continue workflow after clarification is complete."""
        try:
            # Simulate structure creation and final steps
            await self._send_chat_message(
                message_type="info",
                content={
                    "message": "Creating presentation structure...",
                    "context": "Building your slides based on the information provided",
                    "options": None,
                    "question_id": None
                },
                progress=self._create_progress_update("generation", 70)
            )
            
            # Simulate processing time
            await asyncio.sleep(2)
            
            # Send completion
            await self._send_chat_message(
                message_type="info",
                content={
                    "message": "Your presentation is ready! 🎉",
                    "context": "Presentation generated successfully with all the details you provided",
                    "options": ["Download", "Edit", "Share"],
                    "question_id": None
                },
                progress=self._create_progress_update("completed", 100)
            )
            
            # Update final state
            self.workflow_state["current_phase"] = "completed"
            
        except Exception as e:
            api_logger.error(f"Error continuing workflow: {e}", exc_info=True)
            await self._send_error("Error completing presentation generation.")
    
    async def _send_natural_clarification_question(self):
        """Send a natural, conversational clarification question."""
        # Get session context to see what we've already asked
        redis = await get_redis()
        session_data = await redis.get_session(self.session_id) or {}
        clarifications = session_data.get("clarification_responses", [])
        questions_asked = session_data.get("questions_asked", [])
        
        # Determine what to ask based on what we haven't covered yet
        question_flow = [
            {
                "key": "audience",
                "question": "Who is your target audience? (e.g., kids, business professionals, students, etc.)",
                "context": "Understanding your audience helps me tailor the content and style appropriately."
            },
            {
                "key": "purpose", 
                "question": "What's the main goal of this presentation? What do you want your audience to understand or do?",
                "context": "Knowing the purpose helps me structure the content effectively."
            },
            {
                "key": "topic_detail",
                "question": "Can you tell me more about the specific topics or key points you want to cover?",
                "context": "This helps me create relevant and focused content."
            },
            {
                "key": "context",
                "question": "What's the setting for this presentation? (classroom, meeting, conference, etc.) And roughly how long should it be?",
                "context": "Context helps me recommend the right format and pacing."
            }
        ]
        
        # Find the next question to ask
        next_question = None
        for q in question_flow:
            if q["key"] not in questions_asked:
                next_question = q
                break
        
        if next_question:
            # Mark this question as asked
            questions_asked.append(next_question["key"])
            session_data["questions_asked"] = questions_asked
            await redis.set_session(self.session_id, session_data)
            
            await self._send_chat_message(
                message_type="question",
                content={
                    "message": next_question["question"],
                    "context": next_question["context"],
                    "options": None,
                    "question_id": next_question["key"]
                },
                progress=self._create_progress_update("clarification", 15 + len(questions_asked) * 15)
            )
        else:
            # We've asked all our key questions, process what we have
            await self._process_accumulated_clarifications()
    
    async def _handle_workflow_state(self):
        """Handle workflow state and send appropriate messages."""
        if not self.workflow_state:
            api_logger.warning("No workflow state to handle")
            return
        
        # ROUND 24 FIX: Handle both dict state and node output formats
        if isinstance(self.workflow_state, dict):
            # Check if this is a LangGraph node output (has node name as key)
            if len(self.workflow_state) == 1 and list(self.workflow_state.keys())[0] in ['analyze', 'clarify', 'structure', 'generate', 'assemble']:
                # This is a node output, extract the actual state
                node_name = list(self.workflow_state.keys())[0]
                node_state = self.workflow_state[node_name]
                api_logger.info(
                    f"🔍 ROUND 24 FIX: Extracted node state from '{node_name}'",
                    session_id=self.session_id,
                    node_state_keys=list(node_state.keys()) if isinstance(node_state, dict) else "Not a dict"
                )
                # Use the node state for phase detection
                phase = node_state.get("current_phase") if isinstance(node_state, dict) else None
                # Also update our workflow_state to use the extracted state
                if isinstance(node_state, dict):
                    self.workflow_state = node_state
            else:
                # Regular state dict
                phase = self.workflow_state.get("current_phase")
        else:
            phase = None
            
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
            # Send a simple, natural clarification question
            await self._send_natural_clarification_question()
        
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
        
        elif phase == "structure":
            # Send structure progress update
            api_logger.info(f"Handling structure phase", session_id=self.session_id)
            await self._send_chat_message(
                message_type="info",
                content={
                    "message": "Building presentation structure...",
                    "context": "Creating slide layouts and design",
                    "options": None,
                    "question_id": None
                },
                progress=self._create_progress_update("generation", 50)
            )
        
        elif phase == "complete" or phase == "completed":
            # Send final presentation
            api_logger.info(f"Handling complete phase", session_id=self.session_id)
            presentation = self.workflow_state.get("final_presentation")
            if presentation:
                # Mock presentation for testing
                mock_presentation = Presentation(
                    id=presentation.get("id", str(uuid4())),
                    title=presentation.get("title", "Your Presentation"),
                    description="Generated presentation",
                    theme_config={},
                    slides=[],
                    metadata={},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                await self._send_presentation(mock_presentation)
            else:
                await self._send_error("Presentation generation failed")
        
        else:
            api_logger.warning(
                f"Unknown workflow phase: {phase}",
                session_id=self.session_id,
                workflow_state_keys=list(self.workflow_state.keys())
            )
    
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
            # Check if auth is disabled for local development
            import os
            if os.getenv("DISABLE_AUTH", "false").lower() == "true":
                # Create fake token data for local testing
                from ..utils.auth import TokenData
                token_data = TokenData(
                    user_id="local_test_user",
                    email="test@localhost",
                    session_id=f"local_session_{uuid4().hex[:8]}"
                )
                api_logger.info("Auth bypassed for local development (DISABLE_AUTH=true)")
            else:
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