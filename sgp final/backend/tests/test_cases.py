import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_case():
    """Test case creation"""
    case_data = {
        "title": "Test Case for Investigation",
        "description": "This is a test case for the compliance system"
    }
    
    response = client.post("/cases/", json=case_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert "case_id" in data
    assert data["title"] == case_data["title"]
    assert data["description"] == case_data["description"]

def test_create_case_no_title():
    """Test case creation without title (should fail)"""
    case_data = {
        "description": "This case has no title"
    }
    
    response = client.post("/cases/", json=case_data)
    assert response.status_code == 400
    
    data = response.json()
    assert "Case title is required" in data["detail"]

def test_list_cases():
    """Test case listing"""
    # First create a case
    case_data = {
        "title": "Test Case for Listing",
        "description": "This case will appear in the list"
    }
    client.post("/cases/", json=case_data)
    
    # Then list cases
    response = client.get("/cases/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    # Should have at least one case now
    assert len(data) >= 1

def test_get_case():
    """Test getting a specific case"""
    # First create a case
    case_data = {
        "title": "Test Case for Retrieval",
        "description": "This case will be retrieved"
    }
    create_response = client.post("/cases/", json=case_data)
    case_id = create_response.json()["case_id"]
    
    # Then get the case
    response = client.get(f"/cases/{case_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["case_id"] == case_id
    assert data["title"] == case_data["title"]
    assert data["description"] == case_data["description"]
    assert "evidence_count" in data

def test_get_nonexistent_case():
    """Test getting a case that doesn't exist"""
    response = client.get("/cases/99999")
    assert response.status_code == 404
    
    data = response.json()
    assert "Case not found" in data["detail"]

def test_case_summary():
    """Test getting case summary"""
    # First create a case
    case_data = {
        "title": "Test Case for Summary",
        "description": "This case will have its summary retrieved"
    }
    create_response = client.post("/cases/", json=case_data)
    case_id = create_response.json()["case_id"]
    
    # Then get the summary
    response = client.get(f"/cases/{case_id}/summary")
    assert response.status_code == 200
    
    data = response.json()
    assert "case_info" in data
    assert "evidence" in data
    assert "analysis" in data
