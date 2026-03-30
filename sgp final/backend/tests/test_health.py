import pytest
from api.health import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/health")

client = TestClient(app)

def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert "timestamp" in data
    assert "status" in data
    assert "services" in data
    assert "dependencies" in data
    assert "storage" in data

def test_health_response_structure():
    """Test that health response has expected structure"""
    response = client.get("/health/")
    data = response.json()
    
    # Check services
    assert "python" in data["services"]
    assert "database" in data["services"]
    
    # Check dependencies
    assert "tesseract" in data["dependencies"]
    assert "transformers" in data["dependencies"]
    
    # Status should be one of: healthy, warning, degraded
    assert data["status"] in ["healthy", "warning", "degraded"]

def test_health_python_service():
    """Test Python service check"""
    response = client.get("/health/")
    data = response.json()
    
    python_service = data["services"]["python"]
    assert python_service["status"] == "ok"
    assert "version" in python_service
