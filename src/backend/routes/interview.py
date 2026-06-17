"""
Interview Routes - Integrated with LangGraph agents
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR      = PROJECT_ROOT / "src"
AGENT_DIR    = SRC_DIR / "agent"

# Move any paths containing the local 'supabase' folder to the end of
# sys.path to avoid shadowing the third-party library.
shadowing_paths = [str(PROJECT_ROOT), str(SRC_DIR), "", "."]
for path in shadowing_paths:
    while path in sys.path:
        sys.path.remove(path)
    sys.path.append(path)

for p in (str(AGENT_DIR), str(SRC_DIR), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.append(p)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import concurrent.futures
import json

from agent.graph import build_graph
from backend.db import get_or_create_candidate, get_supabase, score_to_db

router = APIRouter(tags=["Interview"])

# Compile the LangGraph instance once at startup
graph = build_graph()

# In-memory session metadata (keyed by session_id)
interview_sessions: Dict[str, dict] = {}

# Secondary index: candidate_id (uuid) → latest session_id
candidate_session_index: Dict[str, str] = {}

DEFAULT_MIN_QUESTIONS = 10
DEFAULT_MAX_QUESTIONS = 30


# ── Helpers ────────────────────────────────────────────────────────────────────

def _question_limit() -> int:
    try:
        from agent.tools import get_program_requirements
        reqs = get_program_requirements()
        return min(max(int(reqs.get("max_turns") or DEFAULT_MAX_QUESTIONS),
                       DEFAULT_MIN_QUESTIONS), DEFAULT_MAX_QUESTIONS)
    except Exception:
        return DEFAULT_MAX_QUESTIONS


def _parse_structured_question(
    raw_question: Optional[str],
) -> tuple[str, str, Optional[List[str]], Optional[str]]:
    """Parse a question that may be plain text or a JSON-encoded dict."""
    q_text      = raw_question or ""
    q_type      = "open_ended"
    options     = None
    initial_code = None

    if not raw_question:
        return q_text, q_type, options, initial_code

    try:
        q_data = json.loads(raw_question)
        if isinstance(q_data, dict) and "type" in q_data:
            q_text       = q_data.get("text", "")
            q_type       = q_data.get("type", "open_ended")
            options      = q_data.get("options")
            initial_code = q_data.get("initial_code")
    except Exception:
        pass

    type_aliases = {
        "text":             "open_ended",
        "mcq":              "multiple_choice",
        "multiple-choice":  "multiple_choice",
        "truefalse":        "true_false",
        "true/false":       "true_false",
    }
    q_type = type_aliases.get(str(q_type).strip().lower(),
                               str(q_type).strip().lower())

    if q_type == "true_false" and not options:
        options = ["True", "False"]

    return q_text, q_type, options, initial_code


def _get_candidate_id_from_db(candidate_email: str, candidate_name: str) -> Optional[str]:
    try:
        candidate = get_or_create_candidate(candidate_name, candidate_email, {"position": "Agentic AI"})
        return candidate.get("id")
    except Exception as e:
        print(f"[interview] Could not look up candidate id: {e}")
    return None


def _persist_session_to_db(session_id: str, session: dict, final_score: Optional[float]) -> None:
    try:
        cand_id = session.get("candidate_db_id")
        if not cand_id:
            return

        supabase = get_supabase()
        completed_at = session.get("completed_at") or datetime.now().isoformat()
        report = session.get("final_report") or {}
        recommendation = report.get("recommendation")
        db_status = (
            "accepted" if recommendation == "accept" else
            "rejected" if recommendation == "reject" else
            "interviewed"
        )

        turns_payload = []
        for i, ans in enumerate(session.get("answers", []), start=1):
            turns_payload.append({
                "session_id": session_id,
                "turn_number": i,
                "question": ans.get("question", ""),
                "answer": ans.get("answer", ""),
                "topic": ans.get("topic", ""),
                "score": ans.get("score"),
                "feedback": ans.get("feedback", ""),
                "needs_probe": bool(ans.get("needs_probe", False)),
            })

        strengths = session.get("strengths", [])
        weaknesses = session.get("weaknesses", [])
        if not isinstance(strengths, list):
            strengths = [s.strip() for s in str(strengths).split(",") if s.strip()]
        if not isinstance(weaknesses, list):
            weaknesses = [w.strip() for w in str(weaknesses).split(",") if w.strip()]

        supabase.table("interview_sessions").upsert(
            {
                "id": session_id,
                "candidate_id": cand_id,
                "status": "completed",
                "current_topic": session.get("current_topic", ""),
                "topics_covered": session.get("topics_covered", []),
                "missing_topics": session.get("missing_topics", []),
                "turn_count": len(turns_payload),
                "scores": {t["topic"]: t["score"] for t in turns_payload if t.get("topic") and t.get("score") is not None},
                "ended_at": completed_at,
            },
            on_conflict="id",
        ).execute()

        supabase.table("interview_reports").upsert(
            {
                "session_id": session_id,
                "candidate_id": cand_id,
                "overall_score": score_to_db(final_score),
                "status": db_status,
                "completed_at": completed_at,
                "ai_analysis": session.get("ai_analysis", ""),
                "summary": session.get("ai_analysis", report.get("summary", "")),
                "recommendation": recommendation,
                "decision_notes": session.get("decision_notes", ""),
                "strengths": ", ".join(strengths),
                "weaknesses": ", ".join(weaknesses),
                "topic_scores": report.get("topic_scores", {}),
            },
            on_conflict="session_id",
        ).execute()

        if turns_payload:
            supabase.table("interview_turns").upsert(
                turns_payload,
                on_conflict="session_id,turn_number",
            ).execute()

        metadata = session.get("metadata", {})
        if isinstance(metadata, dict):
            metadata = dict(metadata)
        else:
            metadata = {}
        metadata.update({"last_score": final_score, "completed_at": completed_at})
        supabase.table("candidates").update({"status": db_status, "metadata": metadata}).eq("id", cand_id).execute()

        print(f"[interview] Persisted session to DB for candidate_id={cand_id}")

    except Exception as e:
        print(f"[interview] DB persist error: {e}")


# ── Pydantic models ────────────────────────────────────────────────────────────

class StartInterviewRequest(BaseModel):
    candidate_name:  str
    candidate_email: str

class StartInterviewResponse(BaseModel):
    session_id:      str
    candidate_name:  str
    first_question:  str
    question_type:   str            = "text"
    options:         Optional[List[str]] = None
    initial_code:    Optional[str]  = None
    current_topic:   str            = "background"
    question_number: int
    total_questions: int

class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer:     str

class SubmitAnswerResponse(BaseModel):
    session_id:      str
    next_question:   Optional[str]  = None
    question_type:   str            = "text"
    options:         Optional[List[str]] = None
    initial_code:    Optional[str]  = None
    current_topic:   str            = "background"
    question_number: int
    total_questions: int
    is_complete:     bool
    score:           Optional[float] = None
    feedback:        Optional[str]   = None
    final_score:     Optional[float] = None


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/interview/start", response_model=StartInterviewResponse)
def start_interview(request: StartInterviewRequest):
    """Start a new interview session via LangGraph."""
    session_id = str(uuid.uuid4())
    config     = {"configurable": {"thread_id": session_id}}

    candidate_db_id = _get_candidate_id_from_db(request.candidate_email, request.candidate_name)
    if not candidate_db_id:
        raise HTTPException(status_code=404, detail="Candidate not found in the database.")

    initial_state = {
        "candidate_id":     candidate_db_id,
        "candidate_name":   request.candidate_name,
        "session_id":       session_id,
        "program_id":       "",
        "current_topic":    "",
        "topics_covered":   [],
        "questions_asked":  [],
        "answers":          [],
        "scores":           {},
        "missing_info":     [],
        "last_question":    "",
        "last_answer":      "",
        "turn_count":       0,
        "probe_count":      0,
        "needs_probe":      False,
        "extracted_skills": [],
        "extracted_info":   {},
        "feedback":         "",
        "is_complete":      False,
        "final_report":     None,
    }

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(graph.invoke, initial_state, config)
            try:
                result = future.result(timeout=120)
            except concurrent.futures.TimeoutError:
                raise HTTPException(
                    status_code=504,
                    detail="Interview initialisation timed out. Please try again.",
                )

        first_question_raw = result.get("last_question", "Hello! Let's start the interview.")
        q_text, q_type, options, initial_code = _parse_structured_question(first_question_raw)

        # Store in-memory session metadata
        db_session_id = result.get("session_id") or session_id
        db_candidate_id = result.get("candidate_id") or candidate_db_id

        interview_sessions[session_id] = {
            "candidate_name":   request.candidate_name,
            "candidate_email":  request.candidate_email,
            "candidate_db_id":  db_candidate_id,
            "db_session_id":    db_session_id,
            "metadata": {"position": "Agentic AI"},
            "started_at":       datetime.now().isoformat(),
            "completed":        False,
            "answers":          [],
            "ai_analysis":      "",
            "decision_notes":   "",
            "strengths":        [],
            "weaknesses":       [],
        }

        # Register in candidate → session index
        if candidate_db_id is not None:
            candidate_session_index[candidate_db_id] = session_id

        return StartInterviewResponse(
            session_id=session_id,
            candidate_name=request.candidate_name,
            first_question=q_text,
            question_type=q_type,
            options=options,
            initial_code=initial_code,
            current_topic=result.get("current_topic") or "background",
            question_number=1,
            total_questions=_question_limit(),
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[interview] Start error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialise interview. Please try again.")


@router.post("/interview/answer", response_model=SubmitAnswerResponse)
def submit_answer(request: SubmitAnswerRequest):
    """Submit a candidate answer and advance the LangGraph agent."""
    session_id = request.session_id
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    config = {"configurable": {"thread_id": session_id}}

    try:
        # Snapshot the question that was asked before updating state
        state         = graph.get_state(config)
        last_question = state.values.get("last_question", "") if state and state.values else ""

        graph.update_state(config, {"last_answer": request.answer})

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(graph.invoke, None, config)
            try:
                result = future.result(timeout=120)
            except concurrent.futures.TimeoutError:
                raise HTTPException(
                    status_code=504,
                    detail="Answer processing timed out. Please try again.",
                )

        is_complete = result.get("is_complete", False)
        feedback    = result.get("feedback")

        # Derive per-turn score
        scores         = result.get("scores", {})
        topics_covered = result.get("topics_covered", [])
        last_score_val = 3.0
        if topics_covered:
            last_score_val = scores.get(topics_covered[-1], 3.0)
        elif result.get("current_topic") in scores:
            last_score_val = scores.get(result["current_topic"], 3.0)
        turn_percentage = (last_score_val / 5.0) * 100

        # Persist turn in session memory
        interview_sessions[session_id]["answers"].append({
            "question":  last_question,
            "answer":    request.answer,
            "topic":     result.get("current_topic", ""),
            "score":     last_score_val,
            "percentage": turn_percentage,
            "feedback":  feedback,
            "timestamp": datetime.now().isoformat(),
        })

        next_question_raw = result.get("last_question") if not is_complete else None
        q_number          = result.get("turn_count", 0) + 1
        q_text, q_type, options, initial_code = _parse_structured_question(next_question_raw)

        final_score = None
        if is_complete:
            report          = result.get("final_report") or {}
            final_score_raw = report.get("overall_score", 3.0)
            final_score     = (final_score_raw / 5.0) * 100

            # Enrich session with report metadata for DB persistence
            session = interview_sessions[session_id]
            session["completed"]       = True
            session["completed_at"]    = datetime.now().isoformat()
            session["final_score"]     = final_score
            session["ai_analysis"]     = report.get("ai_analysis", report.get("summary", ""))
            session["decision_notes"]  = report.get("decision_notes", report.get("notes", ""))
            raw_strengths  = report.get("strengths", [])
            raw_weaknesses = report.get("weaknesses", [])
            session["strengths"]  = raw_strengths  if isinstance(raw_strengths, list)  else [s.strip() for s in str(raw_strengths).split(",")  if s.strip()]
            session["weaknesses"] = raw_weaknesses if isinstance(raw_weaknesses, list) else [w.strip() for w in str(raw_weaknesses).split(",") if w.strip()]

            # Persist to Supabase
            db_session_id = session.get("db_session_id") or session_id
            _persist_session_to_db(db_session_id, session, final_score)

        return SubmitAnswerResponse(
            session_id=session_id,
            next_question=q_text,
            question_type=q_type,
            options=options,
            initial_code=initial_code,
            current_topic=result.get("current_topic") or "",
            question_number=q_number,
            total_questions=_question_limit(),
            is_complete=is_complete,
            score=turn_percentage,
            feedback=feedback,
            final_score=final_score,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[interview] Answer error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process answer. Please try again.")


@router.get("/interview/session/{candidate_id}")
def get_session_by_candidate(candidate_id: str):
    """
    Return full session detail for a candidate by their UUID DB id.
    """
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
        report = (report_res.data or [None])[0]

        if report:
            session_id = report.get("session_id")
            turns = []
            if session_id:
                turns_res = (
                    supabase.table("interview_turns")
                    .select("*")
                    .eq("session_id", session_id)
                    .order("turn_number", desc=False)
                    .execute()
                )
                for t in (turns_res.data or []):
                    turns.append({
                        "question": t.get("question",  t.get("agent_message",     "")),
                        "answer":   t.get("answer",    t.get("candidate_message", "")),
                        "topic":    t.get("topic",     ""),
                        "score":    t.get("score"),
                        "feedback": t.get("feedback",  t.get("comment", "")),
                    })

            def _to_list(val):
                if not val:               return []
                if isinstance(val, list): return [str(v) for v in val if str(v).strip()]
                return [s.strip() for s in str(val).split(",") if s.strip()]

            raw_score = report.get("overall_score")
            score_pct = None
            if raw_score is not None:
                raw_score = float(raw_score)
                score_pct = raw_score * 20.0 if raw_score <= 5.0 else raw_score

            return {
                "candidate_id":   candidate_id,
                "session_id":     session_id,
                "status":         report.get("status", "completed"),
                "score":          score_pct,
                "completed_at":   report.get("completed_at") or report.get("updated_at"),
                "ai_analysis":    report.get("ai_analysis",    report.get("summary",        "")),
                "decision_notes": report.get("decision_notes", report.get("notes",          "")),
                "strengths":      _to_list(report.get("strengths")),
                "weaknesses":     _to_list(report.get("weaknesses")),
                "turns":          turns,
            }
    except Exception as e:
        print(f"[interview] DB session fetch error: {e}")
        raise HTTPException(status_code=500, detail=f"Database session fetch error: {e}")


@router.get("/interview/status/{session_id}")
def get_session_status(session_id: str):
    """
    Get real-time LangGraph state for a running session (keyed by session_id).
    Used by the candidate-facing interview UI.
    """
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    config = {"configurable": {"thread_id": session_id}}
    state  = graph.get_state(config)

    if not state or not state.values:
        raise HTTPException(status_code=404, detail="State not found for session")

    values    = state.values
    scores    = values.get("scores", {})
    avg_score = (sum(scores.values()) / len(scores) / 5.0 * 100) if scores else 0.0

    final_score = None
    if values.get("is_complete"):
        report          = values.get("final_report") or {}
        final_score_raw = report.get("overall_score", 3.0)
        final_score     = (final_score_raw / 5.0) * 100

    return {
        "session_id":      session_id,
        "candidate_name":  values.get("candidate_name"),
        "completed":       values.get("is_complete", False),
        "current_topic":   values.get("current_topic", ""),
        "question_number": values.get("turn_count", 0) + 1,
        "total_questions": _question_limit(),
        "answers_so_far":  len(values.get("answers", [])),
        "average_score":   avg_score,
        "final_score":     final_score,
    }


@router.get("/interview/history/{candidate_name}")
def get_candidate_interview_history(candidate_name: str):
    """Return all in-memory sessions for a candidate (by name)."""
    history = [
        {
            "session_id":    sid,
            "completed":     sess["completed"],
            "completed_at":  sess.get("completed_at"),
            "final_score":   sess.get("final_score"),
            "total_answers": len(sess.get("answers", [])),
            "answers":       sess.get("answers", []),
        }
        for sid, sess in interview_sessions.items()
        if sess["candidate_name"] == candidate_name
    ]
    return {"candidate_name": candidate_name, "sessions": history}