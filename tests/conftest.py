"""
Pytest configuration and fixtures for testing.
"""

import os
import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Set testing environment
os.environ["TESTING"] = "true"
os.environ["APP_ENV"] = "testing"

# Mock environment variables if not set
if not os.getenv("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
if not os.getenv("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
if not os.getenv("SUPABASE_ANON_KEY"):
    os.environ["SUPABASE_ANON_KEY"] = "test-anon-key"

from src.api.main import app
from src.utils.auth import create_test_token
from src.config.settings import get_settings


# Configure pytest-asyncio
pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Get test settings."""
    settings = get_settings()
    # Override settings for testing
    settings.app_env = "testing"
    settings.debug = True
    return settings


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_user_token():
    """Create a test user token."""
    return create_test_token(user_id="test_user_123")


@pytest.fixture
def test_headers(test_user_token):
    """Create test headers with authentication."""
    return {
        "Authorization": f"Bearer {test_user_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def sample_user_input():
    """Sample user input for testing."""
    return {
        "message_id": "test_msg_001",
        "timestamp": "2024-01-01T00:00:00Z",
        "session_id": "test_session_123",
        "type": "user_input",
        "data": {
            "text": "Create a presentation about AI in healthcare",
            "attachments": [],
            "ui_references": [],
            "frontend_actions": []
        }
    }


@pytest.fixture
def sample_presentation_request():
    """Sample presentation request for testing."""
    return {
        "session_id": "test_session_123",
        "topic": "AI in Healthcare",
        "presentation_type": "conference",
        "requirements": {
            "duration": "20 minutes",
            "audience": "Healthcare professionals",
            "style": "professional"
        }
    }


@pytest.fixture
def sample_clarification_response():
    """Sample clarification response for testing."""
    return {
        "round_id": "round_001",
        "responses": {
            "q_001": "20 minutes",
            "q_002": "Healthcare professionals",
            "q_003": "Modern and professional"
        }
    }


@pytest_asyncio.fixture
async def mock_redis(monkeypatch):
    """Mock Redis client for testing."""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def set_session(self, session_id, data, ttl=3600):
            self.data[f"session:{session_id}"] = data
            return True
        
        async def get_session(self, session_id):
            return self.data.get(f"session:{session_id}")
        
        async def health_check(self):
            return True
        
        async def disconnect(self):
            pass
        
        async def set_cache(self, key, value, ttl=300):
            self.data[key] = value
            return True
        
        async def get_cache(self, key, default=None):
            return self.data.get(key, default)
        
        async def check_rate_limit(self, identifier, limit, window_seconds):
            return True, 0
    
    mock = MockRedis()
    
    async def get_mock_redis():
        return mock
    
    monkeypatch.setattr("src.storage.redis_cache.get_redis", get_mock_redis)
    return mock


@pytest_asyncio.fixture
async def mock_supabase(monkeypatch):
    """Mock Supabase client for testing."""
    class MockSupabase:
        def __init__(self):
            self.sessions = {}
            self.presentations = {}
        
        async def create_session(self, session_id, user_id, expires_hours=24):
            session = {
                "id": session_id,
                "user_id": user_id,
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": "2024-01-02T00:00:00Z"
            }
            self.sessions[session_id] = session
            return session
        
        async def get_session(self, session_id):
            return self.sessions.get(session_id)
        
        async def health_check(self):
            return True
        
        async def save_presentation(self, presentation, session_id, embedding=None):
            pres_id = f"pres_{len(self.presentations) + 1}"
            self.presentations[pres_id] = {
                "id": pres_id,
                "session_id": session_id,
                "title": presentation.title
            }
            return pres_id
        
        async def get_presentation(self, presentation_id):
            return self.presentations.get(presentation_id)
        
        async def find_similar_presentations(self, embedding, **kwargs):
            return []
    
    mock = MockSupabase()
    
    def get_mock_supabase():
        return mock
    
    monkeypatch.setattr("src.storage.supabase.get_supabase", get_mock_supabase)
    return mock


@pytest.fixture
def mock_llm_response(monkeypatch):
    """Mock LLM responses for testing."""
    async def mock_run_llm(self, prompt, context, temperature=None):
        # Return different responses based on prompt content
        if "analyze" in prompt.lower():
            return type('MockResult', (), {
                'data': {
                    'completeness_score': 0.5,
                    'missing_information': ['target audience', 'duration'],
                    'detected_intent': 'educational presentation',
                    'presentation_type': 'conference',
                    'estimated_slides': 15,
                    'complexity_level': 'moderate',
                    'key_topics': ['AI applications', 'Healthcare benefits'],
                    'suggested_flow': ['Introduction', 'Current State', 'AI Applications', 'Benefits', 'Challenges', 'Conclusion']
                }
            })
        elif "clarification" in prompt.lower():
            return type('MockResult', (), {
                'data': [
                    {
                        'question_id': 'q_001',
                        'question': 'How long should the presentation be?',
                        'question_type': 'choice',
                        'options': ['10-15 minutes', '20-30 minutes', '45-60 minutes'],
                        'required': True,
                        'category': 'logistics',
                        'priority': 'high'
                    }
                ]
            })
        else:
            return type('MockResult', (), {'data': {}})
    
    monkeypatch.setattr("src.agents.base.BaseAgent.run_llm", mock_run_llm)


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup after each test."""
    yield
    # Any cleanup code here


# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )