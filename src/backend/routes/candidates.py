"""
Candidate Routes - Integrated with Supabase DB & Excel local fallback
"""
import os
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Ensure project root and src/ are in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from supabase import create_client, Client
from backend.security import create_candidate_token

router = APIRouter(tags=["Candidates"])

# Path to local Excel fallback
EXCEL_PATH = PROJECT_ROOT / "data" / "candidates.xlsx"

# Load environment variables, overriding any pre-existing environment variables
load_dotenv(PROJECT_ROOT / ".env", override=True)

_supabase_url = os.environ.get("SUPABASE_URL")
_supabase_key = os.environ.get("SUPABASE_KEY")
_db_client: Client = None

if _supabase_url and _supabase_key and _supabase_key != "your_supabase_service_role_key_here":
    try:
        _db_client = create_client(_supabase_url, _supabase_key)
        print("Supabase client initialized successfully in candidates router.")
    except Exception as e:
        print(f"Error initializing Supabase client in candidates router: {e}")

# Models
class CandidateVerify(BaseModel):
    email: str

class CandidateResponse(BaseModel):
    id: Optional[str] = None
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

def load_candidates_data() -> pd.DataFrame:
    """Load candidates from Supabase DB, falling back to Excel if not available"""
    if _db_client:
        try:
            res = _db_client.table("candidates").select("*").execute()
            if res.data:
                records = []
                for row in res.data:
                    # Fetch score from reports if available
                    score_val = 0.0
                    try:
                        rep_res = _db_client.table("interview_reports").select("overall_score").eq("candidate_id", row["id"]).limit(1).execute()
                        if rep_res.data:
                            score_val = float(rep_res.data[0]["overall_score"]) * 20.0  # Scale 1-5 to 0-100%
                    except Exception as rep_err:
                        pass
                        
                    records.append({
                        "id": row["id"],
                        "name": row["full_name"],
                        "email": row["email"],
                        "position": row.get("metadata", {}).get("position", "Agentic AI") if row.get("metadata") else "Agentic AI",
                        "status": row["status"].capitalize() if row["status"] else "Pending",
                        "score": score_val
                    })
                return pd.DataFrame(records)
        except Exception as e:
            print(f"Error loading candidates from DB: {e}. Falling back to Excel.")
            
    # Fallback to local Excel file
    if EXCEL_PATH.exists():
        df = pd.read_excel(EXCEL_PATH)
        # Standardize columns
        if "bootcamp" in df.columns and "position" not in df.columns:
            df["position"] = df["bootcamp"]
        if "score" not in df.columns:
            df["score"] = 0.0
        return df
    else:
        # If no excel and no DB, return default mock DataFrame
        return pd.DataFrame([
            {"name": "Ali Ahmed", "email": "ali@example.com", "position": "Agentic AI", "status": "Completed", "score": 95.0},
            {"name": "Sara Hassan", "email": "sara@example.com", "position": "Agentic AI", "status": "Pending", "score": 80.0},
            {"name": "John Doe", "email": "john@example.com", "position": "Agentic AI", "status": "Completed", "score": 97.0},
            {"name": "Mai Salem", "email": "mai@example.com", "position": "Agentic AI", "status": "Completed", "score": 77.0},
            {"name": "Reem Omar", "email": "reem@example.com", "position": "Agentic AI", "status": "Pending", "score": 50.0},
        ])

def save_candidates_data(df):
    """Save candidates back to local Excel fallback"""
    try:
        EXCEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(EXCEL_PATH, index=False)
    except Exception as e:
        print(f"Error saving to Excel fallback: {e}")

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
            "candidate_token": create_candidate_token(request.email),
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
            id=str(row.get("id", idx)),
            name=row["name"],
            email=row["email"],
            position=row.get("position", row.get("bootcamp", "Agentic AI")),
            status=row.get("status", "Pending"),
            score=float(row.get("score", 0)) if pd.notna(row.get("score")) else 0.0
        ))
    
    completed = len(df[df["status"].str.lower() == "completed"]) if "status" in df.columns else 0
    pending = len(df[df["status"].str.lower() == "pending"]) if "status" in df.columns else 0
    avg_score = float(df["score"].mean()) if "score" in df.columns and len(df) > 0 else 0.0
    
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
        "position": row.get("position", row.get("bootcamp", "Agentic AI")),
        "status": row.get("status", "Pending"),
        "score": float(row.get("score", 0)) if pd.notna(row.get("score")) else 0.0
    }

@router.post("/candidates/update-score")
def update_candidate_score(candidate_name: str, score: float):
    """Update candidate's interview score and status after completion"""
    # 1. Update in local Excel first
    try:
        if EXCEL_PATH.exists():
            df = pd.read_excel(EXCEL_PATH)
            if candidate_name in df["name"].values:
                df.loc[df["name"] == candidate_name, "score"] = score
                df.loc[df["name"] == candidate_name, "status"] = "Completed"
                df.loc[df["name"] == candidate_name, "completed_at"] = datetime.now().isoformat()
                df.to_excel(EXCEL_PATH, index=False)
                print(f"Successfully updated candidate score in local Excel for {candidate_name}")
    except Exception as e:
        print(f"Error updating candidate score in local Excel: {e}")
        
    # 2. Update in DB if client is connected
    if _db_client:
        try:
            # Find candidate by name
            res = _db_client.table("candidates").select("id").eq("full_name", candidate_name).execute()
            if res.data:
                cand_id = res.data[0]["id"]
                candidate_status = "accepted" if score >= 80 else ("rejected" if score < 60 else "interviewed")
                _db_client.table("candidates").update({
                    "status": candidate_status,
                }).eq("id", cand_id).execute()
                print(f"Successfully updated candidate status in DB for {candidate_name}")
        except Exception as e:
            print(f"Error updating candidate status in DB: {e}")
            
    return {"success": True, "message": f"Score updated for {candidate_name}"}
