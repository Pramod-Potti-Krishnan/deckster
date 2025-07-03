"""
Models module for the presentation generator.
Defines all data structures and message formats.
"""

from .messages import (
    BaseMessage, UserInput, DirectorMessage, AgentMessage,
    SystemMessage, ConnectionMessage, ClarificationRound,
    ClarificationResponse, PresentationRequest, DirectorResponse,
    validate_message
)
from .presentation import (
    Presentation, Slide, ComponentSpec, LayoutType,
    ComponentType, ChartType, DiagramType, Theme
)
from .agents import (
    AgentOutput, DirectorInboundOutput, DirectorOutboundOutput,
    UXArchitectOutput, ResearcherOutput, VisualDesignerOutput,
    DataAnalystOutput, UXAnalystOutput, WorkflowState
)

__all__ = [
    # Messages
    'BaseMessage', 'UserInput', 'DirectorMessage', 'AgentMessage',
    'SystemMessage', 'ConnectionMessage', 'ClarificationRound',
    'ClarificationResponse', 'PresentationRequest', 'DirectorResponse',
    'validate_message',
    
    # Presentation
    'Presentation', 'Slide', 'ComponentSpec', 'LayoutType',
    'ComponentType', 'ChartType', 'DiagramType', 'Theme',
    
    # Agents
    'AgentOutput', 'DirectorInboundOutput', 'DirectorOutboundOutput',
    'UXArchitectOutput', 'ResearcherOutput', 'VisualDesignerOutput',
    'DataAnalystOutput', 'UXAnalystOutput', 'WorkflowState'
]