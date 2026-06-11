"""
Candidate Routes - Reads from your existing data/candidates.xlsx
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from pathlib import Path
from datetime import datetime

router = APIRouter(tags=["Candidates"])

# Path to your existing Excel file in the root data folder
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # Goes up to AI-Interview-Agent/
EXCEL_PATH = PROJECT_ROOT / "data" / "candidates.xlsx"

# Models
class CandidateVerify(BaseModel):
    email: str

class CandidateResponse(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    position: Optional[str] = None
    status: Optional[str] = None
    score: Optional[float] = None

class CandidateListResponse(BaseModel):
    candidates: List[CandidateResponse]
    total: int
    completed: int
    pending: int
    average_score: float

def load_candidates_data():
    """Load candidates from your existing Excel file"""
    if EXCEL_PATH.exists():
        df = pd.read_excel(EXCEL_PATH)
        return df
    else:
        raise HTTPException(status_code=500, detail=f"Excel file not found at {EXCEL_PATH}")

def save_candidates_data(df):
    """Save candidates back to Excel file"""
    EXCEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(EXCEL_PATH, index=False)

@router.post("/candidates/verify")
def verify_candidate(request: CandidateVerify):
    """Verify candidate email - matches Candidate.py page"""
    df = load_candidates_data()
    
    # Check if email exists
    match = df[df["email"] == request.email]
    
    if not match.empty:
        candidate_name = match.iloc[0]["name"]
        return {
            "success": True,
            "name": candidate_name,
            "email": request.email,
            "message": "Email verified successfully"
        }
    else:
        raise HTTPException(status_code=404, detail="Email not found. Please contact HR.")

@router.get("/candidates", response_model=CandidateListResponse)
def get_all_candidates():
    """Get all candidates - matches Dashboard.py"""
    df = load_candidates_data()
    
    candidates = []
    for idx, row in df.iterrows():
        candidates.append(CandidateResponse(
            id=idx,
            name=row["name"],
            email=row["email"],
            position=row.get("position", row.get("bootcamp", "")),  # Handle different column names
            status=row.get("status", "Pending"),
            score=float(row.get("score", 0)) if pd.notna(row.get("score")) else 0
        ))
    
    completed = len(df[df["status"] == "Completed"]) if "status" in df.columns else 0
    pending = len(df[df["status"] == "Pending"]) if "status" in df.columns else 0
    avg_score = float(df["score"].mean()) if "score" in df.columns and len(df) > 0 else 0
    
    return CandidateListResponse(
        candidates=candidates,
        total=len(df),
        completed=completed,
        pending=pending,
        average_score=round(avg_score, 2)
    )

@router.get("/candidates/{candidate_name}")
def get_candidate_by_name(candidate_name: str):
    """Get single candidate by name - matches Reports page"""
    df = load_candidates_data()
    match = df[df["name"] == candidate_name]
    
    if match.empty:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    row = match.iloc[0]
    return {
        "name": row["name"],
        "email": row["email"],
        "position": row.get("position", row.get("bootcamp", "")),
        "status": row.get("status", "Pending"),
        "score": float(row.get("score", 0)) if pd.notna(row.get("score")) else 0
    }

@router.post("/candidates/update-score")
def update_candidate_score(candidate_name: str, score: float):
    """Update candidate's interview score after completion"""
    df = load_candidates_data()
    
    if candidate_name not in df["name"].values:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    df.loc[df["name"] == candidate_name, "score"] = score
    df.loc[df["name"] == candidate_name, "status"] = "Completed"
    df.loc[df["name"] == candidate_name, "completed_at"] = datetime.now().isoformat()
    
    save_candidates_data(df)
    
    return {"success": True, "message": f"Score updated for {candidate_name}"}