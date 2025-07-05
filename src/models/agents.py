"""
Agent-specific models for the presentation generation system.
Defines standardized output formats for all agents using Pydantic BaseModel.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Any, Optional, Literal, Union
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

from .presentation import ComponentSpec, ChartType, DiagramType, LayoutType


# Base Agent Models
class AgentOutput(BaseModel):
    """Base model for all agent outputs ensuring consistency."""
    agent_id: str = Field(..., description="Unique agent identifier")
    output_type: str = Field(..., description="Type of output produced")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    correlation_id: str
    status: Literal["completed", "partial", "failed"]
    confidence_score: float = Field(..., ge=0, le=1, description="Agent's confidence in output")
    processing_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    )


# Director Agent Models
class RequirementAnalysis(BaseModel):
    """Analysis of user requirements by Director."""
    completeness_score: float = Field(..., ge=0, le=1)
    missing_information: List[str] = Field(default_factory=list)
    detected_intent: str
    presentation_type: str
    estimated_slides: int = Field(..., ge=1, le=100)
    complexity_level: Literal["simple", "moderate", "complex"]
    key_topics: List[str]
    suggested_flow: List[str]


class ClarificationQuestion(BaseModel):
    """Individual clarification question."""
    question_id: str = Field(default_factory=lambda: f"q_{uuid4().hex[:8]}")
    question: str
    question_type: Literal["text", "choice", "multi_choice", "scale", "boolean"]
    options: Optional[List[str]] = None
    required: bool = True
    context: Optional[str] = None
    priority: Literal["high", "medium", "low"] = "medium"
    category: str = "general"  # e.g., "audience", "content", "style"


class DirectorInboundOutput(AgentOutput):
    """Output from Director (Inbound) agent."""
    agent_id: Literal["director_inbound"] = "director_inbound"
    output_type: Literal["analysis", "clarification", "structure"] = "analysis"
    analysis: Optional[RequirementAnalysis] = None
    clarification_questions: Optional[List[ClarificationQuestion]] = None
    initial_structure: Optional[Dict[str, Any]] = None  # Simplified structure
    next_agents: List[str] = Field(default_factory=list)  # Agents to activate next


class DirectorOutboundOutput(AgentOutput):
    """Output from Director (Outbound) agent."""
    agent_id: Literal["director_outbound"] = "director_outbound"
    output_type: Literal["assembly", "validation", "export"] = "assembly"
    final_presentation: Optional[Dict[str, Any]] = None  # Complete presentation
    validation_results: Optional[Dict[str, Any]] = None
    export_ready: bool = False
    quality_score: float = Field(default=0.0, ge=0, le=1)
    improvement_suggestions: List[str] = Field(default_factory=list)


# UX Architect Models
class LayoutSpecification(BaseModel):
    """Layout specification for a slide."""
    slide_number: int
    layout_type: LayoutType
    grid_areas: List[Dict[str, Any]]  # Grid definitions
    component_zones: List[Dict[str, Any]]  # Where components can be placed
    responsive_breakpoints: Dict[str, Any]
    accessibility_notes: List[str]


class DesignSystem(BaseModel):
    """Design system specifications."""
    grid_system: Dict[str, Any]
    spacing_scale: List[int]
    typography_scale: Dict[str, Any]
    component_library: Dict[str, Any]
    interaction_patterns: Dict[str, Any]


class UXArchitectOutput(AgentOutput):
    """Output from UX Architect agent."""
    agent_id: Literal["ux_architect"] = "ux_architect"
    output_type: Literal["layout"] = "layout"
    layouts: List[LayoutSpecification]
    design_system: DesignSystem
    responsive_rules: Dict[str, Any]
    accessibility_compliance: Dict[str, bool]
    layout_rationale: Dict[str, str]  # Explanations for layout choices


# Researcher Models
class ResearchSource(BaseModel):
    """Individual research source."""
    source_id: str = Field(default_factory=lambda: f"src_{uuid4().hex[:8]}")
    title: str
    url: Optional[str] = None
    source_type: Literal["web", "document", "database", "api"]
    credibility_score: float = Field(..., ge=0, le=1)
    relevance_score: float = Field(..., ge=0, le=1)
    extracted_date: datetime = Field(default_factory=datetime.utcnow)
    summary: str
    key_points: List[str]


class ResearchFinding(BaseModel):
    """Consolidated research finding."""
    finding_id: str = Field(default_factory=lambda: f"find_{uuid4().hex[:8]}")
    topic: str
    content: str
    supporting_sources: List[str]  # source_ids
    confidence_level: float = Field(..., ge=0, le=1)
    data_points: Optional[List[Dict[str, Any]]] = None
    quotes: Optional[List[Dict[str, str]]] = None
    suggested_slide_placement: Optional[int] = None


class ResearcherOutput(AgentOutput):
    """Output from Researcher agent."""
    agent_id: Literal["researcher"] = "researcher"
    output_type: Literal["research"] = "research"
    findings: List[ResearchFinding]
    sources: List[ResearchSource]
    key_insights: List[str]
    data_suggestions: List[Dict[str, Any]]  # Suggestions for charts/visualizations
    content_outline: Dict[int, List[str]]  # Slide number -> content points
    fact_check_results: Optional[Dict[str, Any]] = None


# Visual Designer Models
class VisualAsset(BaseModel):
    """Generated visual asset."""
    asset_id: str = Field(default_factory=lambda: f"asset_{uuid4().hex[:8]}")
    asset_type: Literal["image", "icon", "pattern", "texture"]
    generation_method: Literal["ai_generated", "stock", "custom", "modified"]
    url: str
    thumbnail_url: Optional[str] = None
    prompt_used: Optional[str] = None
    style_attributes: Dict[str, Any]
    dimensions: Dict[str, int]  # width, height
    file_format: str
    file_size_kb: int
    color_palette: List[str]
    tags: List[str] = Field(default_factory=list)
    usage_rights: Dict[str, Any]
    quality_metrics: Dict[str, float]


class StyleGuide(BaseModel):
    """Visual style guide for consistency."""
    primary_colors: List[str]
    secondary_colors: List[str]
    gradient_styles: List[Dict[str, Any]]
    image_filters: List[str]
    visual_effects: Dict[str, Any]
    icon_style: Literal["flat", "3d", "outline", "filled"]
    illustration_style: Optional[str] = None


class VisualDesignerOutput(AgentOutput):
    """Output from Visual Designer agent."""
    agent_id: Literal["visual_designer"] = "visual_designer"
    output_type: Literal["visuals"] = "visuals"
    assets: List[VisualAsset]
    style_guide: StyleGuide
    asset_mapping: Dict[str, str]  # slide_id -> asset_id
    alternative_options: Dict[str, List[str]]  # asset_id -> [alternative_asset_ids]
    optimization_report: Dict[str, Any]


# Data Analyst Models
class ChartSpecification(BaseModel):
    """Specification for a chart/visualization."""
    chart_id: str = Field(default_factory=lambda: f"chart_{uuid4().hex[:8]}")
    chart_type: ChartType
    title: str
    subtitle: Optional[str] = None
    data_source: str  # Reference to data source
    data_points: List[Dict[str, Any]]
    axes_config: Dict[str, Any]
    series_config: List[Dict[str, Any]]
    color_scheme: List[str]
    interactive_features: List[str]
    annotations: Optional[List[Dict[str, Any]]] = None
    trend_indicators: Optional[Dict[str, Any]] = None


class DataInsight(BaseModel):
    """Data-driven insight."""
    insight_id: str = Field(default_factory=lambda: f"insight_{uuid4().hex[:8]}")
    insight_type: Literal["trend", "anomaly", "correlation", "comparison", "forecast"]
    description: str
    supporting_data: Dict[str, Any]
    significance_score: float = Field(..., ge=0, le=1)
    visualization_suggestion: Optional[str] = None


class DataAnalystOutput(AgentOutput):
    """Output from Data Analyst agent."""
    agent_id: Literal["data_analyst"] = "data_analyst"
    output_type: Literal["analysis"] = "analysis"
    charts: List[ChartSpecification]
    insights: List[DataInsight]
    data_quality_report: Dict[str, Any]
    statistical_summary: Dict[str, Any]
    visualization_rationale: Dict[str, str]  # chart_id -> explanation
    alternative_visualizations: Dict[str, List[Dict[str, Any]]]


# UX Analyst Models
class DiagramSpecification(BaseModel):
    """Specification for a diagram."""
    diagram_id: str = Field(default_factory=lambda: f"diag_{uuid4().hex[:8]}")
    diagram_type: DiagramType
    title: str
    structure: Dict[str, Any]  # Nodes, edges, hierarchy
    styling: Dict[str, Any]  # Colors, shapes, connectors
    layout_algorithm: str
    interactive_elements: List[str]
    annotations: Optional[List[Dict[str, Any]]] = None
    complexity_score: float = Field(..., ge=0, le=1)


class ProcessFlow(BaseModel):
    """Process flow specification."""
    flow_id: str = Field(default_factory=lambda: f"flow_{uuid4().hex[:8]}")
    flow_type: Literal["linear", "branching", "circular", "network"]
    steps: List[Dict[str, Any]]
    decision_points: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    swimlanes: Optional[List[str]] = None


class UXAnalystOutput(AgentOutput):
    """Output from UX Analyst agent."""
    agent_id: Literal["ux_analyst"] = "ux_analyst"
    output_type: Literal["diagrams"] = "diagrams"
    diagrams: List[DiagramSpecification]
    process_flows: List[ProcessFlow]
    information_architecture: Dict[str, Any]
    user_journey_maps: Optional[List[Dict[str, Any]]] = None
    complexity_analysis: Dict[str, Any]
    simplification_suggestions: List[str]


# Agent Communication Models
class AgentMessage(BaseModel):
    """Inter-agent communication message."""
    message_id: str = Field(default_factory=lambda: f"msg_{uuid4().hex[:12]}")
    from_agent: str
    to_agent: Union[str, List[str]]  # Can broadcast to multiple agents
    message_type: Literal["request", "response", "notification", "error"]
    priority: Literal["high", "medium", "low"] = "medium"
    payload: Dict[str, Any]
    requires_response: bool = False
    timeout_seconds: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentRequest(AgentMessage):
    """Request from one agent to another."""
    message_type: Literal["request"] = "request"
    action: str  # What the agent should do
    parameters: Dict[str, Any]
    context: Dict[str, Any]  # Additional context
    deadline: Optional[datetime] = None


class AgentResponse(AgentMessage):
    """Response from agent to request."""
    message_type: Literal["response"] = "response"
    request_id: str  # ID of the request being responded to
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    partial_result: bool = False  # If true, more responses coming


# Workflow State Models
class AgentTaskStatus(BaseModel):
    """Status of a task assigned to an agent."""
    task_id: str
    agent_id: str
    status: Literal["pending", "in_progress", "completed", "failed", "cancelled"]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: float = Field(default=0.0, ge=0, le=100)
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    output_reference: Optional[str] = None  # Reference to agent output


class WorkflowState(BaseModel):
    """Current state of the presentation generation workflow."""
    workflow_id: str = Field(default_factory=lambda: f"wf_{uuid4().hex[:12]}")
    session_id: str
    current_phase: Literal["analysis", "generation", "refinement", "finalization"]
    active_agents: List[str]
    completed_agents: List[str]
    pending_agents: List[str]
    agent_tasks: List[AgentTaskStatus]
    overall_progress: float = Field(default=0.0, ge=0, le=100)
    estimated_completion_time: Optional[datetime] = None
    workflow_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Quality and Validation Models
class QualityMetrics(BaseModel):
    """Quality metrics for generated content."""
    metric_id: str = Field(default_factory=lambda: f"qm_{uuid4().hex[:8]}")
    content_quality: float = Field(..., ge=0, le=1)
    visual_consistency: float = Field(..., ge=0, le=1)
    data_accuracy: float = Field(..., ge=0, le=1)
    layout_effectiveness: float = Field(..., ge=0, le=1)
    accessibility_score: float = Field(..., ge=0, le=1)
    overall_score: float = Field(..., ge=0, le=1)
    detailed_scores: Dict[str, float]
    issues_found: List[Dict[str, Any]]
    improvement_suggestions: List[str]


class ValidationResult(BaseModel):
    """Validation result for agent output."""
    validation_id: str = Field(default_factory=lambda: f"val_{uuid4().hex[:8]}")
    agent_id: str
    output_id: str
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    quality_metrics: Optional[QualityMetrics] = None
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    validator_version: str = "1.0.0"


# Agent Registry
class AgentCapability(BaseModel):
    """Capability description for an agent."""
    capability_id: str
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    required_context: List[str]
    performance_metrics: Dict[str, float]


class AgentRegistration(BaseModel):
    """Agent registration information."""
    agent_id: str
    agent_type: str
    version: str
    capabilities: List[AgentCapability]
    dependencies: List[str]  # Other agents this agent depends on
    resource_requirements: Dict[str, Any]
    configuration: Dict[str, Any]
    status: Literal["active", "inactive", "maintenance"]
    health_check_endpoint: Optional[str] = None
    last_health_check: Optional[datetime] = None