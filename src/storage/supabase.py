"""
Supabase client implementation for the presentation generator.
Handles all database operations including vector similarity search.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from uuid import UUID
import json
import asyncio
from functools import lru_cache

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
import numpy as np

from ..models.presentation import Presentation, Slide
from ..models.agents import WorkflowState, AgentTaskStatus
from ..utils.logger import storage_logger, log_execution_time, log_error


# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


class SupabaseStore:
    """Supabase storage client with vector search capabilities."""
    
    def __init__(self, use_service_key: bool = False):
        """
        Initialize Supabase client.
        
        Args:
            use_service_key: Use service key for admin operations
        """
        if not SUPABASE_URL:
            raise ValueError("SUPABASE_URL environment variable not set")
        
        key = SUPABASE_SERVICE_KEY if use_service_key else SUPABASE_ANON_KEY
        if not key:
            raise ValueError("Supabase key not found in environment")
        
        # Create client with custom options
        options = ClientOptions(
            auto_refresh_token=True,
            persist_session=True
        )
        
        self.client: Client = create_client(SUPABASE_URL, key, options)
        storage_logger.info("Supabase client initialized", url=SUPABASE_URL)
    
    # Session Management
    @log_execution_time("supabase.create_session")
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        expires_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            user_id: User ID
            expires_hours: Hours until session expires
            
        Returns:
            Created session data
        """
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        
        data = {
            "id": session_id,
            "user_id": user_id,
            "conversation_history": [],
            "current_state": {},
            "expires_at": expires_at.isoformat(),
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat()
            }
        }
        
        try:
            result = self.client.table("sessions").insert(data).execute()
            storage_logger.info(
                "Session created",
                session_id=session_id,
                user_id=user_id
            )
            return result.data[0]
        except Exception as e:
            log_error(e, "session_creation_failed", {"session_id": session_id})
            raise
    
    @log_execution_time("supabase.get_session")
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session by ID.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Session data or None if not found
        """
        try:
            result = self.client.table("sessions")\
                .select("*")\
                .eq("id", session_id)\
                .single()\
                .execute()
            
            if result.data:
                # Check if session is expired
                expires_at = datetime.fromisoformat(result.data["expires_at"].replace("Z", "+00:00"))
                if expires_at < datetime.now(timezone.utc):
                    storage_logger.warning("Session expired", session_id=session_id)
                    return None
                
                return result.data
            return None
        except Exception as e:
            storage_logger.error("Failed to get session", session_id=session_id, error=str(e))
            return None
    
    @log_execution_time("supabase.update_session")
    async def update_session(
        self,
        session_id: str,
        conversation_history: Optional[List[Dict]] = None,
        current_state: Optional[Dict] = None
    ) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session ID to update
            conversation_history: New conversation history
            current_state: New current state
            
        Returns:
            True if successful
        """
        update_data = {
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if conversation_history is not None:
            update_data["conversation_history"] = conversation_history
        
        if current_state is not None:
            update_data["current_state"] = current_state
        
        # Update last activity in metadata
        update_data["metadata"] = {
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            result = self.client.table("sessions")\
                .update(update_data)\
                .eq("id", session_id)\
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            log_error(e, "session_update_failed", {"session_id": session_id})
            return False
    
    # Presentation Management
    @log_execution_time("supabase.save_presentation")
    async def save_presentation(
        self,
        presentation: Presentation,
        session_id: str,
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Save presentation to database.
        
        Args:
            presentation: Presentation object
            session_id: Associated session ID
            embedding: Optional vector embedding
            
        Returns:
            Presentation ID
        """
        data = {
            "session_id": session_id,
            "title": presentation.title,
            "description": presentation.description,
            "structure": presentation.model_dump(),
            "presentation_type": presentation.metadata.get("presentation_type"),
            "industry": presentation.metadata.get("industry"),
            "target_audience": presentation.metadata.get("target_audience"),
            "metadata": presentation.metadata,
            "version": presentation.version
        }
        
        if embedding:
            data["embedding"] = embedding
        
        try:
            result = self.client.table("presentations").insert(data).execute()
            presentation_id = result.data[0]["id"]
            
            storage_logger.info(
                "Presentation saved",
                presentation_id=presentation_id,
                session_id=session_id,
                title=presentation.title
            )
            
            return presentation_id
        except Exception as e:
            log_error(e, "presentation_save_failed", {
                "session_id": session_id,
                "title": presentation.title
            })
            raise
    
    @log_execution_time("supabase.get_presentation")
    async def get_presentation(self, presentation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve presentation by ID.
        
        Args:
            presentation_id: Presentation ID
            
        Returns:
            Presentation data or None
        """
        try:
            result = self.client.table("presentations")\
                .select("*")\
                .eq("id", presentation_id)\
                .single()\
                .execute()
            
            return result.data
        except Exception as e:
            storage_logger.error(
                "Failed to get presentation",
                presentation_id=presentation_id,
                error=str(e)
            )
            return None
    
    @log_execution_time("supabase.find_similar_presentations")
    async def find_similar_presentations(
        self,
        embedding: List[float],
        threshold: float = 0.8,
        limit: int = 5,
        filter_type: Optional[str] = None,
        filter_industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar presentations using vector search.
        
        Args:
            embedding: Query embedding vector
            threshold: Similarity threshold (0-1)
            limit: Maximum results
            filter_type: Optional presentation type filter
            filter_industry: Optional industry filter
            
        Returns:
            List of similar presentations with similarity scores
        """
        try:
            # Call the RPC function for similarity search
            params = {
                "query_embedding": embedding,
                "match_threshold": threshold,
                "match_count": limit
            }
            
            if filter_type:
                params["filter_type"] = filter_type
            if filter_industry:
                params["filter_industry"] = filter_industry
            
            result = self.client.rpc("match_presentations", params).execute()
            
            storage_logger.info(
                "Similar presentations found",
                count=len(result.data),
                threshold=threshold
            )
            
            return result.data
        except Exception as e:
            log_error(e, "similarity_search_failed", {
                "threshold": threshold,
                "limit": limit
            })
            return []
    
    # Visual Assets Management
    @log_execution_time("supabase.save_visual_asset")
    async def save_visual_asset(
        self,
        presentation_id: str,
        slide_number: int,
        asset_type: str,
        url: str,
        prompt: Optional[str] = None,
        style_params: Optional[Dict] = None,
        embedding: Optional[List[float]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Save visual asset to database.
        
        Args:
            presentation_id: Associated presentation ID
            slide_number: Slide number
            asset_type: Type of asset (image, chart, diagram, icon)
            url: Asset URL
            prompt: Generation prompt if applicable
            style_params: Style parameters used
            embedding: Optional visual embedding
            tags: Asset tags
            
        Returns:
            Asset ID
        """
        data = {
            "presentation_id": presentation_id,
            "slide_number": slide_number,
            "asset_type": asset_type,
            "url": url,
            "prompt": prompt,
            "style_params": style_params or {},
            "tags": tags or [],
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        if embedding:
            data["embedding"] = embedding
        
        try:
            result = self.client.table("visual_assets").insert(data).execute()
            asset_id = result.data[0]["id"]
            
            storage_logger.info(
                "Visual asset saved",
                asset_id=asset_id,
                presentation_id=presentation_id,
                asset_type=asset_type
            )
            
            return asset_id
        except Exception as e:
            log_error(e, "visual_asset_save_failed", {
                "presentation_id": presentation_id,
                "asset_type": asset_type
            })
            raise
    
    @log_execution_time("supabase.find_similar_visual_assets")
    async def find_similar_visual_assets(
        self,
        embedding: List[float],
        asset_type: Optional[str] = None,
        threshold: float = 0.75,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar visual assets using vector search.
        
        Args:
            embedding: Query embedding vector
            asset_type: Optional asset type filter
            threshold: Similarity threshold
            limit: Maximum results
            
        Returns:
            List of similar assets
        """
        try:
            params = {
                "query_embedding": embedding,
                "match_threshold": threshold,
                "match_count": limit
            }
            
            if asset_type:
                params["asset_type_filter"] = asset_type
            
            result = self.client.rpc("match_visual_assets", params).execute()
            
            # Update usage count for returned assets
            asset_ids = [asset["id"] for asset in result.data]
            if asset_ids:
                self.client.table("visual_assets")\
                    .update({"usage_count": "usage_count + 1"})\
                    .in_("id", asset_ids)\
                    .execute()
            
            return result.data
        except Exception as e:
            log_error(e, "visual_similarity_search_failed", {
                "asset_type": asset_type,
                "threshold": threshold
            })
            return []
    
    # Agent Output Tracking
    @log_execution_time("supabase.save_agent_output")
    async def save_agent_output(
        self,
        session_id: str,
        agent_id: str,
        output_type: str,
        correlation_id: str,
        status: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        processing_time_ms: Optional[int] = None,
        tokens_used: Optional[Dict[str, int]] = None,
        error_message: Optional[str] = None
    ) -> str:
        """
        Save agent output for tracking and analysis.
        
        Returns:
            Output record ID
        """
        data = {
            "session_id": session_id,
            "agent_id": agent_id,
            "output_type": output_type,
            "correlation_id": correlation_id,
            "status": status,
            "input_data": input_data,
            "output_data": output_data,
            "processing_time_ms": processing_time_ms,
            "tokens_used": tokens_used,
            "error_message": error_message
        }
        
        try:
            result = self.client.table("agent_outputs").insert(data).execute()
            return result.data[0]["id"]
        except Exception as e:
            log_error(e, "agent_output_save_failed", {
                "session_id": session_id,
                "agent_id": agent_id
            })
            raise
    
    @log_execution_time("supabase.get_agent_outputs")
    async def get_agent_outputs(
        self,
        session_id: str,
        agent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve agent outputs for a session.
        
        Args:
            session_id: Session ID
            agent_id: Optional filter by agent
            correlation_id: Optional filter by correlation ID
            limit: Maximum results
            
        Returns:
            List of agent outputs
        """
        try:
            query = self.client.table("agent_outputs")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("created_at", desc=True)\
                .limit(limit)
            
            if agent_id:
                query = query.eq("agent_id", agent_id)
            
            if correlation_id:
                query = query.eq("correlation_id", correlation_id)
            
            result = query.execute()
            return result.data
        except Exception as e:
            storage_logger.error(
                "Failed to get agent outputs",
                session_id=session_id,
                error=str(e)
            )
            return []
    
    # Utility Methods
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            result = self.client.rpc("cleanup_expired_sessions").execute()
            count = len(result.data) if result.data else 0
            
            storage_logger.info("Expired sessions cleaned up", count=count)
            return count
        except Exception as e:
            log_error(e, "session_cleanup_failed")
            return 0
    
    async def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get usage statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Usage statistics
        """
        try:
            # Get presentation count
            presentations = self.client.table("presentations")\
                .select("id", count="exact")\
                .eq("sessions.user_id", user_id)\
                .execute()
            
            # Get total slides
            slides_query = """
            SELECT 
                COUNT(*) as total_slides,
                AVG(array_length(structure->'slides', 1)) as avg_slides_per_presentation
            FROM presentations p
            JOIN sessions s ON p.session_id = s.id
            WHERE s.user_id = %s
            """
            
            # Note: Direct SQL queries require service key
            # This is a simplified version
            
            return {
                "total_presentations": presentations.count or 0,
                "last_30_days": 0,  # Would need date filtering
                "total_visual_assets": 0,  # Would need join query
                "usage_trend": []  # Would need time series data
            }
        except Exception as e:
            log_error(e, "usage_stats_failed", {"user_id": user_id})
            return {
                "total_presentations": 0,
                "last_30_days": 0,
                "total_visual_assets": 0,
                "usage_trend": []
            }
    
    async def health_check(self) -> bool:
        """
        Check if Supabase connection is healthy.
        
        Returns:
            True if healthy
        """
        try:
            # Simple query to test connection
            result = self.client.table("sessions").select("id").limit(1).execute()
            return True
        except Exception:
            return False


# Singleton instance
_supabase_instance: Optional[SupabaseStore] = None


def get_supabase() -> SupabaseStore:
    """Get Supabase client instance."""
    global _supabase_instance
    
    if _supabase_instance is None:
        _supabase_instance = SupabaseStore()
    
    return _supabase_instance


# Export main components
__all__ = [
    'SupabaseStore',
    'get_supabase'
]