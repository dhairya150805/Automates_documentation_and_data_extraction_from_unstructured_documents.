from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# Request/Response Models for API validation
class CaseCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Case title")
    description: Optional[str] = Field(None, max_length=2000, description="Case description")
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

class CaseResponse(BaseModel):
    case_id: int
    title: str
    description: Optional[str]
    created_at: datetime
    evidence_count: int
    
    class Config:
        from_attributes = True

class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    file_size: int
    file_type: str
    upload_time: datetime
    processing_status: str

class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="User", regex=r'^(User|Manager|Admin)$')
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class HealthResponse(BaseModel):
    timestamp: datetime
    status: str = Field(..., regex=r'^(healthy|warning|degraded|error)$')
    services: dict
    dependencies: dict
    storage: dict
    warnings: List[str] = []

class ComplianceRuleRequest(BaseModel):
    required_fields: List[str] = Field(default_factory=list)
    patterns: dict = Field(default_factory=dict)
    value_constraints: dict = Field(default_factory=dict)
    
    @validator('required_fields')
    def validate_required_fields(cls, v):
        if len(v) > 50:  # Reasonable limit
            raise ValueError('Too many required fields specified')
        return v
