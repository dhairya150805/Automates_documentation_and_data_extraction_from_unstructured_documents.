import pytest
import sys
import os
import tempfile
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create and setup test database"""    # Use a separate test database
    os.environ['DATABASE_URL'] = 'sqlite:///test.db'
    
    from database.db import init_db, engine
    from database.models import Base
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    init_db()
    
    yield
    
    # Cleanup test database
    try:
        if os.path.exists('test.db'):
            os.remove('test.db')
    except (OSError, PermissionError):
        pass  # Ignore cleanup errors on Windows

@pytest.fixture
def client():
    """Create a test client"""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)

@pytest.fixture
def sample_text_file():
    """Create a temporary text file for testing"""
    content = "This is a test document for AI processing"
    fd, path = tempfile.mkstemp(suffix='.txt')
    try:
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(content)
        yield path, content
    finally:
        try:
            os.unlink(path)
        except (OSError, PermissionError):
            pass  # Ignore cleanup errors on Windows
