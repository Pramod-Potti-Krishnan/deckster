"""
WebSocket handler for Deckster.
"""
import json
import asyncio
import random
from datetime import datetime
from typing import Dict, Any, List
from fastapi import WebSocket
from src.utils.logger import setup_logger
from src.agents.intent_router import IntentRouter
from src.agents.director import DirectorAgent
from src.utils.session_manager import SessionManager
from src.utils.message_packager import MessagePackager
from src.utils.streamlined_packager import StreamlinedMessagePackager
from src.storage.supabase import get_supabase_client
from src.models.agents import UserIntent, StateContext
from src.models.websocket_messages import StreamlinedMessage
from src.workflows.state_machine import WorkflowOrchestrator
from config.settings import get_settings

logger = setup_logger(__name__)


class WebSocketHandler:
    """Handles WebSocket connections and message routing."""
    
    def __init__(self):
        """Initialize handler components."""
        # Get settings
        self.settings = get_settings()
        
        # Initialize Supabase client
        self.supabase = get_supabase_client()
        
        # Initialize components
        self.intent_router = IntentRouter()
        self.director = DirectorAgent()
        self.sessions = SessionManager(self.supabase)
        self.packager = MessagePackager()
        self.streamlined_packager = StreamlinedMessagePackager()
        self.workflow = WorkflowOrchestrator()
        
        logger.info("WebSocketHandler initialized with streamlined protocol: %s", 
                   self.settings.USE_STREAMLINED_PROTOCOL)
    
    def _should_use_streamlined(self, session_id: str) -> bool:
        """
        Determine if this session should use streamlined protocol.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if streamlined protocol should be used
        """
        # If feature is disabled globally, always use old protocol
        if not self.settings.USE_STREAMLINED_PROTOCOL:
            return False
        
        # If percentage is 100, always use streamlined
        if self.settings.STREAMLINED_PROTOCOL_PERCENTAGE >= 100:
            return True
        
        # If percentage is 0, never use streamlined
        if self.settings.STREAMLINED_PROTOCOL_PERCENTAGE <= 0:
            return False
        
        # Use session ID for consistent A/B testing
        # Hash the session ID to get a number between 0-99
        hash_value = hash(session_id) % 100
        return hash_value < self.settings.STREAMLINED_PROTOCOL_PERCENTAGE
    
    async def _send_messages(self, websocket: WebSocket, messages: List[StreamlinedMessage]):
        """
        Send multiple streamlined messages with small delays.
        
        Args:
            websocket: WebSocket connection
            messages: List of streamlined messages to send
        """
        for i, message in enumerate(messages):
            await websocket.send_json(message.dict())
            
            # Add small delay between messages for better UX
            if i < len(messages) - 1:
                await asyncio.sleep(0.1)
    
    async def handle_connection(self, websocket: WebSocket, session_id: str):
        """
        Handle a WebSocket connection for a session.
        
        Args:
            websocket: The WebSocket connection
            session_id: The session ID from query parameter
        """
        try:
            # Get or create session
            session = await self.sessions.get_or_create(session_id)
            logger.info(f"Session {session_id} initialized with state: {session.current_state}")
            
            # Send initial greeting if new session
            if session.current_state == "PROVIDE_GREETING":
                await self._send_greeting(websocket, session)
            
            # Main message loop
            while True:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                logger.debug(f"Received message for session {session_id}: {message.get('type')}")
                
                # Process message
                await self._handle_message(websocket, session, message)
                
        except Exception as e:
            logger.error(f"Error in WebSocket handler for session {session_id}: {str(e)}", exc_info=True)
            await websocket.close()
    
    async def _send_greeting(self, websocket: WebSocket, session: Any):
        """Send initial greeting message."""
        try:
            use_streamlined = self._should_use_streamlined(session.id)
            logger.info(f"Session {session.id} using streamlined protocol: {use_streamlined}")
            
            if use_streamlined:
                # Use streamlined protocol
                messages = self.streamlined_packager.package_messages(
                    session_id=session.id,
                    state="PROVIDE_GREETING",
                    agent_output=None,  # Greeting doesn't need agent output
                    context=None
                )
                await self._send_messages(websocket, messages)
            else:
                # Use legacy protocol
                state_context = StateContext(
                    current_state="PROVIDE_GREETING",
                    user_intent=None,  # No intent for greeting
                    conversation_history=[],
                    session_data={}
                )
                
                # Get greeting from director
                greeting = await self.director.process(state_context)
                
                # Package and send
                message = self.packager.package(
                    response=greeting,
                    session_id=session.id,
                    current_state="PROVIDE_GREETING"
                )
                
                await websocket.send_json(message)
            
            logger.info(f"Sent greeting for session {session.id}")
            
        except Exception as e:
            logger.error(f"Error sending greeting: {str(e)}")
    
    async def _handle_message(self, websocket: WebSocket, session: Any, message: Dict[str, Any]):
        """
        Handle an incoming message.
        
        Args:
            websocket: The WebSocket connection
            session: The session object
            message: The incoming message
        """
        try:
            # Extract user input
            user_input = message.get('data', {}).get('text', '')
            
            # STEP 1: Classify user intent - all messages go through the router
            intent = await self.intent_router.classify(
                user_message=user_input,
                context={
                    'current_state': session.current_state,
                    'recent_history': session.conversation_history[-3:] if session.conversation_history else []
                }
            )
            
            logger.info(f"Classified intent: {intent.intent_type} with confidence {intent.confidence}")
            
            # STEP 2: Handle intent-based actions
            if intent.intent_type == "Change_Topic":
                # Clear context and reset to questions
                await self.sessions.clear_context(session.id)
                session = await self.sessions.get_or_create(session.id)  # Refresh session
                session.current_state = "ASK_CLARIFYING_QUESTIONS"
                # extracted_info now contains the new topic as a string
                session.user_initial_request = intent.extracted_info or user_input
            
            elif intent.intent_type == "Change_Parameter":
                # Update specific parameters without full reset
                # For now, we'll need to parse the parameter from the user input
                # since extracted_info is now a string
                parameters = {}
                if intent.extracted_info:
                    # Simple parsing - could be improved
                    if "audience" in intent.extracted_info.lower():
                        parameters["audience"] = intent.extracted_info
                    elif "slide" in intent.extracted_info.lower():
                        parameters["slide_count"] = intent.extracted_info
                await self.sessions.update_parameters(session.id, parameters)
                session = await self.sessions.get_or_create(session.id)  # Refresh session
            
            elif intent.intent_type == "Submit_Initial_Topic":
                # Save the initial topic
                await self.sessions.save_session_data(
                    session.id,
                    'user_initial_request',
                    user_input
                )
                logger.info(f"Saved initial topic for session {session.id}: {user_input}")
                session = await self.sessions.get_or_create(session.id)  # Refresh session
                logger.debug(f"After refresh - user_initial_request: {session.user_initial_request}")
                
            elif intent.intent_type == "Submit_Clarification_Answers":
                # Save clarifying answers
                await self.sessions.save_session_data(
                    session.id,
                    'clarifying_answers',
                    {
                        "raw_answers": user_input,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                logger.info(f"Saved clarifying answers for session {session.id}")
                session = await self.sessions.get_or_create(session.id)  # Refresh session
            
            # STEP 3: Determine next state BEFORE processing (for intent-based routing)
            logger.info(f"Determining next state: current={session.current_state}, intent={intent.intent_type}")
            next_state = self._determine_next_state(
                session.current_state, 
                intent, 
                None,  # No response yet
                session  # Pass session to check if questions have been asked
            )
            logger.info(f"Next state determined: {next_state}")
            
            # Update state if it changed
            if next_state != session.current_state:
                logger.info(f"Pre-processing state change: {session.current_state} -> {next_state}")
                await self.sessions.update_state(session.id, next_state)
                session.current_state = next_state
            else:
                logger.info(f"State remains: {session.current_state}")
            
            # STEP 4: Build state context with the NEW state
            logger.debug(f"Building StateContext - user_initial_request: {session.user_initial_request}")
            state_context = StateContext(
                current_state=session.current_state,
                user_intent=intent,
                conversation_history=session.conversation_history or [],
                session_data={
                    'user_initial_request': session.user_initial_request,
                    'clarifying_answers': session.clarifying_answers,
                    'confirmation_plan': session.confirmation_plan,
                    'presentation_strawman': session.presentation_strawman
                }
            )
            
            # STEP 4.5: Send pre-generation status for long-running states
            use_streamlined = self._should_use_streamlined(session.id)
            if use_streamlined and session.current_state in ["GENERATE_STRAWMAN", "REFINE_STRAWMAN"]:
                pre_status = self.streamlined_packager.create_pre_generation_status(
                    session_id=session.id,
                    state=session.current_state
                )
                await websocket.send_json(pre_status.dict())
                await asyncio.sleep(0.1)  # Small delay before processing
            
            # STEP 5: Process with Director based on NEW state and intent
            response = await self.director.process(state_context)
            
            # Store in history
            await self.sessions.add_to_history(session.id, {
                'role': 'user',
                'content': user_input,
                'intent': intent.dict()
            })
            await self.sessions.add_to_history(session.id, {
                'role': 'assistant',
                'state': session.current_state,
                'content': response
            })
            
            # Package and send response based on protocol
            use_streamlined = self._should_use_streamlined(session.id)
            
            if use_streamlined:
                # Use streamlined protocol
                messages = self.streamlined_packager.package_messages(
                    session_id=session.id,
                    state=session.current_state,
                    agent_output=response,
                    context=state_context
                )
                await self._send_messages(websocket, messages)
            else:
                # Use legacy protocol
                ws_message = self.packager.package(
                    response=response,
                    session_id=session.id,
                    current_state=session.current_state
                )
                await websocket.send_json(ws_message)
            
            logger.info(f"Sent response for session {session.id} in state {session.current_state}")
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            # Send error message based on protocol
            use_streamlined = self._should_use_streamlined(session.id)
            
            if use_streamlined:
                error_messages = self.streamlined_packager.create_error_message(
                    session_id=session.id,
                    error_text=str(e)
                )
                await self._send_messages(websocket, error_messages)
            else:
                error_message = self.packager.package_error(
                    error=str(e),
                    session_id=session.id
                )
                await websocket.send_json(error_message)
    
    def _determine_next_state(self, current_state: str, intent: UserIntent, 
                             response: Any, session: Any = None) -> str:
        """
        Determine next state based on directional intent.
        Each intent now unambiguously implies the next state.
        
        Args:
            current_state: Current workflow state
            intent: Classified user intent
            response: Response from director (can be None for pre-processing)
            session: Session object to check state details
            
        Returns:
            Next state name
        """
        # Map directional intents to next states
        intent_to_next_state = {
            "Submit_Initial_Topic": "ASK_CLARIFYING_QUESTIONS",
            "Submit_Clarification_Answers": "CREATE_CONFIRMATION_PLAN",
            "Accept_Plan": "GENERATE_STRAWMAN",
            "Reject_Plan": "CREATE_CONFIRMATION_PLAN",  # Loop back
            "Accept_Strawman": current_state,  # Stay in current (effectively END)
            "Submit_Refinement_Request": "REFINE_STRAWMAN",
            "Change_Topic": "ASK_CLARIFYING_QUESTIONS",  # Reset
            "Change_Parameter": "CREATE_CONFIRMATION_PLAN",  # Regenerate
            "Ask_Help_Or_Question": current_state  # No state change
        }
        
        # Get next state from mapping
        next_state = intent_to_next_state.get(intent.intent_type, current_state)
        
        # Log the transition
        if next_state != current_state:
            logger.info(f"State transition: {current_state} -> {next_state} (intent: {intent.intent_type})")
        else:
            logger.info(f"State remains: {current_state} (intent: {intent.intent_type})")
            
        return next_state