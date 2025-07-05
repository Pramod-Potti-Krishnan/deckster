"""
Director (Inbound) Agent implementation.
Handles user interactions, requirement gathering, and orchestration.
"""

from typing import Dict, Any, List, Optional, Type
from datetime import datetime
import asyncio
import json

from pydantic import BaseModel, Field

from .base import BaseAgent, AgentConfig, AgentContext

# Import pydantic_ai if available
try:
    from pydantic_ai import Agent
    from pydantic_ai.settings import ModelSettings
    from pydantic_ai.exceptions import (
        ModelRetry,
        UserError,
        AgentRunError,
        UsageLimitExceeded,
        ModelHTTPError
    )
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    Agent = None
    ModelSettings = None
    PYDANTIC_AI_AVAILABLE = False
    # Mock exceptions for compatibility
    class ModelRetry(Exception): pass
    class UserError(Exception): pass
    class AgentRunError(Exception): pass
    class UsageLimitExceeded(Exception): pass
    class ModelHTTPError(Exception): pass
from ..models.agents import (
    DirectorInboundOutput, RequirementAnalysis,
    ClarificationQuestion as AgentClarificationQuestion, AgentRequest
)
from ..models.messages import (
    UserInput, PresentationRequest, ClarificationRound,
    ClarificationResponse, ClarificationQuestion
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
        
        # Check for greeting patterns
        # Handle both direct text and nested data structure
        if isinstance(user_input.get("data"), dict):
            user_text = user_input.get("data", {}).get("text", "").lower().strip()
        else:
            user_text = user_input.get("text", "").lower().strip()
            
        greeting_patterns = ["hi", "hello", "hey", "good morning", "good afternoon", 
                           "good evening", "greetings", "howdy", "yo", "hiya", "hi there", "hello there"]
        
        # Debug greeting detection
        agent_logger.debug(
            f"🔍 Greeting detection check",
            user_text=user_text,
            user_input_structure=user_input,
            checking_patterns=greeting_patterns[:5] + ["..."]  # Show first 5 patterns
        )
        
        is_greeting = any(user_text.startswith(pattern) or user_text == pattern for pattern in greeting_patterns)
        
        agent_logger.info(
            f"🔍 Greeting detection result",
            user_text=user_text,
            is_greeting=is_greeting,
            session_id=context.session_id
        )
        
        if is_greeting:
            # Return greeting response
            agent_logger.info(
                f"✅ Returning greeting response",
                session_id=context.session_id,
                output_type="greeting"
            )
            
            greeting_output = DirectorInboundOutput(
                agent_id=self.agent_id,
                output_type="greeting",
                timestamp=datetime.utcnow(),
                session_id=context.session_id,
                correlation_id=context.correlation_id,
                status="completed",
                confidence_score=1.0,
                greeting_response={
                    "message": "Hello! I'm Deckster, your AI presentation assistant. 🎯\n\nI can help you create professional presentations on any topic. Just tell me what you'd like to present about, and I'll guide you through creating something amazing!\n\nWhat topic would you like to explore?",
                    "suggestions": [
                        "Business presentation",
                        "Educational content", 
                        "Technical overview",
                        "Sales pitch",
                        "Project update"
                    ]
                },
                metadata={"is_greeting": True}
            )
            
            agent_logger.debug(
                f"🔍 Greeting output created",
                output_type=greeting_output.output_type,
                has_greeting_response=greeting_output.greeting_response is not None,
                greeting_message_preview=greeting_output.greeting_response.get("message", "")[:50] + "..."
            )
            
            return greeting_output
        
        # Check cache for similar requests - use the correct text path
        if isinstance(user_input.get("data"), dict):
            text_for_cache = user_input.get("data", {}).get("text", "")
        else:
            text_for_cache = user_input.get("text", "")
        
        cache_key = f"analysis:{hash(text_for_cache)}"
        cached_analysis = await self.get_cached_result(cache_key)
        
        # Debug cache usage
        agent_logger.debug(
            f"Cache check for analysis",
            session_id=context.session_id,
            text_for_cache=text_for_cache[:50] + "..." if len(text_for_cache) > 50 else text_for_cache,
            cache_key_hash=hash(text_for_cache),
            cache_hit=cached_analysis is not None
        )
        
        if cached_analysis:
            agent_logger.info("Using cached analysis", session_id=context.session_id)
            analysis = RequirementAnalysis(**cached_analysis)
        else:
            # Run analysis through LLM
            analysis = await self._run_requirement_analysis(user_input, context)
            
            # Cache result
            await self.cache_result(cache_key, analysis.model_dump(mode='json'), ttl=3600)
        
        # Determine next step
        if analysis.completeness_score < self.config.min_completeness_score:
            # Need clarifications
            output_type = "clarification"
            next_agents = []
        else:
            # Ready to create structure
            output_type = "structure"
            next_agents = ["ux_architect", "researcher"]
        
        # Create output with proper initialization
        output = DirectorInboundOutput(
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
        
        # If we need clarifications, generate them
        if output_type == "clarification":
            # Generate questions
            questions = await self._run_clarification_generation(
                analysis.missing_information,
                context
            )
            output.clarification_questions = questions
        
        return output
    
    async def _run_requirement_analysis(
        self,
        user_input: Dict[str, Any],
        context: AgentContext
    ) -> RequirementAnalysis:
        """Run requirement analysis using LLM."""
        
        # Use the main agent's run_llm method instead of creating a new agent
        try:
            # Prepare the analysis prompt - handle nested data structure
            if isinstance(user_input.get("data"), dict):
                text_content = user_input.get("data", {}).get("text", "")
                attachments = user_input.get("data", {}).get("attachments", [])
                ui_references = user_input.get("data", {}).get("ui_references", [])
            else:
                text_content = user_input.get("text", "")
                attachments = user_input.get("attachments", [])
                ui_references = user_input.get("ui_references", [])
                
            analysis_prompt = f"""Analyze this presentation request and provide a detailed analysis.

User Input: {text_content}
Attachments: {len(attachments)} files
UI References: {ui_references}

Return a JSON object with these fields:
- completeness_score: float between 0 and 1 indicating how complete the request is
- missing_information: list of strings describing what information is missing
- detected_intent: string describing the main purpose
- presentation_type: string (e.g., "business", "educational", "technical")
- estimated_slides: integer number of slides needed
- complexity_level: string ("simple", "moderate", "complex")
- key_topics: list of main topics to cover
- suggested_flow: list of section names in order

Example response:
{{
    "completeness_score": 0.7,
    "missing_information": ["target audience", "presentation duration"],
    "detected_intent": "educate about AI",
    "presentation_type": "educational",
    "estimated_slides": 15,
    "complexity_level": "moderate",
    "key_topics": ["AI basics", "machine learning", "applications"],
    "suggested_flow": ["Introduction", "AI Fundamentals", "ML Concepts", "Real-world Applications", "Conclusion"]
}}"""
            
            # Run the analysis using the main agent
            result = await self.run_llm(
                prompt=analysis_prompt,
                context=context.model_dump(mode='json'),  # Ensure context is properly serialized
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            # Parse the result - PydanticAI returns structured data directly
            # when output_type is configured properly
            if isinstance(result, RequirementAnalysis):
                return result
            elif isinstance(result, dict):
                return RequirementAnalysis(**result)
            elif isinstance(result, str):
                # Try to parse JSON from string
                try:
                    data = json.loads(result)
                    return RequirementAnalysis(**data)
                except:
                    agent_logger.warning(f"Could not parse analysis result: {result[:100]}...")
                    return self._get_default_analysis(user_input)
            else:
                agent_logger.warning(f"Unexpected result type: {type(result)} - did you configure output_type correctly?")
                return self._get_default_analysis(user_input)
                
        except Exception as e:
            agent_logger.error(f"Failed to run requirement analysis: {e}", exc_info=True)
            return self._get_default_analysis(user_input)
    
    def _get_default_analysis(self, user_input: Dict[str, Any]) -> RequirementAnalysis:
        """Get default analysis when AI is not available."""
        # Handle nested data structure
        if isinstance(user_input.get("data"), dict):
            text = user_input.get("data", {}).get("text", "").lower()
        else:
            text = user_input.get('text', '').lower()
        
        # Simple heuristic analysis
        has_topic = len(text) > 10
        has_details = len(text) > 50
        
        completeness = 0.3
        if has_topic:
            completeness += 0.3
        if has_details:
            completeness += 0.3
            
        missing_info = []
        if "audience" not in text and "for" not in text:
            missing_info.append("Target audience")
        if "slides" not in text and "pages" not in text:
            missing_info.append("Number of slides")
        if "purpose" not in text and "goal" not in text:
            missing_info.append("Presentation purpose")
            
        return RequirementAnalysis(
            completeness_score=completeness,
            missing_information=missing_info or ["General clarification needed"],
            detected_intent="presentation_creation",
            presentation_type="general",
            estimated_slides=10,
            complexity_level="moderate",
            key_topics=[text[:50] + "..."] if text else ["No topic specified"],
            suggested_flow=["Introduction", "Main Content", "Conclusion"]
        )
    
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
        prompt = f"""You are an expert presentation consultant. Based on the user's initial request, I need you to ask thoughtful clarification questions to create the perfect presentation.

Missing Information Identified:
{json.dumps(missing_info, indent=2)}

Previous Questions Asked:
{json.dumps([round.model_dump(mode='json') for round in self.clarification_history.get(context.session_id, [])], indent=2)}

Please generate 2-4 conversational, intelligent questions that will help me understand:
1. **Audience & Context**: Who are they presenting to? What's the setting?
2. **Purpose & Goals**: What do they want to achieve? What action should the audience take?
3. **Content & Focus**: What are the key messages? What level of detail is needed?
4. **Style & Constraints**: What tone/style fits? Any time or format constraints?

Make each question:
- Natural and conversational (not robotic)
- Focused on one specific aspect
- Easy to answer in a few words or sentences
- Relevant to creating a great presentation

Return as a simple list of questions - no complex structure needed. Ask like a helpful colleague would."""
        
        try:
            result = await self.run_llm(
                prompt=prompt,
                context={"missing_info": missing_info},
                temperature=0.5
            )
        except ModelHTTPError as e:
            agent_logger.error(f"API error generating clarifications: {e}")
            # Return fallback questions
            return self._get_fallback_clarification_questions(missing_info)
        except UsageLimitExceeded as e:
            agent_logger.error(f"Usage limit exceeded: {e}")
            return self._get_fallback_clarification_questions(missing_info)
        
        # Parse into ClarificationQuestion objects
        questions = []
        
        # Handle different result types based on PydanticAI best practices
        if isinstance(result, list):
            # Direct list result
            for q_data in result:
                questions.append(self._parse_clarification_question(q_data))
        elif hasattr(result, 'data') and isinstance(result.data, list):
            # RunResult with data attribute (shouldn't happen with proper setup)
            for q_data in result.data:
                questions.append(self._parse_clarification_question(q_data))
        elif isinstance(result, str):
            # String result - try to parse as JSON
            try:
                parsed = json.loads(result)
                if isinstance(parsed, list):
                    for q_data in parsed:
                        questions.append(self._parse_clarification_question(q_data))
                else:
                    return self._get_fallback_clarification_questions(missing_info)
            except:
                return self._get_fallback_clarification_questions(missing_info)
        else:
            # Fallback - create basic questions using message model
            return self._get_fallback_clarification_questions(missing_info)
        
        return questions
    
    def _parse_clarification_question(self, q_data: Dict[str, Any]) -> ClarificationQuestion:
        """Parse a question data dict into ClarificationQuestion."""
        # Convert agent model to message model if needed
        if 'category' in q_data or 'priority' in q_data:
            # This is AgentClarificationQuestion format, convert to message format
            message_data = {
                'question_id': q_data.get('question_id'),
                'question': q_data.get('question'),
                'question_type': q_data.get('question_type', 'text'),
                'options': q_data.get('options'),
                'required': q_data.get('required', True),
                'context': q_data.get('context')
            }
            return ClarificationQuestion(**message_data)
        else:
            return ClarificationQuestion(**q_data)
    
    def _get_fallback_clarification_questions(self, missing_info: List[str]) -> List[ClarificationQuestion]:
        """Get fallback clarification questions when AI is unavailable."""
        questions = []
        for info in missing_info[:5]:  # Limit to 5 questions
            questions.append(ClarificationQuestion(
                question=f"Could you please provide more details about {info}?",
                question_type="text",
                required=True
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
        
        try:
            result = await self.run_llm(
                prompt=prompt,
                context={
                    "requirements": requirements,
                    "similar_count": len(similar_presentations)
                },
                temperature=0.4
            )
        except ModelRetry as e:
            agent_logger.warning(f"Model requested retry for structure generation: {e}")
            # Could implement exponential backoff here
            raise
        except (ModelHTTPError, UsageLimitExceeded) as e:
            agent_logger.error(f"Error generating structure: {e}")
            # Return fallback structure
            return self._get_fallback_structure(requirements)
        
        # Parse into structure - handle different result types
        if isinstance(result, dict):
            return result
        elif isinstance(result, PresentationStructureOutput):
            return result.model_dump(mode='json')
        elif hasattr(result, 'data'):
            # This shouldn't happen with proper output_type configuration
            agent_logger.warning("Received RunResult instead of direct data - check output_type configuration")
            return result.data
        else:
            # Fallback structure
            return self._get_fallback_structure(requirements)
    
    def _get_fallback_structure(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback structure when AI is unavailable."""
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