"""
Director (Inbound) Agent implementation.
Handles user interactions, requirement gathering, and orchestration.
"""

from typing import Dict, Any, List, Optional, Type
from datetime import datetime
import asyncio
import json

from pydantic import BaseModel, Field
from pydantic_ai import RunContext

from .base import BaseAgent, AgentConfig, AgentContext
from ..models.agents import (
    DirectorInboundOutput, RequirementAnalysis,
    ClarificationQuestion, AgentRequest
)
from ..models.messages import (
    UserInput, PresentationRequest, ClarificationRound,
    ClarificationResponse
)
from ..models.presentation import Presentation, Slide, LayoutType
from ..utils.logger import agent_logger
from ..utils.validators import validate_prompt_injection


class DirectorInboundConfig(AgentConfig):
    """Configuration specific to Director Inbound agent."""
    max_clarification_rounds: int = 3
    min_completeness_score: float = 0.8
    embedding_model: str = "text-embedding-3-small"


class PresentationStructureOutput(BaseModel):
    """Output format for presentation structure generation."""
    title: str
    description: str
    estimated_slides: int
    slide_outlines: List[Dict[str, Any]]
    theme_suggestions: Dict[str, Any]
    next_agents: List[str]


class DirectorInboundAgent(BaseAgent):
    """
    Director (Inbound) agent responsible for:
    - Understanding user requirements
    - Asking clarifying questions
    - Creating initial presentation structure
    - Orchestrating other agents
    """
    
    def __init__(self, config: Optional[DirectorInboundConfig] = None):
        """Initialize Director Inbound agent."""
        if config is None:
            config = DirectorInboundConfig(
                name="director_inbound",
                description="Handles user interactions and requirement gathering",
                model_primary="openai:gpt-4",
                model_fallbacks=["openai:gpt-3.5-turbo", "anthropic:claude-3-sonnet"],
                temperature=0.3,  # Lower temperature for more consistent analysis
                system_prompt_file="director_inbound.txt",
                capabilities=[
                    "requirement_analysis",
                    "clarification_generation",
                    "structure_creation",
                    "agent_orchestration"
                ],
                dependencies=[]
            )
        
        super().__init__(config)
        self.config: DirectorInboundConfig = config
        self.clarification_history: Dict[str, List[ClarificationRound]] = {}
    
    def get_output_type(self) -> Type[BaseModel]:
        """Get output type for this agent."""
        return DirectorInboundOutput
    
    def get_default_system_prompt(self) -> str:
        """Get default system prompt."""
        return """You are the Director (Inbound) agent for a presentation generation system.
Your role is to:
1. Analyze user requirements for presentations
2. Identify missing or unclear information
3. Generate thoughtful clarification questions
4. Create initial presentation structures
5. Determine which specialized agents to activate

Key guidelines:
- Be thorough in understanding user needs
- Ask specific, actionable questions
- Consider the target audience and presentation context
- Suggest appropriate presentation types and structures
- Maintain a professional, helpful tone

When analyzing requirements, consider:
- Presentation purpose and goals
- Target audience characteristics
- Time constraints and presentation length
- Visual style preferences
- Content depth and technical level
- Industry or domain context

Output structured JSON responses according to the defined schemas."""
    
    async def process_request(
        self,
        request: AgentRequest,
        context: AgentContext
    ) -> DirectorInboundOutput:
        """
        Process a request to the Director Inbound agent.
        
        Args:
            request: Agent request
            context: Execution context
            
        Returns:
            Director Inbound output
        """
        action = request.action
        
        if action == "analyze_request":
            return await self._analyze_user_request(
                request.parameters.get("user_input"),
                context
            )
        elif action == "generate_clarifications":
            return await self._generate_clarifications(
                request.parameters.get("analysis"),
                context
            )
        elif action == "create_structure":
            return await self._create_presentation_structure(
                request.parameters.get("requirements"),
                context
            )
        elif action == "process_clarification_response":
            return await self._process_clarification_response(
                request.parameters.get("response"),
                context
            )
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _analyze_user_request(
        self,
        user_input: Dict[str, Any],
        context: AgentContext
    ) -> DirectorInboundOutput:
        """Analyze initial user request."""
        # Validate input
        if not validate_prompt_injection(user_input.get("text", "")):
            agent_logger.warning(
                "Potential prompt injection detected",
                session_id=context.session_id,
                user_input=user_input
            )
            # Continue but with caution
        
        # Check cache for similar requests
        cache_key = f"analysis:{hash(user_input.get('text', ''))}"
        cached_analysis = await self.get_cached_result(cache_key)
        
        if cached_analysis:
            agent_logger.info("Using cached analysis", session_id=context.session_id)
            analysis = RequirementAnalysis(**cached_analysis)
        else:
            # Run analysis through LLM
            analysis = await self._run_requirement_analysis(user_input, context)
            
            # Cache result
            await self.cache_result(cache_key, analysis.model_dump(), ttl=3600)
        
        # Determine next step
        if analysis.completeness_score < self.config.min_completeness_score:
            # Need clarifications
            output_type = "clarification"
            next_agents = []
        else:
            # Ready to create structure
            output_type = "structure"
            next_agents = ["ux_architect", "researcher"]
        
        return DirectorInboundOutput(
            agent_id=self.agent_id,
            output_type=output_type,
            timestamp=datetime.utcnow(),
            session_id=context.session_id,
            correlation_id=context.correlation_id,
            status="completed",
            confidence_score=0.9,
            analysis=analysis,
            next_agents=next_agents
        )
    
    async def _run_requirement_analysis(
        self,
        user_input: Dict[str, Any],
        context: AgentContext
    ) -> RequirementAnalysis:
        """Run requirement analysis using LLM."""
        prompt = f"""Analyze the following presentation request:

User Input: {user_input.get('text', '')}
Attachments: {len(user_input.get('attachments', []))} files
UI References: {user_input.get('ui_references', [])}

Analyze and provide:
1. Completeness score (0-1) based on having enough information
2. List of missing information pieces
3. Detected intent/purpose
4. Suggested presentation type
5. Estimated number of slides
6. Complexity level
7. Key topics to cover
8. Suggested presentation flow

Consider:
- Is the target audience clear?
- Is the presentation purpose defined?
- Are there time/length constraints?
- Is the desired style/tone specified?
- Are there specific content requirements?"""
        
        # Run LLM
        result = await self.run_llm(
            prompt=prompt,
            context={
                "session_history": context.session_history,
                "user_input": user_input
            },
            temperature=0.3
        )
        
        # Parse result into RequirementAnalysis
        # The Pydantic AI agent should return structured data
        if hasattr(result, 'data'):
            return RequirementAnalysis(**result.data)
        else:
            # Fallback parsing
            return self._parse_analysis_response(str(result))
    
    def _parse_analysis_response(self, response: str) -> RequirementAnalysis:
        """Parse LLM response into RequirementAnalysis."""
        # This is a fallback - ideally Pydantic AI handles this
        try:
            # Try to parse as JSON first
            data = json.loads(response)
            return RequirementAnalysis(**data)
        except:
            # Manual parsing as last resort
            return RequirementAnalysis(
                completeness_score=0.5,
                missing_information=["Unable to parse response"],
                detected_intent="presentation",
                presentation_type="general",
                estimated_slides=10,
                complexity_level="moderate",
                key_topics=["Topic extraction failed"],
                suggested_flow=["Introduction", "Content", "Conclusion"]
            )
    
    async def _generate_clarifications(
        self,
        analysis: RequirementAnalysis,
        context: AgentContext
    ) -> DirectorInboundOutput:
        """Generate clarification questions based on analysis."""
        # Check clarification history
        round_number = len(self.clarification_history.get(context.session_id, [])) + 1
        
        if round_number > self.config.max_clarification_rounds:
            # Too many rounds, proceed with what we have
            agent_logger.warning(
                "Max clarification rounds reached",
                session_id=context.session_id,
                rounds=round_number
            )
            return await self._create_structure_from_partial_info(analysis, context)
        
        # Generate questions
        questions = await self._run_clarification_generation(
            analysis.missing_information,
            context
        )
        
        # Create clarification round
        clarification_round = ClarificationRound(
            questions=questions,
            context=f"Based on your request for a {analysis.presentation_type} presentation, I need some additional information:",
            max_rounds=self.config.max_clarification_rounds,
            current_round=round_number
        )
        
        # Store in history
        if context.session_id not in self.clarification_history:
            self.clarification_history[context.session_id] = []
        self.clarification_history[context.session_id].append(clarification_round)
        
        return DirectorInboundOutput(
            agent_id=self.agent_id,
            output_type="clarification",
            timestamp=datetime.utcnow(),
            session_id=context.session_id,
            correlation_id=context.correlation_id,
            status="completed",
            confidence_score=0.85,
            clarification_questions=clarification_round.questions,
            metadata={
                "round_number": round_number,
                "max_rounds": self.config.max_clarification_rounds
            }
        )
    
    async def _run_clarification_generation(
        self,
        missing_info: List[str],
        context: AgentContext
    ) -> List[ClarificationQuestion]:
        """Generate clarification questions using LLM."""
        prompt = f"""Generate clarification questions for the following missing information:

Missing Information:
{json.dumps(missing_info, indent=2)}

Previous Questions Asked:
{json.dumps([round.model_dump() for round in self.clarification_history.get(context.session_id, [])], indent=2)}

Generate 3-5 specific, actionable questions that will help gather the missing information.
For each question:
1. Make it clear and specific
2. Provide multiple choice options where appropriate
3. Mark critical questions as required
4. Add helpful context
5. Categorize by type (audience, content, style, logistics)

Avoid:
- Redundant questions
- Overly technical language
- Questions already answered in previous rounds"""
        
        result = await self.run_llm(
            prompt=prompt,
            context={"missing_info": missing_info},
            temperature=0.5
        )
        
        # Parse into ClarificationQuestion objects
        questions = []
        if hasattr(result, 'data') and isinstance(result.data, list):
            for q_data in result.data:
                questions.append(ClarificationQuestion(**q_data))
        else:
            # Fallback - create basic questions
            for info in missing_info[:5]:  # Limit to 5 questions
                questions.append(ClarificationQuestion(
                    question=f"Could you please provide more details about {info}?",
                    question_type="text",
                    required=True,
                    category="general",
                    priority="medium"
                ))
        
        return questions
    
    async def _create_presentation_structure(
        self,
        requirements: Dict[str, Any],
        context: AgentContext
    ) -> DirectorInboundOutput:
        """Create initial presentation structure."""
        # Find similar presentations
        similar_presentations = await self._find_similar_presentations(
            requirements,
            context
        )
        
        # Generate structure
        structure = await self._run_structure_generation(
            requirements,
            similar_presentations,
            context
        )
        
        # Determine next agents
        next_agents = self._determine_next_agents(structure)
        
        # Save initial structure
        await self._save_initial_structure(structure, context)
        
        return DirectorInboundOutput(
            agent_id=self.agent_id,
            output_type="structure",
            timestamp=datetime.utcnow(),
            session_id=context.session_id,
            correlation_id=context.correlation_id,
            status="completed",
            confidence_score=0.95,
            initial_structure=structure,
            next_agents=next_agents,
            metadata={
                "similar_presentations_found": len(similar_presentations),
                "estimated_generation_time": self._estimate_generation_time(structure)
            }
        )
    
    async def _find_similar_presentations(
        self,
        requirements: Dict[str, Any],
        context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Find similar presentations using vector search."""
        try:
            # Generate embedding for requirements
            embedding = await self._generate_embedding(
                json.dumps(requirements)
            )
            
            # Search in Supabase
            supabase = await self.supabase
            similar = await supabase.find_similar_presentations(
                embedding=embedding,
                threshold=0.75,
                limit=5,
                filter_type=requirements.get("presentation_type")
            )
            
            return similar
        except Exception as e:
            agent_logger.error(
                "Failed to find similar presentations",
                error=str(e),
                session_id=context.session_id
            )
            return []
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding using OpenAI."""
        # This would use OpenAI's embedding API
        # Placeholder implementation
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        # Generate a deterministic "embedding" for testing
        return [float(b) / 255.0 for b in hash_obj.digest()[:1536]]
    
    async def _run_structure_generation(
        self,
        requirements: Dict[str, Any],
        similar_presentations: List[Dict[str, Any]],
        context: AgentContext
    ) -> Dict[str, Any]:
        """Generate presentation structure using LLM."""
        prompt = f"""Create a presentation structure based on:

Requirements:
{json.dumps(requirements, indent=2)}

Similar Successful Presentations:
{json.dumps([{
    'title': p.get('title'),
    'structure': p.get('structure', {}).get('slides', [])[:3]
} for p in similar_presentations], indent=2)}

Generate a complete presentation structure including:
1. Title and description
2. Estimated number of slides
3. Detailed outline for each slide:
   - Slide number and title
   - Layout type (hero, content, chart_focused, etc.)
   - Key content points
   - Suggested visuals
4. Theme suggestions (colors, style, tone)
5. Which specialized agents to activate

Consider:
- Target audience needs
- Presentation goals
- Time constraints
- Visual requirements
- Industry best practices"""
        
        result = await self.run_llm(
            prompt=prompt,
            context={
                "requirements": requirements,
                "similar_count": len(similar_presentations)
            },
            temperature=0.4
        )
        
        # Parse into structure
        if hasattr(result, 'data'):
            return result.data
        else:
            # Fallback structure
            return {
                "title": requirements.get("topic", "Presentation"),
                "description": "AI-generated presentation",
                "estimated_slides": 10,
                "slide_outlines": [
                    {
                        "slide_number": i,
                        "title": f"Slide {i}",
                        "layout_type": "content",
                        "content_points": ["Content to be added"]
                    }
                    for i in range(1, 11)
                ],
                "theme_suggestions": {
                    "style": "professional",
                    "color_scheme": "blue"
                },
                "next_agents": ["ux_architect", "researcher"]
            }
    
    def _determine_next_agents(self, structure: Dict[str, Any]) -> List[str]:
        """Determine which agents to activate next."""
        agents = ["ux_architect", "researcher"]  # Always needed
        
        # Check if visual designer needed
        if any("visual" in str(slide).lower() for slide in structure.get("slide_outlines", [])):
            agents.append("visual_designer")
        
        # Check if data analyst needed
        if any("chart" in str(slide).lower() or "data" in str(slide).lower() 
               for slide in structure.get("slide_outlines", [])):
            agents.append("data_analyst")
        
        # Check if UX analyst needed
        if any("diagram" in str(slide).lower() or "process" in str(slide).lower()
               for slide in structure.get("slide_outlines", [])):
            agents.append("ux_analyst")
        
        return agents
    
    async def _save_initial_structure(
        self,
        structure: Dict[str, Any],
        context: AgentContext
    ):
        """Save initial structure to cache and database."""
        # Cache for quick access
        cache_key = f"structure:{context.session_id}"
        await self.cache_result(cache_key, structure, ttl=3600)
        
        # Also update session state
        redis = await self.redis
        session_data = await redis.get_session(context.session_id)
        if session_data:
            session_data["current_structure"] = structure
            session_data["phase"] = "structure_created"
            await redis.set_session(context.session_id, session_data)
    
    async def _process_clarification_response(
        self,
        response: Dict[str, Any],
        context: AgentContext
    ) -> DirectorInboundOutput:
        """Process user's response to clarification questions."""
        # Update context with responses
        clarification_response = ClarificationResponse(**response)
        
        # Merge with existing requirements
        requirements = await self._merge_clarification_responses(
            clarification_response,
            context
        )
        
        # Re-analyze completeness
        analysis = await self._run_requirement_analysis(
            {"text": json.dumps(requirements)},
            context
        )
        
        if analysis.completeness_score >= self.config.min_completeness_score:
            # Ready to create structure
            return await self._create_presentation_structure(requirements, context)
        else:
            # Need more clarifications
            return await self._generate_clarifications(analysis, context)
    
    async def _merge_clarification_responses(
        self,
        response: ClarificationResponse,
        context: AgentContext
    ) -> Dict[str, Any]:
        """Merge clarification responses with existing requirements."""
        # Get existing requirements from session
        redis = await self.redis
        session_data = await redis.get_session(context.session_id)
        
        requirements = session_data.get("requirements", {})
        
        # Merge responses
        for question_id, answer in response.responses.items():
            # Map answer to requirement field
            # This would be more sophisticated in production
            if "audience" in question_id:
                requirements["target_audience"] = answer
            elif "duration" in question_id or "length" in question_id:
                requirements["duration"] = answer
            elif "style" in question_id or "tone" in question_id:
                requirements["style"] = answer
            else:
                requirements[question_id] = answer
        
        # Update session
        session_data["requirements"] = requirements
        await redis.set_session(context.session_id, session_data)
        
        return requirements
    
    async def _create_structure_from_partial_info(
        self,
        analysis: RequirementAnalysis,
        context: AgentContext
    ) -> DirectorInboundOutput:
        """Create structure even with partial information."""
        agent_logger.info(
            "Creating structure from partial information",
            session_id=context.session_id,
            completeness_score=analysis.completeness_score
        )
        
        # Get whatever requirements we have
        redis = await self.redis
        session_data = await redis.get_session(context.session_id)
        requirements = session_data.get("requirements", {})
        
        # Fill in defaults for missing info
        defaults = {
            "target_audience": "general business audience",
            "duration": "15-20 minutes",
            "style": "professional",
            "slides": analysis.estimated_slides
        }
        
        for key, value in defaults.items():
            if key not in requirements:
                requirements[key] = value
        
        # Create structure with lower confidence
        output = await self._create_presentation_structure(requirements, context)
        output.confidence_score = 0.7  # Lower confidence due to partial info
        
        return output
    
    def _estimate_generation_time(self, structure: Dict[str, Any]) -> int:
        """Estimate time to generate full presentation in seconds."""
        base_time = 30  # Base processing time
        slide_time = 5  # Per slide
        
        num_slides = structure.get("estimated_slides", 10)
        complexity_multiplier = {
            "simple": 0.8,
            "moderate": 1.0,
            "complex": 1.5
        }.get(structure.get("complexity", "moderate"), 1.0)
        
        return int((base_time + (num_slides * slide_time)) * complexity_multiplier)


# Export
__all__ = ['DirectorInboundAgent', 'DirectorInboundConfig']