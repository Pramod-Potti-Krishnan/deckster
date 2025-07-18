# PydanticAI Best Practices Guide for Agent Development

## Executive Summary

PydanticAI is a powerful Python framework designed for building production-grade applications with Large Language Models (LLMs). It combines the robustness of Pydantic's data validation with a flexible agent-based architecture, making it ideal for building sophisticated AI-powered applications like Deckster. This guide provides comprehensive best practices for leveraging PydanticAI to build efficient, maintainable, and scalable agents.

### Why PydanticAI for Deckster?
- **Type Safety**: Leverages Python's type hints and Pydantic's validation
- **Model Agnostic**: Supports multiple LLM providers with a unified interface
- **Production Ready**: Built-in error handling, retries, and validation
- **Flexible Architecture**: Easy to extend with tools and custom behaviors
- **Streaming Support**: Efficient handling of real-time responses

---

## Core Concepts - Detailed Coverage

### 1. Agents - The Heart of PydanticAI

#### What Are Agents?

In plain English, an agent is like a smart assistant that can understand requests, think about them using an LLM, and produce structured responses. Agents can be enhanced with tools (functions they can call) and can work with dependencies (shared resources like databases or APIs). Think of an agent as a specialized employee who knows how to handle specific types of requests.

#### Agent Architecture and Components

```python
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import Optional

# Basic agent creation
simple_agent = Agent('openai:gpt-4o')

# Agent with type-safe output
class PresentationPlan(BaseModel):
    title: str
    slide_count: int
    key_themes: list[str]
    estimated_duration: int  # in minutes

typed_agent = Agent(
    'openai:gpt-4o',
    output_type=PresentationPlan,
    instructions="You are a presentation planning expert."
)
```

#### Best Practices for Agent Creation

**1. Always Define Clear Instructions**

```python
presentation_agent = Agent(
    'openai:gpt-4o',
    instructions="""
You are a presentation creation expert for Deckster. Your role is to:
1. Understand user requirements thoroughly
2. Create well-structured, engaging presentations
3. Ensure content is appropriate for the target audience
4. Follow best practices for slide design and flow

Always be concise, professional, and focused on the user's goals.
"""
)
```

**2. Use Type-Safe Outputs for Structured Data**

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class SlideContent(BaseModel):
    title: str = Field(description="Slide title, max 10 words")
    content: List[str] = Field(description="Bullet points, max 5 items")
    speaker_notes: Optional[str] = Field(default=None, description="Notes for presenter")
    visual_suggestion: Optional[str] = Field(default=None, description="Suggested visuals")

class PresentationStrawman(BaseModel):
    title: str
    slides: List[SlideContent]
    theme_suggestions: List[str]
    
strawman_agent = Agent(
    'openai:gpt-4o',
    output_type=PresentationStrawman,
    instructions="Create detailed presentation structures with practical content."
)
```

**3. Leverage Dependencies for Stateful Operations**

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class AgentDependencies:
    """Dependencies shared across agent operations"""
    session_manager: Any  # Your session manager
    supabase_client: Any  # Database client
    user_preferences: Dict[str, Any]
    current_state: str

# Agent with dependencies
stateful_agent = Agent(
    'openai:gpt-4o',
    deps_type=AgentDependencies,
    instructions="You have access to session data and user preferences."
)

# Using the agent with dependencies
async def process_request(deps: AgentDependencies, user_input: str):
    result = await stateful_agent.run(
        user_input,
        deps=deps
    )
    return result
```

**4. Implement Robust Error Handling**

```python
from pydantic_ai import Agent, ModelRetry

async def safe_agent_run(agent: Agent, prompt: str, max_retries: int = 3):
    """Run agent with comprehensive error handling"""
    try:
        result = await agent.run(
            prompt,
            message_history=[],  # Include relevant history
            usage_limits={'total_tokens': 4000}  # Set token limits
        )
        return result
    except ModelRetry as e:
        # Handle retryable errors
        logger.warning(f"Model retry needed: {e}")
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Agent error: {e}")
        return None
```

#### Integration with Deckster's Workflow States

```python
from enum import Enum

class WorkflowState(str, Enum):
    PROVIDE_GREETING = "PROVIDE_GREETING"
    ASK_CLARIFYING_QUESTIONS = "ASK_CLARIFYING_QUESTIONS"
    CREATE_CONFIRMATION_PLAN = "CREATE_CONFIRMATION_PLAN"
    GENERATE_STRAWMAN = "GENERATE_STRAWMAN"
    REFINE_STRAWMAN = "REFINE_STRAWMAN"

# State-specific agents
greeting_agent = Agent(
    'openai:gpt-4o',
    instructions="Provide warm, professional greetings and ask about presentation needs."
)

clarification_agent = Agent(
    'openai:gpt-4o',
    output_type=List[str],  # List of questions
    instructions="Generate 3-5 clarifying questions about the presentation."
)

# Unified agent with state awareness
class UnifiedAgent:
    def __init__(self, model: str = 'openai:gpt-4o'):
        self.agents = {
            WorkflowState.PROVIDE_GREETING: greeting_agent,
            WorkflowState.ASK_CLARIFYING_QUESTIONS: clarification_agent,
            # ... other state-specific agents
        }
    
    async def process(self, state: WorkflowState, context: Dict[str, Any]):
        agent = self.agents.get(state)
        if not agent:
            raise ValueError(f"No agent configured for state: {state}")
        
        # State-specific processing
        return await agent.run(context.get('user_input', ''))
```

### 2. Tools - Extending Agent Capabilities

#### Understanding Tools

Tools are functions that agents can call during their execution. Think of tools as specialized abilities you give to your agent - like giving a presentation assistant the ability to search for images, check facts, or format content. Tools make agents more capable and interactive.

#### Tool Creation Patterns

**Basic Tool Implementation**

```python
from pydantic_ai import Agent, RunContext, Tool
from typing import Dict, Any

def create_presentation_agent_with_tools():
    agent = Agent('openai:gpt-4o')
    
    @agent.tool
    async def search_images(ctx: RunContext[Dict[str, Any]], query: str) -> List[str]:
        """Search for relevant images for the presentation.
        
        Args:
            query: Search query for images
            
        Returns:
            List of image URLs
        """
        # Implementation would connect to image search API
        print(f"Searching images for: {query}")
        return ["image1.jpg", "image2.jpg"]  # Placeholder
    
    @agent.tool
    async def validate_facts(ctx: RunContext[Dict[str, Any]], statement: str) -> Dict[str, Any]:
        """Validate factual claims in presentation content.
        
        Args:
            statement: The statement to fact-check
            
        Returns:
            Validation result with confidence score
        """
        # Implementation would use fact-checking service
        return {
            "statement": statement,
            "is_valid": True,
            "confidence": 0.95,
            "source": "Internal knowledge base"
        }
    
    return agent
```

**Advanced Tool with RunContext Usage**

```python
from pydantic_ai import RunContext
from pydantic import BaseModel

class SessionDeps(BaseModel):
    session_id: str
    user_id: str
    session_manager: Any
    current_state: str

async def advanced_tool_example(
    ctx: RunContext[SessionDeps], 
    action: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """Advanced tool leveraging RunContext features."""
    
    # Access dependencies
    session_id = ctx.deps.session_id
    session_manager = ctx.deps.session_manager
    
    # Access conversation context
    message_count = len(ctx.messages)
    current_prompt = ctx.prompt
    
    # Access model information
    model_name = ctx.model.name
    
    # Track usage
    if ctx.usage:
        tokens_used = ctx.usage.total_tokens
    
    # Perform action based on context
    if action == "save_progress":
        await session_manager.save_session_data(
            session_id,
            ctx.deps.user_id,
            "progress",
            data
        )
        return {"status": "saved", "session_id": session_id}
    
    return {"status": "completed", "action": action}
```

**Tool Registration Patterns**

```python
# Method 1: Decorator pattern (recommended for most cases)
agent = Agent('openai:gpt-4o')

@agent.tool
async def my_tool(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

# Method 2: Explicit Tool creation
from pydantic_ai import Tool

def multiply(x: int, y: int) -> int:
    """Multiply two numbers."""
    return x * y

agent = Agent(
    'openai:gpt-4o',
    tools=[Tool(multiply, name="multiplier")]
)

# Method 3: Dynamic tool registration with preparation
async def prepare_tool(ctx: RunContext[Any], tool_def: Any) -> Any:
    """Conditionally register tool based on context."""
    if ctx.deps and hasattr(ctx.deps, 'enable_advanced_tools'):
        if ctx.deps.enable_advanced_tools:
            return tool_def
    return None

advanced_tool = Tool(
    advanced_function,
    prepare=prepare_tool,
    description="Advanced tool with conditional availability"
)
```

#### Best Practices for Tool Implementation

**1. Clear, Descriptive Names and Docstrings**

```python
@agent.tool
async def generate_slide_outline(
    topic: str,
    max_points: int = 5,
    include_examples: bool = True
) -> Dict[str, Any]:
    """Generate a structured outline for a presentation slide.
    
    This tool creates a hierarchical outline with main points and sub-points
    suitable for a single slide in a presentation.
    
    Args:
        topic: The main topic or title of the slide
        max_points: Maximum number of main points (default: 5)
        include_examples: Whether to include example content (default: True)
        
    Returns:
        Dictionary containing:
        - title: Slide title
        - main_points: List of main points with sub-points
        - examples: Optional examples for each point
    """
    # Implementation
    pass
```

**2. Error Handling in Tools**

```python
from pydantic_ai import ToolRetryError

@agent.tool(max_retries=3)
async def fetch_data_with_retry(
    ctx: RunContext[Any],
    endpoint: str
) -> Dict[str, Any]:
    """Fetch data with automatic retry logic."""
    try:
        # Attempt to fetch data
        response = await external_api_call(endpoint)
        if response.status_code != 200:
            # This will trigger a retry
            raise ToolRetryError(f"API returned {response.status_code}")
        return response.json()
    except ConnectionError as e:
        # This will also trigger a retry
        raise ToolRetryError(f"Connection failed: {e}")
    except Exception as e:
        # This will not retry - permanent failure
        logger.error(f"Permanent error in fetch_data: {e}")
        return {"error": str(e), "status": "failed"}
```

**3. Tool Composition and Modularity**

```python
class PresentationToolkit:
    """Modular toolkit for presentation-related tools"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.image_service = ImageSearchService(config['image_api_key'])
        self.fact_checker = FactCheckService(config['fact_api_key'])
    
    def register_tools(self, agent: Agent):
        """Register all tools with the agent"""
        
        @agent.tool
        async def search_images(query: str, count: int = 5) -> List[str]:
            """Search for presentation images"""
            return await self.image_service.search(query, count)
        
        @agent.tool
        async def check_facts(statements: List[str]) -> List[Dict[str, Any]]:
            """Verify factual claims"""
            return await self.fact_checker.verify_batch(statements)
        
        @agent.tool
        async def format_slide(content: Dict[str, Any]) -> str:
            """Format content for slide display"""
            return self._format_slide_content(content)
        
        return agent
    
    def _format_slide_content(self, content: Dict[str, Any]) -> str:
        """Internal formatting logic"""
        # Implementation
        pass

# Usage
toolkit = PresentationToolkit(config)
agent = Agent('openai:gpt-4o')
agent = toolkit.register_tools(agent)
```

### 3. Base Models - Provider Abstraction Layer

#### Understanding the Model Abstraction

PydanticAI's base model system provides a unified interface for working with different LLM providers. This abstraction means you can switch between OpenAI, Anthropic, Google, and other providers without changing your agent code. It's like having a universal remote that works with all TV brands.

#### Working with Different Providers

```python
from pydantic_ai import Agent

# Different providers, same interface
openai_agent = Agent('openai:gpt-4o')
anthropic_agent = Agent('anthropic:claude-3-sonnet')
google_agent = Agent('google:gemini-pro')
groq_agent = Agent('groq:mixtral-8x7b-32768')

# Provider-specific configuration
from pydantic_ai.models.openai import OpenAIModel

custom_openai = OpenAIModel(
    'gpt-4o',
    api_key='your-api-key',  # Or use environment variable
    organization='your-org-id',
    base_url='https://api.openai.com/v1'  # For proxies or custom endpoints
)

agent_with_custom_model = Agent(model=custom_openai)
```

#### Custom Model Implementation Guide

```python
from pydantic_ai.models.base import Model
from pydantic_ai import UsageInfo
from typing import AsyncIterator, Dict, Any, List
import httpx

class CustomLLMModel(Model):
    """Custom model implementation for proprietary LLM"""
    
    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: str,
        **kwargs
    ):
        self.model_name_str = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"}
        )
        super().__init__(**kwargs)
    
    @property
    def model_name(self) -> str:
        """Return the model name"""
        return self.model_name_str
    
    async def request(
        self,
        messages: List[Dict[str, Any]],
        *,
        model_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the model"""
        
        # Prepare request payload
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": model_settings.get("temperature", 0.7) if model_settings else 0.7,
            "max_tokens": model_settings.get("max_tokens", 1000) if model_settings else 1000
        }
        
        # Make API request
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload
        )
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        return {
            "content": data["choices"][0]["message"]["content"],
            "usage": UsageInfo(
                input_tokens=data["usage"]["prompt_tokens"],
                output_tokens=data["usage"]["completion_tokens"],
                total_tokens=data["usage"]["total_tokens"]
            )
        }
    
    async def request_stream(
        self,
        messages: List[Dict[str, Any]],
        *,
        model_settings: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream responses from the model"""
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "temperature": model_settings.get("temperature", 0.7) if model_settings else 0.7
        }
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield self._parse_stream_chunk(line[6:])

# Usage
custom_model = CustomLLMModel(
    model_name="custom-llm-v1",
    api_key="your-api-key",
    base_url="https://your-llm-api.com"
)

agent = Agent(model=custom_model)
```

#### Provider-Specific Considerations

**OpenAI**
```python
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

openai_agent = Agent(
    'openai:gpt-4o',
    model_settings=ModelSettings(
        temperature=0.7,
        max_tokens=2000,
        top_p=0.9,
        presence_penalty=0.1,
        frequency_penalty=0.1,
        seed=42  # For more deterministic outputs
    )
)

# OpenAI-specific features
openai_agent_with_tools = Agent(
    'openai:gpt-4o',
    model_settings=ModelSettings(
        parallel_tool_calls=True,  # OpenAI supports parallel tool execution
        response_format={"type": "json_object"}  # JSON mode
    )
)
```

**Anthropic (Claude)**
```python
anthropic_agent = Agent(
    'anthropic:claude-3-opus',
    instructions="""You are Claude, an AI assistant created by Anthropic.
    
    Important: Claude models perform best with clear, detailed instructions
    and benefit from chain-of-thought reasoning.""",
    model_settings=ModelSettings(
        temperature=0.7,
        max_tokens=4000,  # Claude supports larger outputs
        stop_sequences=["Human:", "Assistant:"]  # Claude-specific stop sequences
    )
)
```

**Google (Gemini)**
```python
gemini_agent = Agent(
    'google:gemini-pro',
    model_settings=ModelSettings(
        temperature=0.7,
        max_tokens=2048,
        top_p=0.95,
        # Gemini has different safety settings
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE"
        }
    )
)
```

### 4. MCP (Model Context Protocol) - Advanced Integration

#### What is MCP and When to Use It

Model Context Protocol (MCP) is a standardized way to run and communicate with external tools and services. Think of MCP as a universal adapter that lets your AI agents connect to various external systems - whether they're running as local processes, web services, or specialized tools. 

Use MCP when you need to:
- Integrate with external tools that run as separate processes
- Connect to specialized services (like code execution environments)
- Maintain security boundaries between your agent and external systems
- Scale tool execution across different environments

#### Setting Up MCP Servers

**Basic MCP Server Setup**

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
import asyncio

# Create an MCP server that runs as a subprocess
code_executor_server = MCPServerStdio(
    'python',
    args=[
        'mcp_code_executor.py',
        '--mode', 'safe',
        '--timeout', '30'
    ],
    env={'PYTHONPATH': '/path/to/libs'}  # Custom environment
)

# Create agent with MCP server
agent = Agent(
    'openai:gpt-4o',
    mcp_servers=[code_executor_server],
    instructions="You can execute Python code using the code execution tool."
)

# Use the agent with MCP
async def main():
    async with agent.run_mcp_servers():
        result = await agent.run(
            "Calculate the fibonacci sequence up to n=10"
        )
        print(result.output)

asyncio.run(main())
```

**Advanced MCP Configuration**

```python
from pydantic_ai.mcp import MCPServerSSE, MCPServerStreamableHTTP
from datetime import timedelta

# Server-Sent Events MCP Server (for web-based tools)
web_tool_server = MCPServerSSE(
    base_url="https://your-tool-api.com",
    headers={"Authorization": "Bearer your-token"},
    timeout=timedelta(seconds=60),
    tool_prefix="web_",  # Prefix all tools from this server
    log_level="INFO"
)

# HTTP Streaming MCP Server
streaming_server = MCPServerStreamableHTTP(
    base_url="https://streaming-api.com",
    sampling_enabled=True,  # Enable request sampling
    sample_rate=0.1,  # Sample 10% of requests
    timeout=timedelta(seconds=120)
)

# Multiple MCP servers with different capabilities
multi_server_agent = Agent(
    'openai:gpt-4o',
    mcp_servers=[
        code_executor_server,
        web_tool_server,
        streaming_server
    ],
    instructions="""You have access to multiple tools:
    - Code execution (python code)
    - Web tools (prefixed with 'web_')
    - Streaming data tools
    Use them appropriately based on the task."""
)
```

#### Security and Debugging Considerations

**Security Best Practices**

```python
from pydantic_ai.mcp import MCPServerStdio
import os
import tempfile

class SecureMCPServer:
    """Secure MCP server implementation with sandboxing"""
    
    def __init__(self, allowed_commands: List[str]):
        self.allowed_commands = allowed_commands
        self.sandbox_dir = tempfile.mkdtemp()
    
    def create_server(self, command: str, args: List[str]) -> MCPServerStdio:
        """Create a sandboxed MCP server"""
        
        # Validate command
        if command not in self.allowed_commands:
            raise ValueError(f"Command {command} not allowed")
        
        # Create restricted environment
        restricted_env = {
            'PATH': '/usr/bin:/bin',  # Limited PATH
            'HOME': self.sandbox_dir,
            'TMPDIR': self.sandbox_dir,
            # Don't include sensitive environment variables
        }
        
        # Remove potentially dangerous arguments
        safe_args = [arg for arg in args if not arg.startswith('--unsafe')]
        
        return MCPServerStdio(
            command,
            args=safe_args,
            env=restricted_env,
            cwd=self.sandbox_dir  # Restrict working directory
        )
    
    def cleanup(self):
        """Clean up sandbox directory"""
        import shutil
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)

# Usage
secure_server = SecureMCPServer(allowed_commands=['python', 'node'])
mcp_server = secure_server.create_server('python', ['safe_script.py'])
```

**Debugging MCP Connections**

```python
import logging
from pydantic_ai.mcp import MCPServerStdio

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('mcp_debug')

def custom_log_handler(level: str, message: str):
    """Custom handler for MCP logs"""
    logger.log(
        getattr(logging, level.upper()),
        f"MCP: {message}"
    )

# Create server with debug logging
debug_server = MCPServerStdio(
    'problematic_tool',
    args=['--verbose'],
    log_level='DEBUG',
    log_handler=custom_log_handler,
    timeout=timedelta(seconds=30)
)

# Monitor MCP interactions
async def debug_mcp_agent():
    agent = Agent(
        'openai:gpt-4o',
        mcp_servers=[debug_server]
    )
    
    try:
        async with agent.run_mcp_servers():
            # Log server initialization
            logger.info("MCP servers initialized")
            
            # Run with detailed error tracking
            result = await agent.run(
                "Test the MCP tool",
                usage_limits={'request_tokens': 1000}
            )
            
            # Log usage
            if result.usage:
                logger.info(f"Tokens used: {result.usage.total_tokens}")
                
    except Exception as e:
        logger.error(f"MCP error: {e}", exc_info=True)
        raise
```

#### Use Cases for Deckster

**1. Document Processing MCP Server**

```python
# mcp_document_processor.py
from pydantic_ai.mcp import create_stdio_server
import asyncio

async def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from PDF files"""
    # Implementation using PyPDF2 or similar
    pass

async def process_markdown(content: str) -> Dict[str, Any]:
    """Process markdown content into structured format"""
    # Implementation
    pass

# Create MCP server for document processing
document_server = MCPServerStdio(
    'python',
    args=['mcp_document_processor.py'],
    description="Process various document formats for presentations"
)

# Integration with Deckster
presentation_agent = Agent(
    'openai:gpt-4o',
    mcp_servers=[document_server],
    instructions="""When users upload documents, use the document processing
    tools to extract and structure content for presentations."""
)
```

**2. Real-time Data Integration**

```python
# MCP server for real-time data
realtime_data_server = MCPServerSSE(
    base_url="https://data-api.deckster.com",
    headers={"API-Key": os.getenv("DATA_API_KEY")},
    tool_prefix="data_"
)

# Agent that can fetch live data for presentations
data_aware_agent = Agent(
    'openai:gpt-4o',
    mcp_servers=[realtime_data_server],
    instructions="""You can fetch real-time data for presentations.
    Use data_ prefixed tools to get current statistics, charts, and metrics."""
)
```

---

## Supporting Concepts - Brief Coverage

### Output Handling and Validation
PydanticAI provides multiple output strategies for structured data generation. Use `ToolOutput` for maximum control, `NativeOutput` for model-native structured outputs, or `PromptedOutput` for template-based generation.
- Documentation: https://ai.pydantic.dev/api/output/

### Result Streaming and Processing
The `StreamedRunResult` class enables real-time processing of model outputs with partial validation support. Essential for responsive user experiences.
- Documentation: https://ai.pydantic.dev/api/result/

### Message Handling
Comprehensive message tracking and history management for maintaining conversation context across agent interactions.
- Documentation: https://ai.pydantic.dev/api/messages/

### Settings and Configuration
`ModelSettings` provides fine-grained control over LLM behavior including temperature, token limits, penalties, and provider-specific options.
- Documentation: https://ai.pydantic.dev/api/settings/

### Usage Tracking
Built-in usage monitoring for tracking token consumption, request counts, and computational resources across agent operations.
- Documentation: https://ai.pydantic.dev/api/usage/

### Error Handling and Exceptions
Robust exception hierarchy for handling model errors, validation failures, and runtime issues with built-in retry mechanisms.
- Documentation: https://ai.pydantic.dev/api/exceptions/

### Common Tools
Pre-built tools for web search (DuckDuckGo, Tavily) that can be easily integrated into agents for information retrieval.
- Documentation: https://ai.pydantic.dev/api/common_tools/

### Format Utilities
XML formatting utilities for structured prompt engineering and complex data representation in LLM contexts.
- Documentation: https://ai.pydantic.dev/api/format_as_xml/

### Direct Model Access
Low-level model access for advanced use cases requiring direct control over model interactions.
- Documentation: https://ai.pydantic.dev/api/direct/

### Model-Specific Features
Each provider (OpenAI, Anthropic, Google, etc.) has specific features and optimizations documented in their respective modules.
- OpenAI: https://ai.pydantic.dev/api/models/openai/
- Anthropic: https://ai.pydantic.dev/api/models/anthropic/
- Google: https://ai.pydantic.dev/api/models/google/

---

## Best Practices for Deckster Agent Development

### Agent Design Patterns for Workflow States

**1. State-Specific Agent Pattern**

```python
from typing import Protocol, Dict, Any
from pydantic_ai import Agent

class StateAgent(Protocol):
    """Protocol for state-specific agents"""
    async def process(self, context: Dict[str, Any]) -> Any:
        ...

class GreetingStateAgent:
    def __init__(self):
        self.agent = Agent(
            'openai:gpt-4o',
            instructions="""Provide a warm, professional greeting.
            Ask what kind of presentation they need help with.
            Keep it brief and friendly."""
        )
    
    async def process(self, context: Dict[str, Any]) -> str:
        is_returning = context.get('is_returning_user', False)
        prompt = "Greet a returning user" if is_returning else "Greet a new user"
        result = await self.agent.run(prompt)
        return result.output

class ClarificationStateAgent:
    def __init__(self):
        self.agent = Agent(
            'openai:gpt-4o',
            output_type=List[str],
            instructions="""Generate 3-5 clarifying questions based on the user's
            presentation topic. Focus on audience, purpose, duration, and key messages."""
        )
    
    async def process(self, context: Dict[str, Any]) -> List[str]:
        topic = context.get('user_initial_request', '')
        result = await self.agent.run(f"Generate clarifying questions for: {topic}")
        return result.output
```

**2. Unified Agent with State Routing**

```python
class UnifiedWorkflowAgent:
    """Single agent that handles all states with dynamic instructions"""
    
    def __init__(self):
        self.agent = Agent('openai:gpt-4o')
        self.state_instructions = {
            WorkflowState.PROVIDE_GREETING: self._greeting_instructions,
            WorkflowState.ASK_CLARIFYING_QUESTIONS: self._clarification_instructions,
            WorkflowState.CREATE_CONFIRMATION_PLAN: self._planning_instructions,
            WorkflowState.GENERATE_STRAWMAN: self._generation_instructions,
            WorkflowState.REFINE_STRAWMAN: self._refinement_instructions
        }
    
    async def process(self, state: WorkflowState, context: Dict[str, Any]) -> Any:
        # Get state-specific instructions
        instruction_builder = self.state_instructions.get(state)
        if not instruction_builder:
            raise ValueError(f"Unknown state: {state}")
        
        instructions = instruction_builder(context)
        
        # Update agent instructions dynamically
        self.agent.instructions = instructions
        
        # Process based on state
        prompt = self._build_prompt(state, context)
        result = await self.agent.run(prompt)
        
        return self._parse_output(state, result)
    
    def _greeting_instructions(self, context: Dict[str, Any]) -> str:
        return "Provide a warm greeting and ask about presentation needs."
    
    def _clarification_instructions(self, context: Dict[str, Any]) -> str:
        return f"""Generate 3-5 clarifying questions for a presentation about:
        {context.get('user_initial_request', 'unknown topic')}
        Focus on audience, duration, key messages, and purpose."""
```

### Dependency Injection Strategies

**1. Layered Dependencies Pattern**

```python
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class CoreDependencies:
    """Core dependencies available to all agents"""
    supabase_client: Any
    session_manager: Any
    logger: Any

@dataclass
class StateSpecificDeps(CoreDependencies):
    """Extended dependencies for specific states"""
    current_state: str
    session_id: str
    user_id: str
    
    # Optional state-specific resources
    image_service: Optional[Any] = None
    fact_checker: Optional[Any] = None
    template_engine: Optional[Any] = None

# Dependency factory
class DependencyFactory:
    def __init__(self, core_deps: CoreDependencies):
        self.core = core_deps
        self.state_resources = {
            WorkflowState.GENERATE_STRAWMAN: {
                'image_service': ImageSearchService(),
                'template_engine': SlideTemplateEngine()
            },
            WorkflowState.REFINE_STRAWMAN: {
                'fact_checker': FactCheckService()
            }
        }
    
    def create_deps(self, state: str, session_id: str, user_id: str) -> StateSpecificDeps:
        """Create dependencies for a specific state"""
        resources = self.state_resources.get(state, {})
        
        return StateSpecificDeps(
            supabase_client=self.core.supabase_client,
            session_manager=self.core.session_manager,
            logger=self.core.logger,
            current_state=state,
            session_id=session_id,
            user_id=user_id,
            **resources
        )
```

**2. Context-Aware Dependencies**

```python
from pydantic_ai import Agent, RunContext

@dataclass
class SmartDependencies:
    """Dependencies that adapt based on context"""
    
    def __init__(self, base_config: Dict[str, Any]):
        self.base_config = base_config
        self._cache = {}
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Lazily load user preferences"""
        if user_id not in self._cache:
            # Load from database
            prefs = await self._load_user_preferences(user_id)
            self._cache[user_id] = prefs
        return self._cache[user_id]
    
    async def get_templates(self, style: str) -> List[Dict[str, Any]]:
        """Get presentation templates based on style"""
        # Implementation
        pass

# Agent using smart dependencies
agent = Agent(
    'openai:gpt-4o',
    deps_type=SmartDependencies
)

@agent.tool
async def apply_user_style(ctx: RunContext[SmartDependencies], content: Dict[str, Any]) -> Dict[str, Any]:
    """Apply user's preferred styling to content"""
    user_prefs = await ctx.deps.get_user_preferences(ctx.user_id)
    style = user_prefs.get('presentation_style', 'default')
    templates = await ctx.deps.get_templates(style)
    
    # Apply styling
    return apply_template(content, templates[0])
```

### Tool Organization for Presentation Tasks

**1. Tool Categories and Organization**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ToolCategory(ABC):
    """Base class for tool categories"""
    
    @abstractmethod
    def register_tools(self, agent: Agent) -> None:
        """Register all tools in this category"""
        pass

class ContentTools(ToolCategory):
    """Tools for content generation and manipulation"""
    
    def register_tools(self, agent: Agent) -> None:
        @agent.tool
        async def generate_bullet_points(topic: str, count: int = 5) -> List[str]:
            """Generate bullet points for a topic"""
            # Implementation
            pass
        
        @agent.tool
        async def summarize_text(text: str, max_words: int = 100) -> str:
            """Summarize text content"""
            # Implementation
            pass
        
        @agent.tool
        async def expand_outline(outline: List[str]) -> Dict[str, List[str]]:
            """Expand outline points into detailed content"""
            # Implementation
            pass

class VisualizationTools(ToolCategory):
    """Tools for visual content and formatting"""
    
    def register_tools(self, agent: Agent) -> None:
        @agent.tool
        async def suggest_chart_type(data_description: str) -> str:
            """Suggest appropriate chart type for data"""
            # Implementation
            pass
        
        @agent.tool
        async def create_layout(slide_content: Dict[str, Any]) -> Dict[str, Any]:
            """Create slide layout recommendation"""
            # Implementation
            pass

class ValidationTools(ToolCategory):
    """Tools for content validation and quality checks"""
    
    def register_tools(self, agent: Agent) -> None:
        @agent.tool
        async def check_readability(text: str) -> Dict[str, float]:
            """Check text readability scores"""
            # Implementation
            pass
        
        @agent.tool
        async def validate_facts(claims: List[str]) -> List[Dict[str, Any]]:
            """Validate factual claims"""
            # Implementation
            pass

# Tool registry pattern
class PresentationToolRegistry:
    def __init__(self):
        self.categories = {
            'content': ContentTools(),
            'visualization': VisualizationTools(),
            'validation': ValidationTools()
        }
    
    def register_all(self, agent: Agent) -> Agent:
        """Register all tool categories with agent"""
        for category in self.categories.values():
            category.register_tools(agent)
        return agent
    
    def register_category(self, agent: Agent, category_name: str) -> Agent:
        """Register specific tool category"""
        if category_name in self.categories:
            self.categories[category_name].register_tools(agent)
        return agent
```

**2. State-Specific Tool Loading**

```python
class StateAwareToolLoader:
    """Load tools based on workflow state"""
    
    def __init__(self):
        self.state_tools = {
            WorkflowState.GENERATE_STRAWMAN: [
                'content_generation',
                'visualization',
                'research'
            ],
            WorkflowState.REFINE_STRAWMAN: [
                'content_refinement',
                'validation',
                'formatting'
            ]
        }
    
    def create_agent_for_state(self, state: WorkflowState, model: str = 'openai:gpt-4o') -> Agent:
        """Create agent with state-appropriate tools"""
        agent = Agent(model)
        
        # Load base tools
        self._load_base_tools(agent)
        
        # Load state-specific tools
        tool_categories = self.state_tools.get(state, [])
        for category in tool_categories:
            self._load_tool_category(agent, category)
        
        return agent
    
    def _load_base_tools(self, agent: Agent):
        """Load tools needed by all states"""
        @agent.tool
        async def save_progress(data: Dict[str, Any]) -> bool:
            """Save current progress"""
            # Implementation
            return True
    
    def _load_tool_category(self, agent: Agent, category: str):
        """Load specific tool category"""
        # Implementation based on category
        pass
```

### Testing and Debugging Agents

**1. Agent Testing Framework**

```python
import pytest
from unittest.mock import Mock, AsyncMock
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

class AgentTestFramework:
    """Comprehensive testing utilities for agents"""
    
    @staticmethod
    def create_test_agent(
        output_type=str,
        instructions: str = "Test instructions",
        tools: List[Any] = None
    ) -> Agent:
        """Create agent with test model"""
        # Use deterministic test model
        test_model = TestModel(
            responses=[
                "Test response 1",
                "Test response 2"
            ]
        )
        
        agent = Agent(
            model=test_model,
            output_type=output_type,
            instructions=instructions,
            tools=tools or []
        )
        
        return agent
    
    @staticmethod
    async def test_agent_output(agent: Agent, test_cases: List[Dict[str, Any]]):
        """Test agent with multiple cases"""
        results = []
        
        for case in test_cases:
            result = await agent.run(
                case['input'],
                deps=case.get('deps'),
                message_history=case.get('history', [])
            )
            
            results.append({
                'input': case['input'],
                'expected': case['expected'],
                'actual': result.output,
                'passed': result.output == case['expected']
            })
        
        return results

# Example test
async def test_clarification_agent():
    """Test clarification question generation"""
    
    # Create test agent
    agent = AgentTestFramework.create_test_agent(
        output_type=List[str],
        instructions="Generate clarifying questions"
    )
    
    # Define test cases
    test_cases = [
        {
            'input': 'Create a presentation about AI',
            'expected': [
                "Who is your target audience?",
                "How long should the presentation be?",
                "What key messages do you want to convey?"
            ]
        }
    ]
    
    # Run tests
    results = await AgentTestFramework.test_agent_output(agent, test_cases)
    
    # Validate
    assert all(r['passed'] for r in results)
```

**2. Debugging Utilities**

```python
import logging
from functools import wraps
from typing import Any, Callable
import json

class AgentDebugger:
    """Debugging utilities for agent development"""
    
    def __init__(self, log_level: str = "DEBUG"):
        self.logger = logging.getLogger("agent_debug")
        self.logger.setLevel(getattr(logging, log_level))
        
        # Add console handler with formatting
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def trace_tool(self, tool_func: Callable) -> Callable:
        """Decorator to trace tool execution"""
        @wraps(tool_func)
        async def wrapper(*args, **kwargs):
            tool_name = tool_func.__name__
            self.logger.debug(f"Tool '{tool_name}' called with args: {args}, kwargs: {kwargs}")
            
            try:
                result = await tool_func(*args, **kwargs)
                self.logger.debug(f"Tool '{tool_name}' returned: {result}")
                return result
            except Exception as e:
                self.logger.error(f"Tool '{tool_name}' failed: {e}", exc_info=True)
                raise
        
        return wrapper
    
    def log_agent_interaction(self, agent: Agent) -> Agent:
        """Wrap agent to log all interactions"""
        original_run = agent.run
        
        async def logged_run(*args, **kwargs):
            self.logger.info(f"Agent run called with prompt: {args[0] if args else kwargs.get('prompt')}")
            
            # Log dependencies if present
            if 'deps' in kwargs:
                self.logger.debug(f"Dependencies: {kwargs['deps']}")
            
            # Execute
            result = await original_run(*args, **kwargs)
            
            # Log result
            self.logger.info(f"Agent output: {result.output}")
            if result.usage:
                self.logger.debug(f"Token usage: {result.usage.total_tokens}")
            
            return result
        
        agent.run = logged_run
        return agent

# Usage
debugger = AgentDebugger()

# Debug tools
@debugger.trace_tool
async def my_tool(x: int) -> int:
    return x * 2

# Debug agent
agent = Agent('openai:gpt-4o')
agent = debugger.log_agent_interaction(agent)
```

### Performance Optimization

**1. Caching Strategies**

```python
from functools import lru_cache
from typing import Optional
import hashlib

class AgentCache:
    """Intelligent caching for agent operations"""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
    
    def _generate_key(self, prompt: str, deps: Optional[Any] = None) -> str:
        """Generate cache key from prompt and dependencies"""
        key_data = f"{prompt}:{str(deps)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_or_compute(
        self,
        agent: Agent,
        prompt: str,
        deps: Optional[Any] = None,
        ttl: int = 3600
    ) -> Any:
        """Get from cache or compute with agent"""
        key = self._generate_key(prompt, deps)
        
        # Check cache
        if key in self.cache:
            entry = self.cache[key]
            if entry['timestamp'] + ttl > time.time():
                return entry['result']
        
        # Compute
        result = await agent.run(prompt, deps=deps)
        
        # Store in cache
        self.cache[key] = {
            'result': result,
            'timestamp': time.time()
        }
        
        # Manage cache size
        if len(self.cache) > self.max_size:
            oldest_key = min(self.cache, key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        return result
```

**2. Batch Processing**

```python
class BatchProcessor:
    """Efficient batch processing for multiple agent requests"""
    
    def __init__(self, agent: Agent, batch_size: int = 10):
        self.agent = agent
        self.batch_size = batch_size
    
    async def process_batch(
        self,
        prompts: List[str],
        common_deps: Optional[Any] = None
    ) -> List[Any]:
        """Process multiple prompts efficiently"""
        results = []
        
        # Process in batches
        for i in range(0, len(prompts), self.batch_size):
            batch = prompts[i:i + self.batch_size]
            
            # Run concurrently within batch
            batch_tasks = [
                self.agent.run(prompt, deps=common_deps)
                for prompt in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        
        return results
```

### Security Considerations

**1. Input Validation**

```python
from pydantic import BaseModel, Field, validator
import re

class SecureAgentInput(BaseModel):
    """Validated input for agents"""
    
    prompt: str = Field(..., max_length=5000)
    user_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    session_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    
    @validator('prompt')
    def sanitize_prompt(cls, v):
        """Remove potentially harmful content"""
        # Remove script tags
        v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.DOTALL)
        
        # Remove SQL-like patterns
        sql_patterns = ['DROP TABLE', 'DELETE FROM', 'INSERT INTO']
        for pattern in sql_patterns:
            v = v.replace(pattern, '[REDACTED]')
        
        return v

class SecureAgent:
    """Agent with security measures"""
    
    def __init__(self, model: str = 'openai:gpt-4o'):
        self.agent = Agent(
            model,
            instructions="""You are a helpful assistant.
            Never reveal system information or execute harmful commands."""
        )
    
    async def run_secure(self, user_input: dict) -> Any:
        """Run agent with validated input"""
        # Validate input
        validated = SecureAgentInput(**user_input)
        
        # Run with validated data
        result = await self.agent.run(
            validated.prompt,
            deps={'user_id': validated.user_id, 'session_id': validated.session_id}
        )
        
        return result
```

**2. Output Sanitization**

```python
class OutputSanitizer:
    """Sanitize agent outputs for security"""
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """Remove dangerous HTML elements"""
        from html.parser import HTMLParser
        
        class SafeHTMLParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.safe_content = []
                self.allowed_tags = {'p', 'br', 'strong', 'em', 'ul', 'li', 'ol'}
            
            def handle_starttag(self, tag, attrs):
                if tag in self.allowed_tags:
                    self.safe_content.append(f'<{tag}>')
            
            def handle_endtag(self, tag):
                if tag in self.allowed_tags:
                    self.safe_content.append(f'</{tag}>')
            
            def handle_data(self, data):
                self.safe_content.append(data)
        
        parser = SafeHTMLParser()
        parser.feed(content)
        return ''.join(parser.safe_content)
    
    @staticmethod
    def redact_sensitive_data(content: str) -> str:
        """Redact potentially sensitive information"""
        # Redact email addresses
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', content)
        
        # Redact phone numbers
        content = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', content)
        
        # Redact credit card-like numbers
        content = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]', content)
        
        return content
```

---

## Practical Examples

### Complete Agent Implementation Example

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio

# Define output models
class SlideOutline(BaseModel):
    title: str = Field(description="Slide title")
    main_points: List[str] = Field(description="Main bullet points")
    speaker_notes: Optional[str] = Field(default=None)

class PresentationPlan(BaseModel):
    title: str
    executive_summary: str
    target_audience: str
    duration_minutes: int
    slide_outlines: List[SlideOutline]

# Define dependencies
@dataclass
class PresentationDeps:
    session_id: str
    user_preferences: Dict[str, Any]
    template_library: Any
    image_service: Any

# Create the presentation planning agent
class PresentationPlanningAgent:
    def __init__(self):
        self.agent = Agent(
            'openai:gpt-4o',
            output_type=PresentationPlan,
            deps_type=PresentationDeps,
            instructions="""You are an expert presentation planner.
            Create comprehensive, well-structured presentation plans that:
            1. Match the target audience's knowledge level
            2. Fit within the specified time constraints
            3. Include engaging content with clear narratives
            4. Suggest appropriate visuals and examples"""
        )
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        @self.agent.tool
        async def research_topic(
            ctx: RunContext[PresentationDeps],
            topic: str,
            depth: str = "medium"
        ) -> Dict[str, Any]:
            """Research a topic for presentation content"""
            # Simulate research
            return {
                "topic": topic,
                "key_facts": ["Fact 1", "Fact 2", "Fact 3"],
                "recent_developments": ["Development 1", "Development 2"],
                "common_misconceptions": ["Misconception 1"]
            }
        
        @self.agent.tool
        async def generate_examples(
            ctx: RunContext[PresentationDeps],
            concept: str,
            audience_level: str
        ) -> List[str]:
            """Generate relevant examples for a concept"""
            # Use audience level to tailor examples
            if audience_level == "beginner":
                return [f"Simple example of {concept}", f"Everyday analogy for {concept}"]
            else:
                return [f"Technical example of {concept}", f"Industry case study of {concept}"]
        
        @self.agent.tool
        async def suggest_visuals(
            ctx: RunContext[PresentationDeps],
            slide_content: Dict[str, Any]
        ) -> List[str]:
            """Suggest visuals for slide content"""
            # Use image service from dependencies
            suggestions = await ctx.deps.image_service.suggest_visuals(slide_content)
            return suggestions
    
    async def create_plan(
        self,
        request: str,
        audience: str,
        duration: int,
        deps: PresentationDeps
    ) -> PresentationPlan:
        """Create a presentation plan"""
        
        prompt = f"""
        Create a presentation plan for:
        Topic: {request}
        Target Audience: {audience}
        Duration: {duration} minutes
        
        Research the topic thoroughly and create a comprehensive plan with
        detailed slide outlines. Each slide should have clear main points
        and helpful speaker notes.
        """
        
        result = await self.agent.run(prompt, deps=deps)
        return result.output

# Usage example
async def main():
    # Initialize dependencies
    deps = PresentationDeps(
        session_id="session_123",
        user_preferences={"style": "professional", "color_scheme": "blue"},
        template_library=MockTemplateLibrary(),
        image_service=MockImageService()
    )
    
    # Create agent
    planner = PresentationPlanningAgent()
    
    # Create presentation plan
    plan = await planner.create_plan(
        request="Introduction to Machine Learning for Business Leaders",
        audience="C-level executives with limited technical background",
        duration=20,
        deps=deps
    )
    
    # Output the plan
    print(f"Presentation: {plan.title}")
    print(f"Duration: {plan.duration_minutes} minutes")
    print(f"Slides: {len(plan.slide_outlines)}")
    
    for i, slide in enumerate(plan.slide_outlines, 1):
        print(f"\nSlide {i}: {slide.title}")
        for point in slide.main_points:
            print(f"  • {point}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Tool Creation for Slide Generation

```python
from pydantic_ai import Agent, RunContext, Tool
from typing import List, Dict, Any
import asyncio

class SlideGenerationTools:
    """Collection of tools for slide generation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tools = []
        self._create_tools()
    
    def _create_tools(self):
        # Content generation tool
        async def generate_slide_content(
            topic: str,
            style: str = "professional",
            max_points: int = 5
        ) -> Dict[str, Any]:
            """Generate content for a single slide"""
            
            # Simulate content generation
            content = {
                "title": f"{topic} Overview",
                "subtitle": f"Key insights about {topic}",
                "bullet_points": [
                    f"Point 1 about {topic}",
                    f"Point 2 about {topic}",
                    f"Point 3 about {topic}"
                ][:max_points],
                "visual_elements": ["chart", "diagram"],
                "speaker_notes": f"Explain the importance of {topic}"
            }
            
            # Apply style modifications
            if style == "casual":
                content["title"] = f"Let's Talk About {topic}"
            elif style == "technical":
                content["title"] = f"Technical Analysis: {topic}"
            
            return content
        
        # Layout suggestion tool
        async def suggest_slide_layout(
            content_type: str,
            element_count: int
        ) -> Dict[str, Any]:
            """Suggest optimal slide layout"""
            
            layouts = {
                "text_only": {
                    "template": "simple_bullets",
                    "columns": 1,
                    "visual_position": None
                },
                "text_with_image": {
                    "template": "split_layout",
                    "columns": 2,
                    "visual_position": "right"
                },
                "data_visualization": {
                    "template": "chart_focused",
                    "columns": 1,
                    "visual_position": "center"
                }
            }
            
            # Determine best layout
            if element_count <= 3:
                layout_type = "text_only"
            elif element_count <= 5:
                layout_type = "text_with_image"
            else:
                layout_type = "data_visualization"
            
            return layouts.get(layout_type, layouts["text_only"])
        
        # Animation suggestion tool
        async def suggest_animations(
            slide_importance: str,
            content_elements: List[str]
        ) -> List[Dict[str, str]]:
            """Suggest slide animations"""
            
            if slide_importance == "high":
                return [
                    {"element": elem, "animation": "fade_in", "delay": i * 0.5}
                    for i, elem in enumerate(content_elements)
                ]
            else:
                return [{"element": "all", "animation": "appear", "delay": 0}]
        
        # Create Tool objects
        self.tools = [
            Tool(generate_slide_content, name="content_generator"),
            Tool(suggest_slide_layout, name="layout_advisor"),
            Tool(suggest_animations, name="animation_designer")
        ]
    
    def register_with_agent(self, agent: Agent) -> Agent:
        """Register all tools with an agent"""
        for tool in self.tools:
            agent.tools.append(tool)
        return agent

# Example usage
async def create_slide_with_tools():
    # Initialize tools
    slide_tools = SlideGenerationTools({"style": "modern"})
    
    # Create agent with tools
    agent = Agent(
        'openai:gpt-4o',
        instructions="""You are a slide creation expert. Use the available tools to:
        1. Generate appropriate content
        2. Select optimal layouts
        3. Add engaging animations
        Create professional, visually appealing slides."""
    )
    
    # Register tools
    agent = slide_tools.register_with_agent(agent)
    
    # Create a slide
    result = await agent.run("""
        Create a slide about 'Future of AI in Healthcare' for a medical conference.
        The audience consists of doctors and healthcare administrators.
        Make it informative but not too technical.
    """)
    
    return result.output
```

### Output Validation for Presentations

```python
from pydantic_ai import Agent
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional
import re

class ValidatedSlideContent(BaseModel):
    """Slide content with comprehensive validation"""
    
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Slide title"
    )
    
    bullet_points: List[str] = Field(
        ...,
        min_items=1,
        max_items=7,
        description="Main content points"
    )
    
    speaker_notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Notes for the presenter"
    )
    
    visual_type: Optional[str] = Field(
        None,
        regex=r'^(chart|image|diagram|table|none)$'
    )
    
    @validator('title')
    def validate_title(cls, v):
        """Ensure title is properly formatted"""
        # Remove excessive whitespace
        v = ' '.join(v.split())
        
        # Ensure proper capitalization
        if v.islower():
            v = v.title()
        
        return v
    
    @validator('bullet_points', each_item=True)
    def validate_bullet_points(cls, v):
        """Validate each bullet point"""
        # Ensure not too long
        if len(v) > 150:
            raise ValueError(f"Bullet point too long: {len(v)} characters")
        
        # Ensure ends with proper punctuation
        if not re.search(r'[.!?]$', v):
            v += '.'
        
        return v
    
    @root_validator
    def validate_content_coherence(cls, values):
        """Ensure overall content coherence"""
        title = values.get('title', '')
        points = values.get('bullet_points', [])
        
        # Ensure bullet points relate to title
        title_words = set(title.lower().split())
        relevant_points = 0
        
        for point in points:
            point_words = set(point.lower().split())
            if title_words & point_words:  # Intersection
                relevant_points += 1
        
        if relevant_points < len(points) / 2:
            raise ValueError("Bullet points don't seem related to the title")
        
        return values

class PresentationValidator:
    """Comprehensive presentation validation"""
    
    def __init__(self):
        self.agent = Agent(
            'openai:gpt-4o',
            output_type=List[ValidatedSlideContent],
            instructions="""Create presentation slides that are:
            1. Clear and concise
            2. Properly formatted
            3. Appropriate for professional settings
            4. Free of errors and redundancy"""
        )
    
    async def create_validated_presentation(
        self,
        topic: str,
        slide_count: int
    ) -> List[ValidatedSlideContent]:
        """Create a presentation with validated content"""
        
        prompt = f"""
        Create a {slide_count}-slide presentation about: {topic}
        
        Ensure each slide:
        - Has a clear, concise title
        - Contains 3-5 bullet points
        - Includes helpful speaker notes
        - Suggests appropriate visuals
        """
        
        try:
            result = await self.agent.run(prompt)
            return result.output
        except ValidationError as e:
            # Handle validation errors
            print(f"Validation error: {e}")
            # Retry with more specific instructions
            retry_prompt = f"{prompt}\n\nPlease ensure all content follows the validation rules."
            result = await self.agent.run(retry_prompt)
            return result.output

# Usage
async def create_validated_presentation():
    validator = PresentationValidator()
    
    slides = await validator.create_validated_presentation(
        topic="Best Practices for Remote Team Management",
        slide_count=5
    )
    
    for i, slide in enumerate(slides, 1):
        print(f"\nSlide {i}: {slide.title}")
        print("Points:")
        for point in slide.bullet_points:
            print(f"  • {point}")
        if slide.speaker_notes:
            print(f"Speaker Notes: {slide.speaker_notes}")
```

### Error Handling Patterns

```python
from pydantic_ai import Agent, ModelRetry, ValidationError
from typing import Optional, Dict, Any
import asyncio
import logging

class RobustAgentHandler:
    """Comprehensive error handling for agents"""
    
    def __init__(self, model: str = 'openai:gpt-4o'):
        self.agent = Agent(model)
        self.logger = logging.getLogger(__name__)
        self.retry_config = {
            'max_attempts': 3,
            'backoff_factor': 2,
            'max_delay': 30
        }
    
    async def run_with_fallback(
        self,
        primary_prompt: str,
        fallback_prompt: str,
        **kwargs
    ) -> Optional[Any]:
        """Run with fallback prompt on failure"""
        
        try:
            # Try primary prompt
            result = await self.agent.run(primary_prompt, **kwargs)
            return result.output
        
        except ModelRetry as e:
            self.logger.warning(f"Primary prompt failed with retry: {e}")
            
            # Try fallback prompt
            try:
                result = await self.agent.run(fallback_prompt, **kwargs)
                return result.output
            except Exception as e2:
                self.logger.error(f"Fallback also failed: {e2}")
                return None
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return None
    
    async def run_with_retry(
        self,
        prompt: str,
        custom_retry_logic: Optional[callable] = None,
        **kwargs
    ) -> Optional[Any]:
        """Run with custom retry logic"""
        
        attempt = 0
        delay = 1
        
        while attempt < self.retry_config['max_attempts']:
            try:
                result = await self.agent.run(prompt, **kwargs)
                return result.output
            
            except ModelRetry as e:
                attempt += 1
                
                if custom_retry_logic:
                    # Apply custom retry logic
                    should_retry, new_prompt = await custom_retry_logic(
                        prompt, e, attempt
                    )
                    if not should_retry:
                        break
                    prompt = new_prompt or prompt
                
                # Calculate backoff delay
                delay = min(
                    delay * self.retry_config['backoff_factor'],
                    self.retry_config['max_delay']
                )
                
                self.logger.info(f"Retry {attempt} after {delay}s delay")
                await asyncio.sleep(delay)
            
            except Exception as e:
                self.logger.error(f"Non-retryable error: {e}")
                break
        
        return None
    
    async def run_with_timeout(
        self,
        prompt: str,
        timeout_seconds: int = 30,
        **kwargs
    ) -> Optional[Any]:
        """Run with timeout protection"""
        
        try:
            result = await asyncio.wait_for(
                self.agent.run(prompt, **kwargs),
                timeout=timeout_seconds
            )
            return result.output
        
        except asyncio.TimeoutError:
            self.logger.error(f"Agent timeout after {timeout_seconds}s")
            return None
        
        except Exception as e:
            self.logger.error(f"Error during execution: {e}")
            return None

# Example custom retry logic
async def presentation_retry_logic(
    prompt: str,
    error: Exception,
    attempt: int
) -> tuple[bool, Optional[str]]:
    """Custom retry logic for presentation generation"""
    
    if "token limit" in str(error):
        # Reduce scope on token limit errors
        new_prompt = prompt + "\n\nPlease provide a more concise response."
        return True, new_prompt
    
    elif "validation" in str(error):
        # Add validation hints
        new_prompt = prompt + "\n\nEnsure all slides have titles and bullet points."
        return True, new_prompt
    
    elif attempt >= 3:
        # Give up after 3 attempts
        return False, None
    
    # Default: retry with same prompt
    return True, None

# Usage example
async def create_presentation_with_error_handling():
    handler = RobustAgentHandler()
    
    # Try with fallback
    result = await handler.run_with_fallback(
        primary_prompt="Create a 50-slide presentation about quantum computing",
        fallback_prompt="Create a 10-slide overview of quantum computing basics"
    )
    
    # Try with custom retry logic
    result2 = await handler.run_with_retry(
        prompt="Generate a technical presentation about AI",
        custom_retry_logic=presentation_retry_logic
    )
    
    # Try with timeout
    result3 = await handler.run_with_timeout(
        prompt="Create a simple 3-slide presentation",
        timeout_seconds=15
    )
    
    return result, result2, result3
```

---

## Quick Reference

### Common Patterns and Snippets

```python
# 1. Basic Agent Creation
agent = Agent('openai:gpt-4o', instructions="You are a helpful assistant.")

# 2. Agent with Structured Output
from pydantic import BaseModel

class MyOutput(BaseModel):
    field1: str
    field2: int

agent = Agent('openai:gpt-4o', output_type=MyOutput)

# 3. Agent with Dependencies
@dataclass
class MyDeps:
    db: Any
    cache: Any

agent = Agent('openai:gpt-4o', deps_type=MyDeps)

# 4. Simple Tool Registration
@agent.tool
async def my_tool(x: int) -> int:
    return x * 2

# 5. Tool with Context
@agent.tool
async def context_tool(ctx: RunContext[MyDeps], data: str) -> str:
    # Access deps via ctx.deps
    return f"Processed: {data}"

# 6. Streaming Response
async for chunk in agent.run_stream("Generate a long response"):
    print(chunk, end='')

# 7. Error Handling
try:
    result = await agent.run("My prompt")
except ModelRetry:
    # Handle retry
    pass
except ValidationError:
    # Handle validation error
    pass

# 8. Model Settings
from pydantic_ai.settings import ModelSettings

agent = Agent(
    'openai:gpt-4o',
    model_settings=ModelSettings(
        temperature=0.7,
        max_tokens=1000
    )
)

# 9. Multiple Models (Fallback)
from pydantic_ai.models.fallback import FallbackModel

model = FallbackModel(
    'openai:gpt-4o',
    'anthropic:claude-3-sonnet',
    'google:gemini-pro'
)
agent = Agent(model=model)

# 10. MCP Server Usage
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio('python', args=['tool.py'])
agent = Agent('openai:gpt-4o', mcp_servers=[server])

async with agent.run_mcp_servers():
    result = await agent.run("Use the tool")
```

### Troubleshooting Guide

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Agent returns empty output | Output validation failing | Check output_type schema, add validators |
| Tools not being called | Poor tool descriptions | Improve tool docstrings, add clear descriptions |
| High token usage | Sending full context | Implement state-aware context selection |
| Slow responses | Model latency | Use streaming, implement caching |
| Validation errors | Strict output schema | Add flexible validators, use Optional fields |
| MCP connection fails | Server configuration | Check server paths, permissions, logs |
| Dependency injection fails | Type mismatch | Verify deps_type matches actual dependencies |
| Rate limiting | Too many requests | Implement backoff, use batch processing |

### Resource Links

- **Official Documentation**: https://ai.pydantic.dev/
- **GitHub Repository**: https://github.com/pydantic/pydantic-ai
- **API Reference**: https://ai.pydantic.dev/api/
- **Examples**: https://ai.pydantic.dev/examples/
- **Model Providers**:
  - OpenAI: https://ai.pydantic.dev/api/models/openai/
  - Anthropic: https://ai.pydantic.dev/api/models/anthropic/
  - Google: https://ai.pydantic.dev/api/models/google/
- **Advanced Topics**:
  - MCP: https://ai.pydantic.dev/api/mcp/
  - Streaming: https://ai.pydantic.dev/api/result/
  - Testing: https://ai.pydantic.dev/api/models/test/

---

## Conclusion

This guide provides comprehensive best practices for building production-grade agents with PydanticAI. By following these patterns and principles, you can create robust, maintainable, and efficient AI-powered applications. Remember to:

1. Start with clear agent instructions and well-defined outputs
2. Use tools to extend agent capabilities
3. Implement proper error handling and validation
4. Leverage the model abstraction for provider flexibility
5. Consider MCP for advanced integrations
6. Always prioritize security and performance

PydanticAI's combination of type safety, flexible architecture, and production-ready features makes it an excellent choice for building sophisticated AI agents for applications like Deckster.