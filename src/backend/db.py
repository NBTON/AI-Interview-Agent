import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from dotenv import load_dotenv
from supabase import Client, create_client

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)

_SUPABASE_URL = os.getenv("SUPABASE_URL")
_SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
_db_client: Optional[Client] = None


def is_supabase_configured() -> bool:
    return bool(_SUPABASE_URL and _SUPABASE_KEY and _SUPABASE_KEY != "your_supabase_service_role_key_here")


def get_supabase() -> Client:
    global _db_client
    if not is_supabase_configured():
        raise RuntimeError("Supabase environment variables are not configured.")
    if _db_client is None:
        _db_client = create_client(_SUPABASE_URL, _SUPABASE_KEY)
    return _db_client


def optional_supabase() -> Optional[Client]:
    if not is_supabase_configured():
        return None
    return get_supabase()


def score_to_db(score: Optional[float]) -> Optional[float]:
    if score is None:
        return None
    value = float(score)
    return round(value / 20.0, 2) if value > 5.0 else round(value, 2)


def score_to_frontend(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    score = float(value)
    return round(score * 20.0, 2) if score <= 5.0 else round(score, 2)


def display_status(status: Optional[str]) -> str:
    raw = str(status or "new").lower().strip()
    mapping = {
        "new": "Pending",
        "pending": "Pending",
        "not started": "Pending",
        "interviewing": "In Progress",
        "in_progress": "In Progress",
        "interviewed": "Completed",
        "completed": "Completed",
        "accepted": "Completed",
        "rejected": "Completed",
    }
    return mapping.get(raw, raw.replace("_", " ").title())


def db_status(status: Optional[str]) -> str:
    raw = str(status or "new").lower().strip()
    if raw in {"accepted"}:
        return "accepted"
    if raw in {"rejected"}:
        return "rejected"
    if raw in {"interviewed", "completed", "accepted", "rejected"}:
        return "interviewed"
    if raw in {"interviewing", "in_progress"}:
        return "interviewing"
    return "new"


def candidate_name(row: Dict[str, Any]) -> str:
    return row.get("full_name") or row.get("name") or row.get("metadata", {}).get("name") or "Unknown Candidate"


def candidate_position(row: Dict[str, Any]) -> str:
    metadata = row.get("metadata") or {}
    return (
        metadata.get("position")
        or metadata.get("bootcamp")
        or metadata.get("program")
        or row.get("bootcamp")
        or row.get("position")
        or "Agentic AI"
    )


def candidate_metadata(row: Dict[str, Any]) -> Dict[str, Any]:
    metadata = row.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            import json

            metadata = json.loads(metadata)
        except Exception:
            metadata = {}
    return metadata if isinstance(metadata, dict) else {}


def public_candidate(row: Dict[str, Any], report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    report = report or {}
    score = score_to_frontend(report.get("overall_score") or report.get("score"))
    return {
        "id": row.get("id"),
        "name": candidate_name(row),
        "email": row.get("email") or "",
        "position": candidate_position(row),
        "status": display_status(row.get("status")),
        "score": score if score is not None else 0.0,
        "completed_at": report.get("completed_at") or row.get("completed_at") or report.get("updated_at") or row.get("updated_at"),
    }


def public_session(report: Optional[Dict[str, Any]], turns: Iterable[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not report:
        return None
    score = score_to_frontend(report.get("overall_score") or report.get("score"))
    return {
        "candidate_id": report.get("candidate_id"),
        "session_id": report.get("session_id"),
        "status": display_status(report.get("status")) or "Completed",
        "score": score,
        "completed_at": report.get("completed_at") or report.get("updated_at"),
        "ai_analysis": report.get("ai_analysis") or report.get("summary") or "",
        "decision_notes": report.get("decision_notes") or report.get("notes") or report.get("recommendation") or "",
        "strengths": _to_list(report.get("strengths")),
        "weaknesses": _to_list(report.get("weaknesses")),
        "turns": [
            {
                "question": t.get("question", t.get("agent_message", "")),
                "answer": t.get("answer", t.get("candidate_message", "")),
                "topic": t.get("topic", ""),
                "score": t.get("score"),
                "feedback": t.get("feedback", t.get("comment", "")),
            }
            for t in turns
        ],
    }


def _to_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return [s.strip() for s in str(value).split(",") if s.strip()]


def find_candidate_by_email(email: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase()
    response = supabase.table("candidates").select("*").eq("email", email.lower()).limit(1).execute()
    return (response.data or [None])[0]


def find_candidate_by_name(name: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase()
    response = supabase.table("candidates").select("*").ilike("full_name", name).limit(1).execute()
    if response.data:
        return response.data[0]
    response = supabase.table("candidates").select("*").ilike("email", name).limit(1).execute()
    return (response.data or [None])[0]


def get_or_create_candidate(full_name: str, email: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    supabase = get_supabase()
    candidate = find_candidate_by_email(email)
    existing_metadata = candidate_metadata(candidate) if candidate else {}
    payload = {
        "full_name": full_name,
        "email": email.lower(),
        "status": "interviewing",
        "metadata": {**existing_metadata, **(metadata or {})},
    }
    if candidate:
        response = supabase.table("candidates").update(payload).eq("id", candidate["id"]).execute()
        return (response.data or [candidate])[0]
    response = supabase.table("candidates").insert(payload).execute()
    return (response.data or [{}])[0]


def get_candidate_reports_map() -> Dict[Any, Dict[str, Any]]:
    supabase = get_supabase()
    response = supabase.table("interview_reports").select("*").execute()
    latest: Dict[Any, Dict[str, Any]] = {}
    for report in response.data or []:
        cid = report.get("candidate_id")
        if cid is None:
            continue
        existing = latest.get(cid)
        created = report.get("created_at") or report.get("updated_at") or ""
        if not existing or created >= (existing.get("created_at") or existing.get("updated_at") or ""):
            latest[cid] = report
    return latest
