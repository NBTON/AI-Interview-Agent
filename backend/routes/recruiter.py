"""
Recruiter Routes - Mock Data Only
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import os

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])

# ============================================
# MOCK DATA
# ============================================
# Mock candidates data (same as candidates.py for consistency)
mock_candidates = {
    1: {
        "id": 1,
        "name": "Ahmed Al-Rashidi",
        "email": "ahmed@example.com",
        "bootcamp": "Agentic AI",
        "status": "completed",
        "overall_score": 85,
        "completed_at": "2024-01-20T15:30:00"
    },
    2: {
        "id": 2,
        "name": "Sarah Johnson",
        "email": "sarah@example.com",
        "bootcamp": "Data Science",
        "status": "in_progress",
        "overall_score": None,
        "completed_at": None
    },
    3: {
        "id": 3,
        "name": "Carlos Mendez",
        "email": "carlos@example.com",
        "bootcamp": "Web Development",
        "status": "completed",
        "overall_score": 72,
        "completed_at": "2024-01-19T11:45:00"
    },
    4: {
        "id": 4,
        "name": "Emma Watson",
        "email": "emma@example.com",
        "bootcamp": "Agentic AI",
        "status": "pending",
        "overall_score": None,
        "completed_at": None
    }
}

# Mock interview sessions
mock_sessions = {
    "session-1": {
        "candidate_id": 1,
        "status": "completed",
        "score": 85,
        "completed_at": "2024-01-20T15:30:00"
    },
    "session-2": {
        "candidate_id": 2,
        "status": "in_progress",
        "score": None,
        "completed_at": None
    },
    "session-3": {
        "candidate_id": 3,
        "status": "completed",
        "score": 72,
        "completed_at": "2024-01-19T11:45:00"
    }
}

# ============================================
# PYDANTIC MODELS
# ============================================
class RecruiterLoginRequest(BaseModel):
    username: str
    password: str

class RecruiterLoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None

class DashboardStats(BaseModel):
    total_candidates: int
    completed_interviews: int
    pending_interviews: int
    in_progress_interviews: int
    average_score: float
    acceptance_rate: float

class CandidateSummary(BaseModel):
    id: int
    name: str
    email: str
    bootcamp: str
    status: str
    score: Optional[int] = None
    completed_at: Optional[str] = None

# ============================================
# ROUTES
# ============================================

@router.post("/login", response_model=RecruiterLoginResponse)
def recruiter_login(request: RecruiterLoginRequest):
    """Authenticate a recruiter"""
    # Get password from environment
    recruiter_password = os.getenv("RECRUITER_PASSWORD", "admin")
    
    if request.username != "admin" or request.password != recruiter_password:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    return RecruiterLoginResponse(
        success=True,
        message="Login successful",
        token="mock-jwt-token-12345"  # Mock token for MVP
    )

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats():
    """Get recruiter dashboard statistics"""
    candidates_list = list(mock_candidates.values())
    
    total = len(candidates_list)
    completed = len([c for c in candidates_list if c["status"] == "completed"])
    in_progress = len([c for c in candidates_list if c["status"] == "in_progress"])
    pending = len([c for c in candidates_list if c["status"] == "pending"])
    
    # Calculate average score from completed interviews
    scores = [c["overall_score"] for c in candidates_list if c["overall_score"] is not None]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Mock acceptance rate (candidates with score >= 70)
    accepted = len([c for c in candidates_list if c.get("overall_score", 0) >= 70])
    acceptance_rate = (accepted / completed * 100) if completed > 0 else 0
    
    return DashboardStats(
        total_candidates=total,
        completed_interviews=completed,
        pending_interviews=pending,
        in_progress_interviews=in_progress,
        average_score=round(avg_score, 1),
        acceptance_rate=round(acceptance_rate, 1)
    )

@router.get("/candidates", response_model=List[CandidateSummary])
def get_all_candidates():
    """Get all candidates with their interview status"""
    candidates_list = list(mock_candidates.values())
    
    return [
        CandidateSummary(
            id=c["id"],
            name=c["name"],
            email=c["email"],
            bootcamp=c["bootcamp"],
            status=c["status"],
            score=c.get("overall_score"),
            completed_at=c.get("completed_at")
        )
        for c in candidates_list
    ]

@router.get("/candidates/{candidate_id}", response_model=CandidateSummary)
def get_candidate_details(candidate_id: int):
    """Get detailed information about a specific candidate"""
    if candidate_id not in mock_candidates:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    c = mock_candidates[candidate_id]
    
    return CandidateSummary(
        id=c["id"],
        name=c["name"],
        email=c["email"],
        bootcamp=c["bootcamp"],
        status=c["status"],
        score=c.get("overall_score"),
        completed_at=c.get("completed_at")
    )

@router.get("/sessions")
def get_all_sessions():
    """Get all interview sessions"""
    return list(mock_sessions.values())

@router.get("/sessions/{session_id}")
def get_session_details(session_id: str):
    """Get detailed session information"""
    if session_id not in mock_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = mock_sessions[session_id]
    candidate = mock_candidates.get(session["candidate_id"])
    
    return {
        "session_id": session_id,
        "candidate": candidate,
        "status": session["status"],
        "score": session.get("score"),
        "completed_at": session.get("completed_at")
    }