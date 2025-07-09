"""
A/B Testing Framework for Modular Prompt System
Manages deterministic assignment of sessions to test groups.
"""
import hashlib
from typing import Dict, Any
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ABTestManager:
    """Manage A/B testing for modular prompts"""
    
    def __init__(self, percentage: int = 0):
        """
        Initialize A/B test manager.
        
        Args:
            percentage: Percentage of sessions to use modular prompts (0-100)
        """
        self.percentage = min(max(percentage, 0), 100)  # Clamp to 0-100
        logger.info(f"ABTestManager initialized with {self.percentage}% modular assignment")
    
    def should_use_modular(self, session_id: str) -> bool:
        """
        Deterministically decide if session should use modular prompts.
        Uses consistent hashing to ensure same session always gets same assignment.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session should use modular prompts
        """
        if self.percentage == 0:
            return False
        if self.percentage == 100:
            return True
        
        # Use hash for consistent assignment
        hash_value = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        assigned_to_modular = (hash_value % 100) < self.percentage
        
        logger.debug(
            f"Session {session_id} assigned to {'modular' if assigned_to_modular else 'monolithic'} "
            f"prompts (hash_mod={hash_value % 100}, threshold={self.percentage})"
        )
        
        return assigned_to_modular
    
    def get_assignment_stats(self, session_ids: list[str]) -> Dict[str, Any]:
        """
        Get statistics about A/B test assignments for a list of sessions.
        
        Args:
            session_ids: List of session IDs to analyze
            
        Returns:
            Dictionary with assignment statistics
        """
        modular_count = sum(1 for sid in session_ids if self.should_use_modular(sid))
        total_count = len(session_ids)
        
        return {
            "total_sessions": total_count,
            "modular_sessions": modular_count,
            "monolithic_sessions": total_count - modular_count,
            "modular_percentage": (modular_count / total_count * 100) if total_count > 0 else 0,
            "expected_percentage": self.percentage
        }