"""
Main LangGraph workflow for presentation generation.
Orchestrates the flow between different agents.
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated, Sequence
from datetime import datetime
import operator
import asyncio
from uuid import uuid4

# Make langgraph optional
try:
    from langgraph import StateGraph, END
    from langgraph.prebuilt import ToolExecutor, ToolInvocation
    from langgraph.graph import Graph
    LANGGRAPH_AVAILABLE = True
    logger.info("✅ LangGraph successfully imported - Full workflow orchestration available")
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    logger.warning(f"⚠️  LangGraph import failed: {e} - Using simplified workflow")
    # Define fallback constants
    END = "END"
    class StateGraph: pass
    class ToolExecutor: pass
    class ToolInvocation: pass
    class Graph: pass

from ..models.messages import (
    UserInput, PresentationRequest, ClarificationRound,
    ClarificationResponse, DirectorMessage
)
from ..models.presentation import Presentation
from ..models.agents import WorkflowState as WorkflowStateModel, AgentTaskStatus
from ..agents.director_in import DirectorInboundAgent
from ..utils.logger import logger, set_request_id, set_session_id


# State definition
class WorkflowState(TypedDict):
    """State for the presentation generation workflow."""
    # Request information
    request_id: str
    session_id: str
    user_id: str
    correlation_id: str
    
    # User interaction
    user_input: UserInput
    presentation_request: Optional[PresentationRequest]
    clarification_rounds: Annotated[List[ClarificationRound], operator.add]
    clarification_responses: Annotated[List[ClarificationResponse], operator.add]
    
    # Agent outputs
    requirement_analysis: Optional[Dict[str, Any]]
    presentation_structure: Optional[Dict[str, Any]]
    layouts: Optional[List[Dict[str, Any]]]
    research_findings: Optional[Dict[str, Any]]
    visual_assets: Optional[List[Dict[str, Any]]]
    charts: Optional[List[Dict[str, Any]]]
    diagrams: Optional[List[Dict[str, Any]]]
    
    # Final output
    final_presentation: Optional[Presentation]
    
    # Workflow control
    current_phase: str  # "analysis", "clarification", "generation", "assembly"
    needs_clarification: bool
    active_agents: List[str]
    completed_agents: List[str]
    agent_errors: Dict[str, str]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    processing_time_ms: int


# Node functions
async def analyze_request(state: WorkflowState) -> Dict[str, Any]:
    """Analyze user request using Director Inbound."""
    logger.info(
        "Analyzing user request",
        session_id=state["session_id"],
        request_id=state["request_id"]
    )
    
    # Set context for logging
    set_request_id(state["request_id"])
    set_session_id(state["session_id"])
    
    # Debug logging
    logger.debug(
        "analyze_request starting",
        session_id=state["session_id"],
        has_user_input=state.get("user_input") is not None
    )
    
    # Initialize Director agent
    director = DirectorInboundAgent()
    
    # Create agent context
    from ..agents.base import AgentContext
    context = AgentContext(
        session_id=state["session_id"],
        correlation_id=state["correlation_id"],
        request_id=state["request_id"],
        user_id=state["user_id"]
    )
    
    # Debug before execute
    logger.debug(
        "Calling director.execute",
        session_id=state["session_id"],
        action="analyze_request",
        user_input_type=type(state["user_input"]).__name__
    )
    
    # Execute analysis
    result = await director.execute(
        action="analyze_request",
        parameters={"user_input": state["user_input"].model_dump(mode='json')},
        context=context
    )
    
    # Debug after execute
    logger.debug(
        "Director execute returned",
        session_id=state["session_id"],
        result_type=type(result).__name__,
        output_type=result.output_type if result else None,
        has_analysis=result.analysis is not None if result else False,
        has_clarification_questions=result.clarification_questions is not None if result else False,
        clarification_questions_type=type(result.clarification_questions).__name__ if result and result.clarification_questions is not None else "None"
    )
    
    # Update state based on result
    updates = {
        "requirement_analysis": result.analysis.model_dump(mode='json') if result.analysis else None,
        "updated_at": datetime.utcnow()
    }
    
    if result.output_type == "greeting":
        # Handle greeting response - just store it, don't change phase
        updates["needs_clarification"] = False
        updates["current_phase"] = "greeting"
        updates["greeting_response"] = result.greeting_response
    elif result.output_type == "clarification":
        updates["needs_clarification"] = True
        updates["current_phase"] = "clarification"
        if result.clarification_questions:
            updates["clarification_rounds"] = [ClarificationRound(
                questions=result.clarification_questions
            )]
    else:
        updates["needs_clarification"] = False
        updates["current_phase"] = "generation"
        updates["presentation_structure"] = result.initial_structure
        updates["active_agents"] = result.next_agents
    
    return updates


async def generate_clarifications(state: WorkflowState) -> Dict[str, Any]:
    """Generate clarification questions."""
    logger.info(
        "Generating clarification questions",
        session_id=state["session_id"],
        round=len(state.get("clarification_rounds", []))
    )
    
    # This is handled by analyze_request in our implementation
    # Just update phase
    return {
        "current_phase": "clarification",
        "updated_at": datetime.utcnow()
    }


async def process_clarification_response(state: WorkflowState) -> Dict[str, Any]:
    """Process user's clarification response."""
    logger.info(
        "Processing clarification response",
        session_id=state["session_id"]
    )
    
    # Get latest response
    if not state.get("clarification_responses"):
        return {"updated_at": datetime.utcnow()}
    
    latest_response = state["clarification_responses"][-1]
    
    # Process through Director
    director = DirectorInboundAgent()
    context = AgentContext(
        session_id=state["session_id"],
        correlation_id=state["correlation_id"],
        request_id=state["request_id"],
        user_id=state["user_id"]
    )
    
    result = await director.execute(
        action="process_clarification_response",
        parameters={"response": latest_response.model_dump(mode='json')},
        context=context
    )
    
    # Update state
    updates = {"updated_at": datetime.utcnow()}
    
    if result.output_type == "clarification":
        # Need more clarifications
        updates["clarification_rounds"] = [ClarificationRound(
            questions=result.clarification_questions
        )]
    else:
        # Ready to proceed
        updates["needs_clarification"] = False
        updates["current_phase"] = "generation"
        updates["presentation_structure"] = result.initial_structure
        updates["active_agents"] = result.next_agents
    
    return updates


async def create_structure(state: WorkflowState) -> Dict[str, Any]:
    """Create presentation structure if not already created."""
    logger.info(
        "Creating presentation structure",
        session_id=state["session_id"]
    )
    
    if state.get("presentation_structure"):
        # Already have structure
        return {"updated_at": datetime.utcnow()}
    
    # Create structure using Director
    director = DirectorInboundAgent()
    context = AgentContext(
        session_id=state["session_id"],
        correlation_id=state["correlation_id"],
        request_id=state["request_id"],
        user_id=state["user_id"]
    )
    
    # Gather all requirements
    requirements = {
        "user_input": state["user_input"].model_dump(mode='json'),
        "analysis": state.get("requirement_analysis", {}),
        "clarifications": [
            {
                "questions": round.questions,
                "responses": response.responses
            }
            for round, response in zip(
                state.get("clarification_rounds", []),
                state.get("clarification_responses", [])
            )
        ]
    }
    
    result = await director.execute(
        action="create_structure",
        parameters={"requirements": requirements},
        context=context
    )
    
    return {
        "presentation_structure": result.initial_structure,
        "active_agents": result.next_agents,
        "current_phase": "generation",
        "updated_at": datetime.utcnow()
    }


async def run_parallel_agents(state: WorkflowState) -> Dict[str, Any]:
    """Run multiple agents in parallel."""
    logger.info(
        "Running parallel agents",
        session_id=state["session_id"],
        agents=state.get("active_agents", [])
    )
    
    # For Phase 1, we only have Director implemented
    # This is a placeholder for future agent execution
    
    updates = {
        "completed_agents": state.get("active_agents", []),
        "current_phase": "assembly",
        "updated_at": datetime.utcnow()
    }
    
    # Simulate agent outputs for now
    if "ux_architect" in state.get("active_agents", []):
        updates["layouts"] = [{
            "slide_number": i,
            "layout_type": "content",
            "grid_areas": []
        } for i in range(1, 11)]
    
    if "researcher" in state.get("active_agents", []):
        updates["research_findings"] = {
            "findings": ["Sample finding 1", "Sample finding 2"],
            "sources": []
        }
    
    return updates


async def assemble_presentation(state: WorkflowState) -> Dict[str, Any]:
    """Assemble final presentation from all agent outputs."""
    logger.info(
        "Assembling final presentation",
        session_id=state["session_id"]
    )
    
    # Create presentation from structure and agent outputs
    structure = state.get("presentation_structure", {})
    
    # Build presentation object
    from ..models.presentation import (
        Presentation, Slide, Theme, ColorPalette,
        Typography, PresentationSettings
    )
    
    # Create theme
    theme = Theme(
        name="default",
        colors=ColorPalette(
            primary="#0066CC",
            secondary="#4D94FF",
            accent="#FF6B6B",
            background="#FFFFFF",
            text="#333333",
            text_secondary="#666666"
        ),
        typography=Typography(
            heading_font="Arial",
            body_font="Arial",
            base_size=16
        )
    )
    
    # Create slides
    slides = []
    for i, outline in enumerate(structure.get("slide_outlines", []), 1):
        slide = Slide(
            slide_number=i,
            title=outline.get("title", f"Slide {i}"),
            layout_type=outline.get("layout_type", "content"),
            components=[],  # Would be populated by agents
            speaker_notes=outline.get("notes", "")
        )
        slides.append(slide)
    
    # Create presentation
    presentation = Presentation(
        title=structure.get("title", "Untitled Presentation"),
        subtitle=structure.get("subtitle"),
        description=structure.get("description"),
        slides=slides,
        theme=theme,
        settings=PresentationSettings(),
        metadata={
            "session_id": state["session_id"],
            "created_by": "AI Assistant",
            "generation_time_ms": state.get("processing_time_ms", 0)
        }
    )
    
    return {
        "final_presentation": presentation,
        "current_phase": "completed",
        "updated_at": datetime.utcnow()
    }


# Conditional edge functions
def should_clarify(state: WorkflowState) -> str:
    """Determine if clarification is needed."""
    if state.get("needs_clarification", False):
        return "clarify"
    return "structure"


def should_continue_clarifying(state: WorkflowState) -> str:
    """Determine if more clarification is needed."""
    if state.get("needs_clarification", False):
        return "clarify"
    return "structure"


def all_agents_complete(state: WorkflowState) -> str:
    """Check if all agents have completed."""
    active = set(state.get("active_agents", []))
    completed = set(state.get("completed_agents", []))
    
    if active.issubset(completed):
        return "assemble"
    return "wait"


# Mock workflow for when LangGraph is not available
class MockWorkflow:
    """Mock workflow implementation for Phase 1 without LangGraph."""
    
    def _is_recoverable_error(self, error: Exception) -> bool:
        """Determine if an error is recoverable and workflow should continue."""
        # RLS policy violations are recoverable (non-critical)
        if "row-level security policy" in str(error).lower():
            return True
        
        # Validation errors might be recoverable
        if "ValidationError" in str(type(error)):
            return True
        
        # Network/timeout errors are recoverable
        if any(error_type in str(type(error)) for error_type in [
            "TimeoutError", "ConnectionError", "HTTPError", "RequestException"
        ]):
            return True
        
        # Import/module errors are usually not recoverable
        if any(error_type in str(type(error)) for error_type in [
            "ImportError", "ModuleNotFoundError", "AttributeError"
        ]):
            return False
        
        # Default to recoverable for other errors
        return True
    
    async def astream(self, state: WorkflowState, config=None):
        """Mock async stream that just runs analyze_request."""
        logger.info(
            "Running mock workflow (LangGraph not available)",
            session_id=state.get("session_id"),
            request_id=state.get("request_id"),
            current_phase=state.get("current_phase")
        )
        
        # Debug logging for initial state
        logger.debug(
            "MockWorkflow initial state",
            session_id=state.get("session_id"),
            has_user_input=state.get("user_input") is not None,
            state_keys=list(state.keys())
        )
        
        # Just run the analyze step for Phase 1
        try:
            logger.debug("MockWorkflow calling analyze_request")
            updates = await analyze_request(state)
            
            # Debug logging for updates
            logger.debug(
                "MockWorkflow analyze_request returned",
                session_id=state.get("session_id"),
                updates_keys=list(updates.keys()) if updates else [],
                needs_clarification=updates.get("needs_clarification") if updates else None,
                current_phase=updates.get("current_phase") if updates else None
            )
            
            state.update(updates)
            yield state
        except Exception as e:
            logger.error(
                f"Mock workflow error: {type(e).__name__}: {str(e)}",
                session_id=state.get("session_id"),
                error_type=type(e).__name__,
                error_message=str(e),
                current_phase=state.get("current_phase", "unknown"),
                exc_info=True
            )
            
            # Determine if this is a recoverable error
            error_count = state.get("error_count", 0) + 1
            max_retries = 3
            
            if error_count < max_retries and self._is_recoverable_error(e):
                # Recoverable error - retry with error state but continue workflow
                logger.info(
                    f"Recoverable error encountered (attempt {error_count}/{max_retries}), continuing workflow",
                    session_id=state.get("session_id"),
                    error_type=type(e).__name__
                )
                state.update({
                    "current_phase": "error_recovery",
                    "error_count": error_count,
                    "last_error": {
                        "type": type(e).__name__,
                        "message": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    "can_retry": True,
                    "updated_at": datetime.utcnow()
                })
            else:
                # Non-recoverable error or max retries exceeded
                logger.error(
                    f"Non-recoverable error or max retries exceeded ({error_count}/{max_retries})",
                    session_id=state.get("session_id"),
                    error_type=type(e).__name__
                )
                state.update({
                    "current_phase": "error",
                    "error_count": error_count,
                    "agent_errors": {"workflow": str(e)},
                    "can_retry": False,
                    "updated_at": datetime.utcnow()
                })
            
            yield state


# Build the graph
def create_workflow() -> Graph:
    """Create the main workflow graph."""
    if not LANGGRAPH_AVAILABLE:
        logger.warning(
            "LangGraph not available - using MockWorkflow. Install langgraph for full functionality.",
            langgraph_available=LANGGRAPH_AVAILABLE
        )
        # Return a mock workflow when LangGraph is not installed
        return MockWorkflow()
    
    logger.info("🚀 Creating REAL LangGraph workflow with full orchestration")
    
    # Initialize workflow
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_request)
    workflow.add_node("clarify", generate_clarifications)
    workflow.add_node("process_response", process_clarification_response)
    workflow.add_node("structure", create_structure)
    workflow.add_node("generate", run_parallel_agents)
    workflow.add_node("assemble", assemble_presentation)
    
    logger.info("✅ Added all workflow nodes successfully")
    
    # Add edges
    workflow.set_entry_point("analyze")
    
    # Conditional routing after analysis
    workflow.add_conditional_edges(
        "analyze",
        should_clarify,
        {
            "clarify": "clarify",
            "structure": "structure"
        }
    )
    
    # Clarification loop
    workflow.add_edge("clarify", END)  # Frontend will handle response
    workflow.add_edge("process_response", "analyze")  # Re-analyze with new info
    
    # Generation flow
    workflow.add_edge("structure", "generate")
    workflow.add_edge("generate", "assemble")
    workflow.add_edge("assemble", END)
    
    logger.info("✅ Configured all workflow edges and conditions")
    
    # Compile workflow
    compiled = workflow.compile()
    logger.info(f"✅ Successfully compiled LangGraph workflow: {type(compiled).__name__}")
    
    return compiled


# Workflow runner
class WorkflowRunner:
    """Helper class to run the workflow."""
    
    def __init__(self):
        self.workflow = create_workflow()
    
    async def start_generation(
        self,
        user_input: UserInput,
        session_id: str,
        user_id: str
    ) -> WorkflowState:
        """Start a new presentation generation workflow."""
        # Create initial state
        initial_state: WorkflowState = {
            "request_id": f"req_{uuid4().hex[:12]}",
            "session_id": session_id,
            "user_id": user_id,
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
            "charts": None,
            "diagrams": None,
            "final_presentation": None,
            "current_phase": "analysis",
            "needs_clarification": False,
            "active_agents": [],
            "completed_agents": [],
            "agent_errors": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "processing_time_ms": 0
        }
        
        # Run workflow
        start_time = datetime.utcnow()
        
        async for state in self.workflow.astream(initial_state):
            # Update processing time
            state["processing_time_ms"] = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            # Log progress
            logger.info(
                "Workflow progress",
                phase=state.get("current_phase"),
                session_id=session_id
            )
        
        return state
    
    async def process_clarification(
        self,
        state: WorkflowState,
        response: ClarificationResponse
    ) -> WorkflowState:
        """Process clarification response and continue workflow."""
        # Add response to state
        state["clarification_responses"].append(response)
        
        # Continue from process_response node
        async for updated_state in self.workflow.astream(
            state,
            {"recursion_limit": 10}
        ):
            state = updated_state
        
        return state


# Singleton instance
_workflow_runner: Optional[WorkflowRunner] = None


def get_workflow_runner() -> WorkflowRunner:
    """Get workflow runner instance."""
    global _workflow_runner
    
    if _workflow_runner is None:
        _workflow_runner = WorkflowRunner()
    
    return _workflow_runner


# Export
__all__ = [
    'WorkflowState',
    'create_workflow',
    'WorkflowRunner',
    'get_workflow_runner'
]