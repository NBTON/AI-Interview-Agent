from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.db import (
    candidate_metadata,
    candidate_name,
    display_status,
    get_candidate_reports_map,
    get_supabase,
    public_candidate,
    score_to_db,
)

router = APIRouter(tags=["Candidates"])


class CandidateVerify(BaseModel):
    email: str


class CandidateResponse(BaseModel):
    id: Optional[Any] = None
    name: str
    email: str
    position: Optional[str] = None
    status: Optional[str] = None
    score: Optional[float] = None
    completed_at: Optional[str] = None


class CandidateListResponse(BaseModel):
    candidates: List[CandidateResponse]
    total: int
    completed: int
    pending: int
    in_progress: int
    average_score: float
    acceptance_rate: float


def _load_candidates_from_db() -> List[Dict[str, Any]]:
    supabase = get_supabase()
    candidates_res = supabase.table("candidates").select("*").order("created_at", desc=True).execute()
    reports_map = get_candidate_reports_map()

    return [public_candidate(row, reports_map.get(row.get("id"))) for row in candidates_res.data or []]


def _candidate_record_from_db(candidate_id: str) -> Dict[str, Any]:
    supabase = get_supabase()
    response = supabase.table("candidates").select("*").eq("id", candidate_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return response.data


def _find_candidate_by_name(name: str) -> Dict[str, Any]:
    supabase = get_supabase()
    response = supabase.table("candidates").select("*").eq("full_name", name).limit(1).execute()
    if response.data:
        return response.data[0]

    response = supabase.table("candidates").select("*").ilike("full_name", name).limit(1).execute()
    if response.data:
        return response.data[0]

    response = supabase.table("candidates").select("*").ilike("email", name).limit(1).execute()
    if response.data:
        return response.data[0]

    raise HTTPException(status_code=404, detail="Candidate not found")


def _write_score_to_db(candidate: Dict[str, Any], score: float) -> None:
    supabase = get_supabase()
    candidate_id = candidate["id"]
    status = "accepted" if score >= 80 else "rejected" if score < 60 else "interviewed"
    metadata = candidate_metadata(candidate)
    metadata.update(
        {
            "last_score": score,
            "completed_at": datetime.now().isoformat(),
            "position": candidate_metadata(candidate).get("position") or metadata.get("position") or "Agentic AI",
        }
    )

    supabase.table("candidates").update({"status": status, "metadata": metadata}).eq("id", candidate_id).execute()

    session_id = str(uuid4())
    supabase.table("interview_sessions").upsert(
        {
            "id": session_id,
            "candidate_id": candidate_id,
            "status": "completed",
            "current_topic": metadata.get("position") or "Agentic AI",
            "topics_covered": [],
            "missing_topics": [],
            "turn_count": 0,
            "scores": {},
        },
        on_conflict="id",
    ).execute()

    supabase.table("interview_reports").upsert(
        {
            "session_id": session_id,
            "candidate_id": candidate_id,
            "overall_score": score_to_db(score),
            "status": status,
            "summary": f"Score updated manually to {score}%. Decision status: {status}.",
            "recommendation": "accept" if status == "accepted" else "reject" if status == "rejected" else "review",
            "decision_notes": "Score updated from recruiter/candidate flow.",
            "strengths": "",
            "weaknesses": "",
        },
        on_conflict="session_id",
    ).execute()


@router.post("/candidates/verify")
def verify_candidate(request: CandidateVerify):
    supabase = get_supabase()
    response = supabase.table("candidates").select("*").eq("email", request.email.lower()).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Email not found. Please contact HR.")

    row = response.data[0]
    return {
        "success": True,
        "name": candidate_name(row),
        "email": row.get("email") or request.email,
        "message": "Email verified successfully",
    }


@router.get("/candidates", response_model=CandidateListResponse)
def get_all_candidates():
    candidates = _load_candidates_from_db()

    completed = sum(1 for c in candidates if str(c.get("status", "")).lower() in {"completed", "accepted", "rejected", "interviewed"})
    in_progress = sum(1 for c in candidates if str(c.get("status", "")).lower() in {"in progress", "interviewing"})
    pending = sum(1 for c in candidates if str(c.get("status", "")).lower() in {"pending", "new", "not started"})
    scores = [float(c.get("score") or 0) for c in candidates]
    accepted = sum(1 for score in scores if score >= 70)

    return CandidateListResponse(
        candidates=[CandidateResponse(**candidate) for candidate in candidates],
        total=len(candidates),
        completed=completed,
        pending=pending,
        in_progress=in_progress,
        average_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
        acceptance_rate=round(accepted / completed * 100, 1) if completed else 0.0,
    )


@router.get("/candidates/{candidate_id}")
def get_candidate_by_id(candidate_id: str):
    row = _candidate_record_from_db(candidate_id)
    reports_map = get_candidate_reports_map()
    candidate = public_candidate(row, reports_map.get(row.get("id")))
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.post("/candidates/update-score")
def update_candidate_score(candidate_name: str, score: float):
    candidate = _find_candidate_by_name(candidate_name)
    _write_score_to_db(candidate, score)
    return {"success": True, "message": f"Score updated for {candidate_name}"}
