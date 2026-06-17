"""
Recruiter Routes - Live Supabase analytics for admissions dashboards.
"""
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from agent.db import get_supabase_client

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])


class DashboardStats(BaseModel):
    total_candidates: int
    completed_interviews: int
    pending_interviews: int
    in_progress_interviews: int
    average_score: float
    acceptance_rate: float


class CandidateSummary(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    bootcamp: str = "Agentic AI"
    status: str
    score: Optional[float] = None
    completed_at: Optional[str] = None
    report_id: Optional[str] = None
    session_id: Optional[str] = None
    recommendation: Optional[str] = None


def _require_db():
    db = get_supabase_client()
    if not db:
        raise HTTPException(status_code=503, detail="Supabase is not configured for live recruiter analytics")
    return db


def _as_percent(score: Any) -> Optional[float]:
    try:
        if score is None:
            return None
        return round(float(score) * 20.0, 1)
    except (TypeError, ValueError):
        return None


def _bootcamp(candidate: dict) -> str:
    metadata = candidate.get("metadata") or {}
    if isinstance(metadata, dict):
        return metadata.get("position") or metadata.get("bootcamp") or "Agentic AI"
    return "Agentic AI"


def _fetch_candidates(db) -> list[dict]:
    try:
        res = db.table("candidates").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as exc:
        print(f"Error loading recruiter candidates from Supabase: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load candidates")


def _fetch_reports(db) -> list[dict]:
    try:
        res = db.table("interview_reports").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as exc:
        print(f"Error loading recruiter reports from Supabase: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load interview reports")


def _fetch_sessions(db) -> list[dict]:
    try:
        res = db.table("interview_sessions").select("*").order("started_at", desc=True).execute()
        return res.data or []
    except Exception as exc:
        print(f"Error loading recruiter sessions from Supabase: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load interview sessions")


def _latest_by(rows: list[dict], key: str, date_key: str) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for row in rows:
        value = row.get(key)
        if not value:
            continue
        current = latest.get(value)
        if not current or str(row.get(date_key) or "") > str(current.get(date_key) or ""):
            latest[value] = row
    return latest


def _candidate_summary(candidate: dict, report: Optional[dict], session: Optional[dict]) -> CandidateSummary:
    status = candidate.get("status") or "new"
    completed_at = None
    if session:
        completed_at = session.get("ended_at")
        if session.get("status") == "in_progress" and status == "new":
            status = "interviewing"
    if report:
        completed_at = report.get("created_at") or completed_at

    return CandidateSummary(
        id=str(candidate.get("id")),
        name=candidate.get("full_name") or "Unknown candidate",
        email=candidate.get("email"),
        bootcamp=_bootcamp(candidate),
        status=status,
        score=_as_percent(report.get("overall_score")) if report else None,
        completed_at=completed_at,
        report_id=str(report.get("id")) if report else None,
        session_id=str((report or session or {}).get("session_id") or (session or {}).get("id") or ""),
        recommendation=report.get("recommendation") if report else None,
    )


def _load_candidate_bundle(candidate_id: str) -> dict:
    db = _require_db()
    try:
        candidate_res = db.table("candidates").select("*").eq("id", candidate_id).limit(1).execute()
        if not candidate_res.data:
            raise HTTPException(status_code=404, detail="Candidate not found")
        candidate = candidate_res.data[0]

        reports_res = (
            db.table("interview_reports")
            .select("*")
            .eq("candidate_id", candidate_id)
            .order("created_at", desc=True)
            .execute()
        )
        sessions_res = (
            db.table("interview_sessions")
            .select("*")
            .eq("candidate_id", candidate_id)
            .order("started_at", desc=True)
            .execute()
        )
        profile_res = db.table("candidate_profiles").select("*").eq("candidate_id", candidate_id).limit(1).execute()
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error loading recruiter candidate bundle from Supabase: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load candidate report")

    reports = reports_res.data or []
    sessions = sessions_res.data or []
    report = reports[0] if reports else None
    report_session_id = report.get("session_id") if report else None
    session = next((item for item in sessions if item.get("id") == report_session_id), sessions[0] if sessions else None)
    session_id = session.get("id") if session else report_session_id

    turns: list[dict] = []
    messages: list[dict] = []
    if session_id:
        try:
            turns_res = (
                db.table("interview_turns")
                .select("*")
                .eq("session_id", session_id)
                .order("turn_number")
                .execute()
            )
            turns = turns_res.data or []
            messages_res = (
                db.table("conversation_messages")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at")
                .execute()
            )
            messages = messages_res.data or []
        except Exception as exc:
            print(f"Error loading recruiter turn history from Supabase: {exc}")
            raise HTTPException(status_code=500, detail="Failed to load interview history")

    return {
        "candidate": _candidate_summary(candidate, report, session).model_dump(),
        "report": report,
        "session": session,
        "profile": (profile_res.data or [None])[0],
        "turns": turns,
        "messages": messages,
        "reports": reports,
        "sessions": sessions,
    }


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats():
    """Get live recruiter dashboard statistics from Supabase."""
    db = _require_db()
    candidates = _fetch_candidates(db)
    reports = _fetch_reports(db)
    sessions = _fetch_sessions(db)

    completed = len([session for session in sessions if session.get("status") == "completed"])
    in_progress = len([session for session in sessions if session.get("status") == "in_progress"])
    candidates_with_sessions = {session.get("candidate_id") for session in sessions if session.get("candidate_id")}
    pending = len([candidate for candidate in candidates if candidate.get("id") not in candidates_with_sessions])
    scores = [float(report["overall_score"]) for report in reports if report.get("overall_score") is not None]
    accepted = len([report for report in reports if report.get("recommendation") == "accept"])

    return DashboardStats(
        total_candidates=len(candidates),
        completed_interviews=completed,
        pending_interviews=pending,
        in_progress_interviews=in_progress,
        average_score=round((sum(scores) / len(scores)) * 20.0, 1) if scores else 0.0,
        acceptance_rate=round((accepted / len(reports)) * 100.0, 1) if reports else 0.0,
    )


@router.get("/candidates", response_model=list[CandidateSummary])
def get_all_candidates():
    """Get all candidates with their latest live report/session state."""
    db = _require_db()
    candidates = _fetch_candidates(db)
    latest_report = _latest_by(_fetch_reports(db), "candidate_id", "created_at")
    latest_session = _latest_by(_fetch_sessions(db), "candidate_id", "started_at")
    return [
        _candidate_summary(
            candidate,
            latest_report.get(candidate.get("id")),
            latest_session.get(candidate.get("id")),
        )
        for candidate in candidates
    ]


@router.get("/candidates/{candidate_id}")
def get_candidate_details(candidate_id: str):
    """Get complete report, turn history, chat logs, and notes for one candidate."""
    return _load_candidate_bundle(candidate_id)


@router.get("/reports/{report_id}")
def get_report_by_id(report_id: str):
    """Get complete candidate report context by report ID."""
    db = _require_db()
    try:
        report_res = db.table("interview_reports").select("*").eq("id", report_id).limit(1).execute()
    except Exception as exc:
        print(f"Error loading recruiter report by ID from Supabase: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load report")
    if not report_res.data:
        raise HTTPException(status_code=404, detail="Report not found")
    return _load_candidate_bundle(report_res.data[0]["candidate_id"])


@router.get("/sessions")
def get_all_sessions():
    """Get all live interview sessions."""
    db = _require_db()
    return _fetch_sessions(db)


@router.get("/sessions/{session_id}")
def get_session_details(session_id: str):
    """Get one live session with report, candidate, turns, and chat logs."""
    db = _require_db()
    try:
        session_res = db.table("interview_sessions").select("*").eq("id", session_id).limit(1).execute()
    except Exception as exc:
        print(f"Error loading recruiter session by ID from Supabase: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load session")
    if not session_res.data:
        raise HTTPException(status_code=404, detail="Session not found")
    return _load_candidate_bundle(session_res.data[0]["candidate_id"])
