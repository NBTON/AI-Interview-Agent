# tests/conftest.py
import pytest
import uuid
from pathlib import Path
import sys

# Setup paths once
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
AGENT_DIR = SRC_DIR / "agent"

from src.agent.db import get_supabase_client

# Clean up sys.path to avoid conflicts
for path in [str(AGENT_DIR), str(SRC_DIR), str(PROJECT_ROOT)]:
    if path in sys.path:
        sys.path.remove(path)
    sys.path.insert(0, path)

@pytest.fixture(scope="session")
def db_client():
    """Get database client for tests"""
    return get_supabase_client()

@pytest.fixture(scope="session")
def test_session(db_client):
    """Create a test session in DB"""
    from tools import ensure_candidate_and_session
    if db_client:
        result = ensure_candidate_and_session(
            candidate_id=f"test-session-{uuid.uuid4().hex[:8]}",
            candidate_name="Test Session User",
            program_id=None
        )
        return result
    return None

@pytest.fixture(scope="session")
def candidate_id():
    """Generate a unique candidate ID for tests"""
    return str(uuid.uuid4())


@pytest.fixture(scope="session")
def mock_answers():
    """Mock answers for testing"""
    return {
        "background": "Computer Science background with 5 years of Python development experience.",
        "education": "BSc in Software Engineering from KFUPM.",
        "experience": "3 years building Python backends with Django and FastAPI.",
        "skills": "Python, SQL, Docker, Machine Learning basics.",
        "projects": "Built an AI agent using LangGraph with PostgreSQL integration."
    }


@pytest.fixture(scope="session")
def rubric():
    """Get program rubric - using direct import to avoid circular issues"""
    # Import here to avoid circular import at module level
    import importlib.util
    import sys
    
    # Try direct import
    try:
        from src.agent.tools import get_program_requirements
        return get_program_requirements()["rubric"]
    except ImportError:
        # Fallback: manual import
        spec = importlib.util.spec_from_file_location(
            "tools", 
            PROJECT_ROOT / "src" / "agent" / "tools.py"
        )
        tools = importlib.util.module_from_spec(spec)
        sys.modules["tools"] = tools
        spec.loader.exec_module(tools)
        return tools.get_program_requirements()["rubric"]


@pytest.fixture(scope="session")
def required_topics():
    """Required topics for interview"""
    return ["background", "education", "experience", "skills", "projects"]