"""
Authentication Routes - Matches recruiter_login.py
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import hmac
from pathlib import Path
from dotenv import load_dotenv

router = APIRouter(tags=["Authentication"])
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env", override=True)

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str

VALID_EMAIL = os.environ.get("RECRUITER_EMAIL", "")
VALID_PASSWORD = os.environ.get("RECRUITER_PASSWORD", "")

@router.post("/recruiter/login", response_model=LoginResponse)
def recruiter_login(request: LoginRequest):
    """Authenticate recruiter - matches recruiter_login.py"""
    
    if not VALID_EMAIL or not VALID_PASSWORD:
        raise HTTPException(status_code=503, detail="Recruiter login is not configured")

    if hmac.compare_digest(request.email.strip().lower(), VALID_EMAIL.strip().lower()) and hmac.compare_digest(request.password, VALID_PASSWORD):
        return LoginResponse(
            success=True,
            message="Login successful"
        )
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
