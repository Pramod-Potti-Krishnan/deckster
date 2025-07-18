"""
Session management for Deckster.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from supabase import Client
from src.models.session import Session
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SessionManager:
    """Manages session CRUD operations with Supabase."""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize session manager.
        
        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client
        self.table_name = "sessions"
        self.cache: Dict[str, Session] = {}  # Local cache for performance
    
    async def get_or_create(self, session_id: str, user_id: str) -> Session:
        """
        Get or create a session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            Session object
        """
        print(f"[DEBUG SessionManager] get_or_create called with session_id={session_id}, user_id={user_id}")
        
        # Check cache first
        cache_key = f"{user_id}:{session_id}"
        if cache_key in self.cache:
            print(f"[DEBUG SessionManager] Found in cache: {cache_key}")
            logger.debug(f"Returning cached session {session_id} for user {user_id}")
            return self.cache[cache_key]
        
        # Try to fetch from Supabase
        print("[DEBUG SessionManager] Checking Supabase for existing session")
        try:
            result = self.supabase.table(self.table_name).select("*").eq("id", session_id).eq("user_id", user_id).execute()
            print(f"[DEBUG SessionManager] Supabase query result: {result}")
            
            if result.data:
                # Session exists
                session_data = result.data[0]
                logger.debug(f"Session data from DB: {session_data}")
                session = Session(**session_data)
                self.cache[cache_key] = session
                logger.info(f"Retrieved existing session {session_id} for user {user_id}")
                logger.debug(f"Session user_initial_request: {session.user_initial_request}")
                return session
        except Exception as e:
            logger.warning(f"Error fetching session {session_id}: {str(e)}")
        
        # Create new session
        session = Session(
            id=session_id,
            user_id=user_id,
            current_state="PROVIDE_GREETING",
            conversation_history=[],
            user_initial_request=None,
            clarifying_answers=None,
            confirmation_plan=None,
            presentation_strawman=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to Supabase
        try:
            # Convert datetime to ISO format for JSON serialization
            session_data = session.dict()
            session_data['created_at'] = session.created_at.isoformat()
            session_data['updated_at'] = session.updated_at.isoformat()
            
            result = self.supabase.table(self.table_name).insert(session_data).execute()
            logger.info(f"Created new session {session_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Error creating session in Supabase: {str(e)}")
            # Continue with local session even if Supabase fails
        
        self.cache[cache_key] = session
        return session
    
    async def update_state(self, session_id: str, user_id: str, state: str):
        """
        Update session state.
        
        Args:
            session_id: Session ID
            user_id: User ID
            state: New state
        """
        session = await self.get_or_create(session_id, user_id)
        session.current_state = state
        session.updated_at = datetime.utcnow()
        
        # Update in Supabase
        try:
            self.supabase.table(self.table_name).update({
                'current_state': state,
                'updated_at': session.updated_at.isoformat()
            }).eq('id', session_id).eq('user_id', user_id).execute()
            logger.info(f"Updated session {session_id} state to {state}")
            
            # Force refresh from database to ensure cache consistency
            cache_key = f"{user_id}:{session_id}"
            if cache_key in self.cache:
                del self.cache[cache_key]
                logger.debug(f"Cleared cache for session {session_id} after state update")
                
        except Exception as e:
            logger.error(f"Error updating session state: {str(e)}")
    
    async def add_to_history(self, session_id: str, user_id: str, message: Dict[str, Any]):
        """
        Add message to conversation history.
        
        Args:
            session_id: Session ID
            user_id: User ID
            message: Message to add
        """
        session = await self.get_or_create(session_id, user_id)
        
        # Convert Pydantic objects to dict if needed
        if hasattr(message.get('content'), 'dict'):
            message['content'] = message['content'].dict()
        
        session.conversation_history.append(message)
        session.updated_at = datetime.utcnow()
        
        # Update in Supabase
        try:
            self.supabase.table(self.table_name).update({
                'conversation_history': session.conversation_history,
                'updated_at': session.updated_at.isoformat()
            }).eq('id', session_id).eq('user_id', user_id).execute()
            logger.debug(f"Added message to session {session_id} history")
        except Exception as e:
            logger.error(f"Error updating conversation history: {str(e)}")
    
    async def clear_context(self, session_id: str, user_id: str):
        """
        Clear session context for topic change.
        
        Args:
            session_id: Session ID
            user_id: User ID
        """
        session = await self.get_or_create(session_id, user_id)
        
        # Clear relevant fields
        session.user_initial_request = None
        session.clarifying_answers = None
        session.confirmation_plan = None
        session.presentation_strawman = None
        session.refinement_feedback = None
        session.conversation_history = []  # Clear history for fresh start
        session.updated_at = datetime.utcnow()
        
        # Update in Supabase
        try:
            self.supabase.table(self.table_name).update({
                'user_initial_request': None,
                'clarifying_answers': None,
                'confirmation_plan': None,
                'presentation_strawman': None,
                'refinement_feedback': None,
                'conversation_history': [],
                'updated_at': session.updated_at.isoformat()
            }).eq('id', session_id).eq('user_id', user_id).execute()
            logger.info(f"Cleared context for session {session_id}")
        except Exception as e:
            logger.error(f"Error clearing session context: {str(e)}")
    
    async def update_parameters(self, session_id: str, user_id: str, parameters: Dict[str, Any]):
        """
        Update specific parameters without full reset.
        
        Args:
            session_id: Session ID
            user_id: User ID
            parameters: Parameters to update
        """
        session = await self.get_or_create(session_id, user_id)
        
        # Update specific fields based on parameters
        if 'audience' in parameters and session.clarifying_answers:
            session.clarifying_answers['audience'] = parameters['audience']
        
        if 'slide_count' in parameters and session.confirmation_plan:
            session.confirmation_plan['proposed_slide_count'] = parameters['slide_count']
        
        session.updated_at = datetime.utcnow()
        
        # Update in Supabase
        try:
            updates = {
                'updated_at': session.updated_at.isoformat()
            }
            if session.clarifying_answers:
                updates['clarifying_answers'] = session.clarifying_answers
            if session.confirmation_plan:
                updates['confirmation_plan'] = session.confirmation_plan
            
            self.supabase.table(self.table_name).update(updates).eq('id', session_id).eq('user_id', user_id).execute()
            logger.info(f"Updated parameters for session {session_id}")
            
            # Force refresh from database to ensure cache consistency
            cache_key = f"{user_id}:{session_id}"
            if cache_key in self.cache:
                del self.cache[cache_key]
                logger.debug(f"Cleared cache for session {session_id} after parameter update")
                
        except Exception as e:
            logger.error(f"Error updating session parameters: {str(e)}")
    
    async def save_session_data(self, session_id: str, user_id: str, field: str, data: Any):
        """
        Save specific session data field.
        
        Args:
            session_id: Session ID
            user_id: User ID
            field: Field name to update
            data: Data to save
        """
        session = await self.get_or_create(session_id, user_id)
        
        # Update field
        if hasattr(session, field):
            setattr(session, field, data)
            session.updated_at = datetime.utcnow()
            
            # Update in Supabase
            try:
                self.supabase.table(self.table_name).update({
                    field: data,
                    'updated_at': session.updated_at.isoformat()
                }).eq('id', session_id).eq('user_id', user_id).execute()
                logger.info(f"Saved {field} for session {session_id}")
                
                # Force refresh from database to ensure cache consistency
                # Remove from cache to force fresh read
                cache_key = f"{user_id}:{session_id}"
                if cache_key in self.cache:
                    del self.cache[cache_key]
                    logger.debug(f"Cleared cache for session {session_id} after save")
                    
            except Exception as e:
                logger.error(f"Error saving session data: {str(e)}")