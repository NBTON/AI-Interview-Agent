"""
Interview Routes - Integrated with LangGraph agents
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
AGENT_DIR = SRC_DIR / "agent"

# Move any paths containing the local 'supabase' folder to the end of sys.path to avoid shadowing the third-party library
shadowing_paths = [str(PROJECT_ROOT), str(SRC_DIR), "", "."]
for path in shadowing_paths:
    while path in sys.path:
        sys.path.remove(path)
    sys.path.append(path)

# Add AGENT_DIR, SRC_DIR, and PROJECT_ROOT to sys.path so we can import internal modules
if str(AGENT_DIR) not in sys.path:
    sys.path.append(str(AGENT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
import concurrent.futures
import json

from agent.graph import build_graph
from agent.db import get_supabase_client
from backend.security import verify_candidate_token

router = APIRouter(tags=["Interview"])

# Compile the LangGraph instance
_graph = None
_graph_error = None
_db_client = get_supabase_client()

DEFAULT_MIN_QUESTIONS = 10
DEFAULT_MAX_QUESTIONS = 30


def _question_limit() -> int:
    try:
        from agent.tools import get_program_requirements
        reqs = get_program_requirements()
        return min(max(int(reqs.get("max_turns") or DEFAULT_MAX_QUESTIONS), DEFAULT_MIN_QUESTIONS), DEFAULT_MAX_QUESTIONS)
    except Exception:
        return DEFAULT_MAX_QUESTIONS


def _parse_structured_question(raw_question: Optional[str]) -> tuple[str, str, Optional[List[str]], Optional[str]]:
    q_text = raw_question or ""
    q_type = "open_ended"
    options = None
    initial_code = None

    if not raw_question:
        return q_text, q_type, options, initial_code

    try:
        q_data = json.loads(raw_question)
        if isinstance(q_data, dict) and "type" in q_data:
            q_text = q_data.get("text", "")
            q_type = q_data.get("type", "open_ended")
            options = q_data.get("options")
            initial_code = q_data.get("initial_code")
    except Exception:
        pass

    type_aliases = {
        "text": "open_ended",
        "mcq": "multiple_choice",
        "multiple-choice": "multiple_choice",
        "truefalse": "true_false",
        "true/false": "true_false",
    }
    q_type = type_aliases.get(str(q_type).strip().lower(), str(q_type).strip().lower())

    if q_type == "true_false" and not options:
        options = ["True", "False"]

    return q_text, q_type, options, initial_code

class StartInterviewRequest(BaseModel):
    candidate_name: str
    candidate_email: str
    candidate_token: str

class StartInterviewResponse(BaseModel):
    session_id: str
    candidate_name: str
    first_question: str
    question_type: str = "text"
    options: Optional[List[str]] = None
    initial_code: Optional[str] = None
    current_topic: str = "background"
    question_number: int
    total_questions: int

class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer: str

class SubmitAnswerResponse(BaseModel):
    session_id: str
    next_question: Optional[str] = None
    question_type: str = "text"
    options: Optional[List[str]] = None
    initial_code: Optional[str] = None
    current_topic: str = "background"
    question_number: int
    total_questions: int
    is_complete: bool
    score: Optional[float] = None
    feedback: Optional[str] = None
    final_score: Optional[float] = None


def _require_db_client():
    if not _db_client:
        raise HTTPException(status_code=503, detail="Supabase is not configured")
    return _db_client


def _fetch_session(session_id: str) -> dict:
    db = _require_db_client()
    try:
        res = db.table("interview_sessions").select("*").eq("id", session_id).limit(1).execute()
    except Exception as exc:
        print(f"Error fetching interview session from Supabase: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load session")
    if not res.data:
        raise HTTPException(status_code=404, detail="Session not found")
    return res.data[0]


def _fetch_candidate(candidate_id: str) -> dict:
    db = _require_db_client()
    try:
        res = db.table("candidates").select("*").eq("id", candidate_id).limit(1).execute()
    except Exception as exc:
        print(f"Error fetching candidate from Supabase: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load candidate")
    return res.data[0] if res.data else {}


def _fetch_turns(session_id: str) -> list[dict]:
    db = _require_db_client()
    try:
        res = db.table("interview_turns").select("*").eq("session_id", session_id).order("turn_number").execute()
        return res.data or []
    except Exception as exc:
        print(f"Error fetching interview turns from Supabase: {exc}")
        return []


def _fetch_messages(session_id: str) -> list[dict]:
    db = _require_db_client()
    try:
        res = db.table("conversation_messages").select("*").eq("session_id", session_id).order("created_at").execute()
        return res.data or []
    except Exception as exc:
        print(f"Error fetching conversation messages from Supabase: {exc}")
        return []


def _fetch_final_score(session_id: str) -> Optional[float]:
    db = _require_db_client()
    try:
        res = db.table("interview_reports").select("overall_score").eq("session_id", session_id).limit(1).execute()
        if res.data and res.data[0].get("overall_score") is not None:
            return float(res.data[0]["overall_score"]) * 20.0
    except Exception as exc:
        print(f"Error fetching final score from Supabase: {exc}")
    return None


def _get_graph():
    global _graph, _graph_error
    if _graph:
        return _graph
    try:
        _graph = build_graph()
        _graph_error = None
        return _graph
    except Exception as exc:
        _graph_error = exc
        print(f"Error initializing persistent LangGraph checkpointer: {exc}")
        raise HTTPException(
            status_code=503,
            detail=(
                "Persistent interview state is not configured. Set SUPABASE_DB_URL, DATABASE_URL, "
                "POSTGRES_URL, or SUPABASE_DB_PASSWORD with SUPABASE_URL."
            ),
        )

@router.post("/interview/start", response_model=StartInterviewResponse)
def start_interview(request: StartInterviewRequest):
    """Start a new interview session - running the LangGraph agent"""
    verify_candidate_token(request.candidate_token, request.candidate_email)

    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    
    # Initialize the LangGraph state
    initial_state = {
        "candidate_id": request.candidate_email,
        "candidate_name": request.candidate_name,
        "session_id": session_id,
        "program_id": "",
        "current_topic": "",
        "topics_covered": [],
        "questions_asked": [],
        "answers": [],
        "scores": {},
        "missing_info": [],
        "last_question": "",
        "last_answer": "",
        "turn_count": 0,
        "probe_count": 0,
        "needs_probe": False,
        "extracted_skills": [],
        "extracted_info": {},
        "feedback": "",
        "is_complete": False,
        "final_report": None,
    }
    
    try:
        graph = _get_graph()
        # Run graph with timeout to prevent hanging on slow LLM responses
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(graph.invoke, initial_state, config)
            try:
                result = future.result(timeout=120)
            except concurrent.futures.TimeoutError:
                raise HTTPException(status_code=504, detail="Interview initialization timed out. Please try again.")
        
        first_question_raw = result.get("last_question", "Hello! Let's start the interview.")
        
        q_text, q_type, options, initial_code = _parse_structured_question(first_question_raw)

        return StartInterviewResponse(
            session_id=session_id,
            candidate_name=request.candidate_name,
            first_question=q_text,
            question_type=q_type,
            options=options,
            initial_code=initial_code,
            current_topic=result.get("current_topic") or "background",
            question_number=1,
            total_questions=_question_limit()
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize interview. Please try again.")

@router.post("/interview/answer", response_model=SubmitAnswerResponse)
def submit_answer(request: SubmitAnswerRequest):
    """Submit an answer and resume the LangGraph execution to get evaluation and next question"""
    session_id = request.session_id
    _fetch_session(session_id)
        
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        graph = _get_graph()
        # Get current state to know which question was asked
        state = graph.get_state(config)
        if not state or not state.values:
            raise HTTPException(status_code=404, detail="State not found for session")
        last_question = state.values.get("last_question") if state and state.values else ""
        
        # Update state with the candidate's answer
        graph.update_state(config, {"last_answer": request.answer})
        
        # Resume the graph with timeout protection
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(graph.invoke, None, config)
            try:
                result = future.result(timeout=120)
            except concurrent.futures.TimeoutError:
                raise HTTPException(status_code=504, detail="Answer processing timed out. Please try again.")
        
        is_complete = result.get("is_complete", False)
        feedback = result.get("feedback")
        
        # Calculate turn score percentage
        scores = result.get("scores", {})
        last_score_val = 3.0
        topics_covered = result.get("topics_covered", [])
        if topics_covered:
            last_topic = topics_covered[-1]
            last_score_val = scores.get(last_topic, 3.0)
        elif result.get("current_topic") in scores:
            last_score_val = scores.get(result["current_topic"], 3.0)
            
        turn_percentage = (last_score_val / 5.0) * 100
        
        # Next question
        next_question_raw = result.get("last_question") if not is_complete else None
        q_number = result.get("turn_count", 0) + 1
        
        q_text, q_type, options, initial_code = _parse_structured_question(next_question_raw)

        final_score = None
        if is_complete:
            report = result.get("final_report", {})
            final_score_raw = report.get("overall_score", 3.0) if report else 3.0
            final_score = (final_score_raw / 5.0) * 100
            
            # Sync candidate score to Excel
            try:
                from backend.routes.candidates import update_candidate_score
                update_candidate_score(result["candidate_name"], final_score)
                print(f"Excel updated successfully for candidate: {result['candidate_name']}")
            except Exception as ex:
                print(f"Error syncing score to Excel: {ex}")
                
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
            final_score=final_score
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to process answer. Please try again.")

@router.get("/interview/session/{session_id}")
def get_session_status(session_id: str):
    """Get current session status from Supabase rows and PostgreSQL checkpoint state."""
    session = _fetch_session(session_id)
    candidate = _fetch_candidate(session["candidate_id"])
    turns = _fetch_turns(session_id)
    messages = _fetch_messages(session_id)
        
    config = {"configurable": {"thread_id": session_id}}
    graph = _get_graph()
    state = graph.get_state(config)
    
    if not state or not state.values:
        raise HTTPException(status_code=404, detail="State not found for session")
        
    values = state.values
    scores = session.get("scores") or values.get("scores", {})
    avg_score = 0.0
    if scores:
        avg_score = (sum(scores.values()) / len(scores) / 5.0) * 100
        
    final_score = _fetch_final_score(session_id)
        
    return {
        "session_id": session_id,
        "candidate_name": candidate.get("full_name") or values.get("candidate_name"),
        "candidate_email": candidate.get("email"),
        "completed": session.get("status") == "completed",
        "current_topic": session.get("current_topic") or values.get("current_topic", ""),
        "question_number": int(session.get("turn_count") or values.get("turn_count", 0)) + 1,
        "total_questions": _question_limit(),
        "answers_so_far": len(turns),
        "average_score": avg_score,
        "final_score": final_score,
        "turns": turns,
        "messages": messages
    }

@router.get("/interview/history/{candidate_name}")
def get_candidate_interview_history(candidate_name: str):
    """Get interview history for a candidate from Supabase."""
    db = _require_db_client()
    history = []

    try:
        candidate_res = db.table("candidates").select("*").eq("full_name", candidate_name).limit(1).execute()
        if not candidate_res.data:
            return {"candidate_name": candidate_name, "sessions": []}

        candidate = candidate_res.data[0]
        sessions_res = (
            db.table("interview_sessions")
            .select("*")
            .eq("candidate_id", candidate["id"])
            .order("started_at", desc=True)
            .execute()
        )
    except Exception as exc:
        print(f"Error loading candidate interview history from Supabase: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load candidate history")

    for session in sessions_res.data or []:
        session_id = session["id"]
        turns = _fetch_turns(session_id)
        history.append({
            "session_id": session_id,
            "completed": session.get("status") == "completed",
            "completed_at": session.get("ended_at"),
            "final_score": _fetch_final_score(session_id),
            "total_answers": len(turns),
            "answers": turns,
            "messages": _fetch_messages(session_id),
        })
            
    return {"candidate_name": candidate_name, "sessions": history}
