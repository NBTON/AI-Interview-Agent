from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.db import get_candidate_reports_map, get_supabase, public_candidate, score_to_frontend

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


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
    id: Any
    name: str
    email: str
    bootcamp: Optional[str] = "Agentic AI"
    status: str
    score: Optional[float] = None
    completed_at: Optional[str] = None


class SessionDetail(BaseModel):
    candidate_id: Any
    status: str
    score: Optional[float] = None
    completed_at: Optional[str] = None
    ai_analysis: Optional[str] = None
    decision_notes: Optional[str] = None
    strengths: Optional[List[str]] = []
    weaknesses: Optional[List[str]] = []
    turns: Optional[List[dict]] = []


def _fetch_candidates() -> List[Dict[str, Any]]:
    supabase = get_supabase()
    try:
        res = supabase.table("candidates").select("*").order("created_at", desc=True).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    reports_map = get_candidate_reports_map()
    return [public_candidate(row, reports_map.get(row.get("id"))) for row in res.data or []]


def _fetch_session(candidate_id: str) -> Dict[str, Any]:
    supabase = get_supabase()
    try:
        report_res = (
            supabase.table("interview_reports")
            .select("*")
            .eq("candidate_id", candidate_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error (report): {e}")

    report = (report_res.data or [None])[0]
    if not report:
        raise HTTPException(status_code=404, detail="No interview report found for this candidate.")

    turns = []
    session_id = report.get("session_id")
    if session_id:
        try:
            turns_res = (
                supabase.table("interview_turns")
                .select("*")
                .eq("session_id", session_id)
                .order("turn_number", desc=False)
                .execute()
            )
            raw_turns = turns_res.data or []
        except Exception:
            raw_turns = []

        for t in raw_turns:
            turns.append(
                {
                    "question": t.get("question", t.get("agent_message", "")),
                    "answer": t.get("answer", t.get("candidate_message", "")),
                    "topic": t.get("topic", ""),
                    "score": t.get("score"),
                    "feedback": t.get("feedback", t.get("comment", "")),
                }
            )

    def to_list(value):
        if not value:
            return []
        if isinstance(value, list):
            return [str(v) for v in value if str(v).strip()]
        return [s.strip() for s in str(value).split(",") if s.strip()]

    return {
        "candidate_id": candidate_id,
        "session_id": session_id,
        "status": report.get("status", "completed"),
        "score": score_to_frontend(report.get("overall_score") or report.get("score")),
        "completed_at": report.get("completed_at") or report.get("updated_at"),
        "ai_analysis": report.get("ai_analysis") or report.get("summary") or "",
        "decision_notes": report.get("decision_notes") or report.get("notes") or report.get("recommendation") or "",
        "strengths": to_list(report.get("strengths")),
        "weaknesses": to_list(report.get("weaknesses")),
        "turns": turns,
    }


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats():
    candidates = _fetch_candidates()
    total = len(candidates)
    completed = sum(1 for c in candidates if c["status"].lower() in {"completed", "accepted", "rejected", "interviewed"})
    in_progress = sum(1 for c in candidates if c["status"].lower() in {"in progress", "interviewing"})
    pending = sum(1 for c in candidates if c["status"].lower() in {"pending", "new", "not started"})
    scores = [float(c.get("score") or 0) for c in candidates]
    accepted = sum(1 for score in scores if score >= 70)

    return DashboardStats(
        total_candidates=total,
        completed_interviews=completed,
        pending_interviews=pending,
        in_progress_interviews=in_progress,
        average_score=round(sum(scores) / len(scores), 1) if scores else 0.0,
        acceptance_rate=round(accepted / completed * 100, 1) if completed else 0.0,
    )


@router.get("/candidates", response_model=List[CandidateSummary])
def get_all_candidates():
    return [
        CandidateSummary(
            id=c["id"],
            name=c["name"],
            email=c["email"],
            bootcamp=c.get("position") or c.get("bootcamp") or "Agentic AI",
            status=c.get("status") or "Pending",
            score=c.get("score"),
            completed_at=c.get("completed_at"),
        )
        for c in _fetch_candidates()
    ]


@router.get("/candidates/{candidate_id}", response_model=CandidateSummary)
def get_candidate_details(candidate_id: str):
    candidates = [c for c in _fetch_candidates() if str(c["id"]) == candidate_id]
    if not candidates:
        raise HTTPException(status_code=404, detail="Candidate not found")
    c = candidates[0]
    return CandidateSummary(
        id=c["id"],
        name=c["name"],
        email=c["email"],
        bootcamp=c.get("position") or c.get("bootcamp") or "Agentic AI",
        status=c.get("status") or "Pending",
        score=c.get("score"),
        completed_at=c.get("completed_at"),
    )


@router.get("/sessions")
def get_all_sessions():
    supabase = get_supabase()
    try:
        res = supabase.table("interview_reports").select("*").order("created_at", desc=True).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    return res.data or []


@router.get("/sessions/{candidate_id}", response_model=SessionDetail)
def get_session_by_candidate(candidate_id: str):
    return _fetch_session(candidate_id)
