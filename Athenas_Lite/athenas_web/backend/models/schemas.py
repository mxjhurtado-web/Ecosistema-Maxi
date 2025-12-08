"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Auth models
class UserInfo(BaseModel):
    email: str  # Changed from EmailStr to avoid email-validator dependency
    name: str
    role: str  # 'admin' or 'user'
    keycloak_id: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo

# Analysis models
class AnalysisRequest(BaseModel):
    department: str
    evaluator: str
    advisor: str
    gemini_api_key: Optional[str] = None

class AnalysisResult(BaseModel):
    id: int
    filename: str
    department: str
    evaluator: str
    advisor: str
    timestamp: datetime
    score_bruto: float
    score_final: float
    sentiment: str
    drive_txt_link: Optional[str] = None
    drive_csv_link: Optional[str] = None
    drive_pdf_link: Optional[str] = None

class CallSummary(BaseModel):
    id: int
    filename: str
    department: str
    score_final: float
    sentiment: str
    timestamp: datetime

# Admin models
class DepartmentCreate(BaseModel):
    name: str
    active: bool = True

class Department(BaseModel):
    id: int
    name: str
    active: bool
    created_at: datetime

class RubricUpload(BaseModel):
    department: str
    rubric_data: dict

class UserCreate(BaseModel):
    email: str  # Changed from EmailStr
    name: str # Added name field for pre-provisioning
    role: str  # 'admin' or 'user'
