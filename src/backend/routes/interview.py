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
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import concurrent.futures

from agent.graph import build_graph

router = APIRouter(tags=["Interview"])

# Compile the LangGraph instance
graph = build_graph()

# Store session metadata (in-memory)
interview_sessions: Dict[str, dict] = {}

class StartInterviewRequest(BaseModel):
    candidate_name: str
    candidate_email: str

class StartInterviewResponse(BaseModel):
    session_id: str
    candidate_name: str
    first_question: str
    question_type: str = "text"
    options: Optional[List[str]] = None
    initial_code: Optional[str] = None
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
    question_number: int
    total_questions: int
    is_complete: bool
    score: Optional[float] = None
    feedback: Optional[str] = None
    final_score: Optional[float] = None

@router.post("/interview/start", response_model=StartInterviewResponse)
def start_interview(request: StartInterviewRequest):
    """Start a new interview session - running the LangGraph agent"""
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
        # Run graph with timeout to prevent hanging on slow LLM responses
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(graph.invoke, initial_state, config)
            try:
                result = future.result(timeout=120)
            except concurrent.futures.TimeoutError:
                raise HTTPException(status_code=504, detail="Interview initialization timed out. Please try again.")
        
        first_question_raw = result.get("last_question", "Hello! Let's start the interview.")
        
        # Parse structured question if JSON
        q_text = first_question_raw
        q_type = "text"
        options = None
        initial_code = None
        try:
            import json
            q_data = json.loads(first_question_raw)
            if isinstance(q_data, dict) and "type" in q_data:
                q_text = q_data.get("text", "")
                q_type = q_data.get("type", "text")
                options = q_data.get("options")
                initial_code = q_data.get("initial_code")
        except:
            pass

        # Store in-memory metadata for compatibility
        interview_sessions[session_id] = {
            "candidate_name": request.candidate_name,
            "candidate_email": request.candidate_email,
            "started_at": datetime.now().isoformat(),
            "completed": False,
            "answers": []
        }
        
        return StartInterviewResponse(
            session_id=session_id,
            candidate_name=request.candidate_name,
            first_question=q_text,
            question_type=q_type,
            options=options,
            initial_code=initial_code,
            question_number=1,
            total_questions=5  # 5 required topics
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting interview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize interview: {str(e)}")

@router.post("/interview/answer", response_model=SubmitAnswerResponse)
def submit_answer(request: SubmitAnswerRequest):
    """Submit an answer and resume the LangGraph execution to get evaluation and next question"""
    session_id = request.session_id
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        # Get current state to know which question was asked
        state = graph.get_state(config)
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
        
        # Store in in-memory session metadata
        interview_sessions[session_id]["answers"].append({
            "question": last_question,
            "answer": request.answer,
            "score": last_score_val,
            "percentage": turn_percentage,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })
        
        # Next question
        next_question_raw = result.get("last_question") if not is_complete else None
        q_number = result.get("turn_count", 0) + 1
        
        q_text = next_question_raw
        q_type = "text"
        options = None
        initial_code = None
        if next_question_raw:
            try:
                import json
                q_data = json.loads(next_question_raw)
                if isinstance(q_data, dict) and "type" in q_data:
                    q_text = q_data.get("text", "")
                    q_type = q_data.get("type", "text")
                    options = q_data.get("options")
                    initial_code = q_data.get("initial_code")
            except:
                pass

        final_score = None
        if is_complete:
            report = result.get("final_report", {})
            final_score_raw = report.get("overall_score", 3.0) if report else 3.0
            final_score = (final_score_raw / 5.0) * 100
            
            interview_sessions[session_id]["completed"] = True
            interview_sessions[session_id]["completed_at"] = datetime.now().isoformat()
            interview_sessions[session_id]["final_score"] = final_score
            
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
            question_number=q_number,
            total_questions=5,
            is_complete=is_complete,
            score=turn_percentage,
            feedback=feedback,
            final_score=final_score
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process answer: {str(e)}")

@router.get("/interview/session/{session_id}")
def get_session_status(session_id: str):
    """Get current session status from LangGraph state"""
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    config = {"configurable": {"thread_id": session_id}}
    state = graph.get_state(config)
    
    if not state or not state.values:
        raise HTTPException(status_code=404, detail="State not found for session")
        
    values = state.values
    scores = values.get("scores", {})
    avg_score = 0.0
    if scores:
        avg_score = (sum(scores.values()) / len(scores) / 5.0) * 100
        
    final_score = None
    if values.get("is_complete"):
        report = values.get("final_report", {})
        final_score_raw = report.get("overall_score", 3.0) if report else 3.0
        final_score = (final_score_raw / 5.0) * 100
        
    return {
        "session_id": session_id,
        "candidate_name": values.get("candidate_name"),
        "completed": values.get("is_complete", False),
        "question_number": values.get("turn_count", 0) + 1,
        "total_questions": 5,
        "answers_so_far": len(values.get("answers", [])),
        "average_score": avg_score,
        "final_score": final_score
    }

@router.get("/interview/history/{candidate_name}")
def get_candidate_interview_history(candidate_name: str):
    """Get interview history for a candidate"""
    history = []
    for session_id, session in interview_sessions.items():
        if session["candidate_name"] == candidate_name:
            history.append({
                "session_id": session_id,
                "completed": session["completed"],
                "completed_at": session.get("completed_at"),
                "final_score": session.get("final_score"),
                "total_answers": len(session.get("answers", [])),
                "answers": session.get("answers", [])
            })
            
    return {"candidate_name": candidate_name, "sessions": history}