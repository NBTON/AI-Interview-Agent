"""
Authentication Routes - Matches recruiter_login.py
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

router = APIRouter(tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str

# Match your hardcoded values from recruiter_login.py
VALID_EMAIL = "admin@example.com"
VALID_PASSWORD = "12345"

@router.post("/recruiter/login", response_model=LoginResponse)
def recruiter_login(request: LoginRequest):
    """Authenticate recruiter - matches recruiter_login.py"""
    
    if request.email == VALID_EMAIL and request.password == VALID_PASSWORD:
        return LoginResponse(
            success=True,
            message="Login successful"
        )
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )