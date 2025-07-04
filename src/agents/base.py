"""
Base agent class for all AI agents in the presentation generator.
Provides common functionality using Pydantic AI framework.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type, Union
from datetime import datetime
import asyncio
import time
from uuid import uuid4

from pydantic import BaseModel, Field

# Import logger first before using it
from ..models.agents import AgentOutput, AgentMessage, AgentRequest, AgentResponse
from ..utils.logger import agent_logger, log_agent_request, log_agent_response, log_llm_call, log_error
from ..storage import get_redis, get_supabase

# Make pydantic_ai optional
PYDANTIC_AI_IMPORT_ERROR = None
try:
    from pydantic_ai import Agent, RunContext
    from pydantic_ai.exceptions import ModelRetry
    
    # Try different import patterns for models
    FallbackModel = None
    ModelMessage = None
    
    # Try importing from pydantic_ai.models
    try:
        from pydantic_ai.models import ModelMessage
        agent_logger.debug("✅ Imported ModelMessage from pydantic_ai.models")
    except ImportError:
        agent_logger.debug("⚠️  ModelMessage not found in pydantic_ai.models")
    
    # Try importing FallbackModel - it might have a different name or location
    try:
        from pydantic_ai.models import FallbackModel
        agent_logger.debug("✅ Imported FallbackModel from pydantic_ai.models")
    except ImportError:
        # Try alternative names
        try:
            from pydantic_ai.models import Model as FallbackModel
            agent_logger.debug("✅ Using Model as FallbackModel")
        except ImportError:
            try:
                from pydantic_ai import Model as FallbackModel
                agent_logger.debug("✅ Using pydantic_ai.Model as FallbackModel")
            except ImportError:
                agent_logger.warning("⚠️  FallbackModel not found, will use single model approach")
                FallbackModel = None
    
    PYDANTIC_AI_AVAILABLE = True
    agent_logger.info("✅ Successfully imported pydantic_ai core components")
    
except ImportError as e:
    PYDANTIC_AI_AVAILABLE = False
    PYDANTIC_AI_IMPORT_ERROR = str(e)
    agent_logger.warning(f"⚠️  Failed to import pydantic_ai: {e}")
    # Create mock classes for compatibility
    class Agent: pass
    class RunContext:
        def __init__(self, deps=None):
            self.deps = deps
    class FallbackModel: pass
    class ModelMessage: pass
    class ModelRetry(Exception): pass


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    name: str
    description: str
    model_primary: str = "openai:gpt-4"
    model_fallbacks: List[str] = Field(default_factory=lambda: ["openai:gpt-3.5-turbo"])
    temperature: float = 0.7
    max_retries: int = 3
    timeout_seconds: int = 30
    system_prompt_file: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)


class AgentContext(BaseModel):
    """Context passed to agent during execution."""
    session_id: str
    correlation_id: str
    request_id: str
    user_id: Optional[str] = None
    session_history: List[Dict[str, Any]] = Field(default_factory=list)
    shared_memory: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Provides common functionality and interfaces.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize base agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.agent_id = config.name
        
        # Initialize Pydantic AI agent
        self._init_pydantic_agent()
        
        # Storage clients (lazy loaded)
        self._redis = None
        self._supabase = None
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "average_latency_ms": 0.0
        }
        
        agent_logger.info(
            f"Agent initialized: {self.agent_id}",
            config=config.model_dump()
        )
    
    def _init_pydantic_agent(self):
        """Initialize the Pydantic AI agent."""
        agent_logger.info(f"🔍 Starting pydantic_ai agent initialization for {self.agent_id}")
        
        if PYDANTIC_AI_AVAILABLE:
            try:
                # Debug: Check available imports
                agent_logger.debug(f"🔍 Pydantic AI imports available: Agent={Agent}, FallbackModel={FallbackModel}")
                
                # Create model configuration
                models = [self.config.model_primary] + self.config.model_fallbacks
                agent_logger.info(
                    f"🔍 Configuring models for {self.agent_id}",
                    primary_model=self.config.model_primary,
                    fallback_models=self.config.model_fallbacks,
                    total_models=len(models),
                    fallback_model_available=FallbackModel is not None
                )
                
                # Debug: Check each model format
                for i, model in enumerate(models):
                    agent_logger.debug(f"🔍 Model {i}: {model} (type: {type(model)})")
                
                # Create model configuration based on what's available
                if FallbackModel is not None:
                    try:
                        model_config = FallbackModel(*models)
                        agent_logger.debug(f"✅ FallbackModel created successfully: {type(model_config)}")
                    except Exception as e:
                        agent_logger.error(f"❌ Failed to create FallbackModel: {type(e).__name__}: {e}")
                        # Try with just primary model
                        agent_logger.info("🔍 Trying with primary model only...")
                        model_config = self.config.model_primary
                else:
                    # Use primary model directly if FallbackModel not available
                    agent_logger.info("🔍 FallbackModel not available, using primary model directly")
                    model_config = self.config.model_primary
                
                # Load system prompt
                agent_logger.debug(f"🔍 Loading system prompt...")
                system_prompt = self._load_system_prompt()
                agent_logger.debug(f"✅ System prompt loaded, length: {len(system_prompt)}")
                
                # Get output type
                output_type = self.get_output_type()
                agent_logger.debug(f"🔍 Output type for agent: {output_type}")
                
                # Create agent with comprehensive debugging
                agent_logger.info(f"🔍 Creating pydantic_ai Agent with parameters:")
                agent_logger.info(f"   - name: {self.agent_id}")
                agent_logger.info(f"   - model: {type(model_config).__name__}")
                agent_logger.info(f"   - result_type: {output_type}")
                agent_logger.info(f"   - retries: {self.config.max_retries}")
                agent_logger.info(f"   - system_prompt length: {len(system_prompt)}")
                
                try:
                    self.ai_agent = Agent(
                        name=self.agent_id,
                        model=model_config,
                        system_prompt=system_prompt,
                        result_type=output_type,
                        retries=self.config.max_retries
                    )
                    agent_logger.info(
                        f"✅ Successfully initialized pydantic_ai agent for {self.agent_id}",
                        agent_type=type(self.ai_agent).__name__,
                        agent_attrs=dir(self.ai_agent)[:10],  # First 10 attributes
                        models_configured=len(models)
                    )
                except Exception as e:
                    agent_logger.error(f"❌ Failed to create Agent instance: {type(e).__name__}: {e}")
                    agent_logger.error(f"   Full error details: {repr(e)}")
                    raise
                    
            except Exception as e:
                agent_logger.error(
                    f"❌ Failed to initialize pydantic_ai agent for {self.agent_id}",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True  # Include full traceback
                )
                self.ai_agent = None
                self.system_prompt = self._load_system_prompt()
        else:
            # Fallback: Store config for direct API calls
            agent_logger.warning(
                f"⚠️  pydantic_ai not available for {self.agent_id} - using mock mode",
                pydantic_ai_available=False,
                pydantic_ai_import_error=PYDANTIC_AI_IMPORT_ERROR
            )
            self.system_prompt = self._load_system_prompt()
            self.ai_agent = None
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file or return default."""
        if self.config.system_prompt_file:
            try:
                prompt_path = os.path.join("config", "prompts", self.config.system_prompt_file)
                with open(prompt_path, "r") as f:
                    return f.read()
            except Exception as e:
                agent_logger.error(
                    f"Failed to load system prompt for {self.agent_id}",
                    error=str(e)
                )
        
        return self.get_default_system_prompt()
    
    @property
    async def redis(self):
        """Get Redis client (lazy loaded)."""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis
    
    @property
    async def supabase(self):
        """Get Supabase client (lazy loaded)."""
        if self._supabase is None:
            from ..storage import get_supabase
            self._supabase = get_supabase()
        return self._supabase
    
    @abstractmethod
    def get_output_type(self) -> Type[BaseModel]:
        """
        Get the output type for this agent.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def get_default_system_prompt(self) -> str:
        """
        Get default system prompt if file not found.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    async def process_request(
        self,
        request: AgentRequest,
        context: AgentContext
    ) -> AgentOutput:
        """
        Process an agent request.
        Must be implemented by subclasses.
        
        Args:
            request: The request to process
            context: Execution context
            
        Returns:
            Agent output
        """
        pass
    
    async def execute(
        self,
        action: str,
        parameters: Dict[str, Any],
        context: AgentContext
    ) -> AgentOutput:
        """
        Execute an agent action.
        
        Args:
            action: Action to perform
            parameters: Action parameters
            context: Execution context
            
        Returns:
            Agent output
        """
        start_time = time.time()
        
        # Create request
        request = AgentRequest(
            from_agent="system",
            to_agent=self.agent_id,
            action=action,
            parameters=parameters,
            context=context.model_dump(mode='json'),
            payload=parameters  # AgentMessage requires payload field
        )
        
        # Log request
        log_agent_request(
            agent_name=self.agent_id,
            action=action,
            input_data=parameters,
            correlation_id=context.correlation_id
        )
        
        try:
            # Process request
            output = await self.process_request(request, context)
            
            # Update metrics
            self.metrics["total_requests"] += 1
            self.metrics["successful_requests"] += 1
            
            # Log response
            processing_time_ms = (time.time() - start_time) * 1000
            log_agent_response(
                agent_name=self.agent_id,
                status="completed",
                processing_time_ms=processing_time_ms,
                output_summary=self._summarize_output(output),
                tokens_used=getattr(output, "tokens_used", None)
            )
            
            # Save to database
            await self._save_output(output, request, context, processing_time_ms)
            
            return output
            
        except Exception as e:
            # Update metrics
            self.metrics["total_requests"] += 1
            self.metrics["failed_requests"] += 1
            
            # Log error
            processing_time_ms = (time.time() - start_time) * 1000
            log_agent_response(
                agent_name=self.agent_id,
                status="failed",
                processing_time_ms=processing_time_ms,
                output_summary={},
                error=str(e)
            )
            
            # Create error output
            output = self._create_error_output(e, request, context)
            
            # Save to database
            await self._save_output(output, request, context, processing_time_ms, str(e))
            
            raise
    
    async def run_llm(
        self,
        prompt: str,
        context: Dict[str, Any],
        temperature: Optional[float] = None
    ) -> Any:
        """
        Run LLM with the configured agent.
        
        Args:
            prompt: User prompt
            context: Additional context
            temperature: Optional temperature override
            
        Returns:
            LLM response
        """
        start_time = time.time()
        
        try:
            # Check if pydantic_ai is available and ai_agent is initialized
            if not PYDANTIC_AI_AVAILABLE or self.ai_agent is None:
                # Return a mock response when pydantic_ai is not available
                agent_logger.warning(
                    "⚠️  Using mock LLM response - Real AI not available",
                    agent_id=self.agent_id,
                    pydantic_ai_available=PYDANTIC_AI_AVAILABLE,
                    ai_agent_initialized=self.ai_agent is not None,
                    pydantic_ai_import_error=PYDANTIC_AI_IMPORT_ERROR,
                    reason="pydantic_ai not imported" if not PYDANTIC_AI_AVAILABLE else "ai_agent not initialized"
                )
                
                # Log mock LLM call
                latency_ms = (time.time() - start_time) * 1000
                log_llm_call(
                    model="mock",
                    provider="mock",
                    prompt_tokens=len(prompt.split()),
                    completion_tokens=50,
                    latency_ms=latency_ms,
                    temperature=temperature or self.config.temperature
                )
                
                # Return a simple mock response
                return f"Mock response for prompt: {prompt[:100]}..."
            
            # Create run context
            run_context = RunContext(deps=context)
            
            agent_logger.info(
                f"🤖 Running REAL AI with pydantic_ai for {self.agent_id}",
                model=self.config.model_primary,
                prompt_preview=prompt[:100] + "..." if len(prompt) > 100 else prompt,
                ai_agent_type=type(self.ai_agent).__name__,
                ai_agent_attrs=dir(self.ai_agent)[:5]  # First 5 attributes
            )
            
            # Debug: Check environment variables
            import os
            agent_logger.debug(
                "🔍 Environment check for AI APIs",
                has_openai_key=bool(os.getenv("OPENAI_API_KEY")),
                has_anthropic_key=bool(os.getenv("ANTHROPIC_API_KEY")),
                openai_key_prefix=os.getenv("OPENAI_API_KEY", "")[:10] + "..." if os.getenv("OPENAI_API_KEY") else "None"
            )
            
            # Run agent
            try:
                agent_logger.debug(f"🔍 Calling ai_agent.run() with prompt length: {len(prompt)}")
                result = await self.ai_agent.run(
                    prompt,
                    context=run_context,
                    model_settings={
                        "temperature": temperature or self.config.temperature
                    }
                )
                agent_logger.debug(f"✅ ai_agent.run() returned: {type(result).__name__}")
            except Exception as e:
                agent_logger.error(f"❌ ai_agent.run() failed: {type(e).__name__}: {e}")
                agent_logger.error(f"   Full error: {repr(e)}")
                raise
            
            # Log LLM call
            latency_ms = (time.time() - start_time) * 1000
            if hasattr(result, "_usage"):
                log_llm_call(
                    model=self.config.model_primary,
                    provider=self.config.model_primary.split(":")[0],
                    prompt_tokens=result._usage.get("prompt_tokens", 0),
                    completion_tokens=result._usage.get("completion_tokens", 0),
                    latency_ms=latency_ms,
                    temperature=temperature or self.config.temperature
                )
            
            agent_logger.info(
                f"✅ Real AI response received for {self.agent_id}",
                latency_ms=latency_ms,
                result_type=type(result).__name__,
                result_attrs=dir(result)[:10] if result else []
            )
            
            return result
            
        except Exception as e:
            # Log failed LLM call
            latency_ms = (time.time() - start_time) * 1000
            log_llm_call(
                model=self.config.model_primary,
                provider=self.config.model_primary.split(":")[0],
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=latency_ms,
                temperature=temperature or self.config.temperature,
                error=str(e)
            )
            raise
    
    async def publish_message(
        self,
        target_agents: Union[str, List[str]],
        message_type: str,
        payload: Dict[str, Any],
        priority: str = "medium"
    ):
        """
        Publish message to other agents.
        
        Args:
            target_agents: Target agent(s)
            message_type: Type of message
            payload: Message payload
            priority: Message priority
        """
        # Ensure target_agents is a list
        if isinstance(target_agents, str):
            target_agents = [target_agents]
        
        # Create message
        message = AgentMessage(
            from_agent=self.agent_id,
            to_agent=target_agents,
            message_type="notification",
            priority=priority,
            payload={
                "type": message_type,
                "data": payload
            }
        )
        
        # Publish to each target
        redis = await self.redis
        for target in target_agents:
            await redis.publish_message(
                channel=target,
                message=message.model_dump(mode='json')
            )
    
    async def subscribe_to_messages(self, callback: callable):
        """
        Subscribe to messages for this agent.
        
        Args:
            callback: Async callback function
        """
        redis = await self.redis
        await redis.subscribe_channel(
            channel=self.agent_id,
            callback=callback
        )
    
    async def cache_result(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ):
        """
        Cache a result.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        redis = await self.redis
        cache_key = f"agent:{self.agent_id}:{key}"
        await redis.set_cache(cache_key, value, ttl)
    
    async def get_cached_result(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Get cached result.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        redis = await self.redis
        cache_key = f"agent:{self.agent_id}:{key}"
        return await redis.get_cache(cache_key, default=default)
    
    def _summarize_output(self, output: AgentOutput) -> Dict[str, Any]:
        """
        Create summary of agent output for logging.
        
        Args:
            output: Agent output
            
        Returns:
            Summary dict
        """
        summary = {
            "output_type": output.output_type,
            "status": output.status,
            "confidence_score": output.confidence_score
        }
        
        # Add type-specific summaries with None checks
        try:
            if hasattr(output, "clarification_questions") and output.clarification_questions is not None:
                summary["question_count"] = len(output.clarification_questions)
            if hasattr(output, "layouts") and output.layouts is not None:
                summary["layout_count"] = len(output.layouts)
            if hasattr(output, "findings") and output.findings is not None:
                summary["finding_count"] = len(output.findings)
            if hasattr(output, "assets") and output.assets is not None:
                summary["asset_count"] = len(output.assets)
            if hasattr(output, "charts") and output.charts is not None:
                summary["chart_count"] = len(output.charts)
            if hasattr(output, "diagrams") and output.diagrams is not None:
                summary["diagram_count"] = len(output.diagrams)
        except Exception as e:
            # Log the error but don't fail - summaries are for logging only
            agent_logger.warning(
                f"Error creating output summary for {self.agent_id}: {e}",
                output_type=output.output_type,
                error=str(e)
            )
        
        return summary
    
    def _create_error_output(
        self,
        error: Exception,
        request: AgentRequest,
        context: AgentContext
    ) -> AgentOutput:
        """
        Create error output.
        
        Args:
            error: The exception
            request: Original request
            context: Execution context
            
        Returns:
            Error output
        """
        return AgentOutput(
            agent_id=self.agent_id,
            output_type="error",
            timestamp=datetime.utcnow(),
            session_id=context.session_id,
            correlation_id=context.correlation_id,
            status="failed",
            confidence_score=0.0,
            metadata={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "action": request.action
            }
        )
    
    async def _save_output(
        self,
        output: AgentOutput,
        request: AgentRequest,
        context: AgentContext,
        processing_time_ms: float,
        error_message: Optional[str] = None
    ):
        """
        Save agent output to database.
        
        Args:
            output: Agent output
            request: Original request
            context: Execution context
            processing_time_ms: Processing time
            error_message: Optional error message
        """
        try:
            supabase = await self.supabase
            result = await supabase.save_agent_output(
                session_id=context.session_id,
                agent_id=self.agent_id,
                output_type=output.output_type,
                correlation_id=context.correlation_id,
                status=output.status,
                input_data=request.parameters,
                output_data=output.model_dump(mode='json'),
                processing_time_ms=int(processing_time_ms),
                tokens_used=getattr(output, "tokens_used", None),
                error_message=error_message
            )
            
            if result is None:
                # RLS policy prevented save, but workflow continues
                agent_logger.debug(f"Agent output save blocked by RLS policy for {self.agent_id}, continuing normally")
            else:
                agent_logger.debug(f"Agent output saved successfully for {self.agent_id}")
                
        except Exception as e:
            # Handle any other exceptions that weren't caught by save_agent_output
            log_error(e, "agent_output_save_failed", {
                "agent_id": self.agent_id,
                "session_id": context.session_id
            })
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.
        
        Returns:
            Health status
        """
        try:
            # Check Redis
            redis = await self.redis
            redis_healthy = await redis.health_check()
            
            # Check Supabase
            supabase = await self.supabase
            supabase_healthy = await supabase.health_check()
            
            # Check LLM (simple prompt)
            llm_healthy = False
            try:
                await self.run_llm("ping", {})
                llm_healthy = True
            except:
                pass
            
            return {
                "agent_id": self.agent_id,
                "status": "healthy" if all([redis_healthy, supabase_healthy, llm_healthy]) else "degraded",
                "checks": {
                    "redis": redis_healthy,
                    "supabase": supabase_healthy,
                    "llm": llm_healthy
                },
                "metrics": self.metrics
            }
        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "status": "unhealthy",
                "error": str(e),
                "metrics": self.metrics
            }


# Export
__all__ = ['BaseAgent', 'AgentConfig', 'AgentContext']