"""
Interview Routes - Matches Chatbot.py interview flow
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uuid

router = APIRouter(tags=["Interview"])

# Store active interview sessions (in-memory for MVP)
interview_sessions: Dict[str, dict] = {}

# Question bank for the interview
QUESTIONS = [
    "Tell me about yourself.",
    "What is your educational background?",
    "Describe your relevant work experience.",
    "What technical skills do you have?",
    "Tell me about a project you've worked on.",
    "Why are you interested in this bootcamp?",
    "Where do you see yourself in 5 years?",
    "Do you have any questions for us?"
]

# Answer evaluation (simple length-based for MVP)
def evaluate_answer(answer: str, question_number: int) -> dict:
    """Simple evaluation based on answer length and keywords"""
    answer_length = len(answer.split())
    
    if answer_length < 10:
        score = 2
        feedback = "Your answer is quite brief. Could you provide more detail?"
    elif answer_length < 30:
        score = 3
        feedback = "Good answer, but adding specific examples would strengthen it."
    elif answer_length < 60:
        score = 4
        feedback = "Good answer with reasonable detail."
    else:
        score = 5
        feedback = "Excellent detailed answer!"
    
    # Calculate percentage score (0-100)
    percentage = (score / 5) * 100
    
    return {
        "score": score,
        "percentage": percentage,
        "feedback": feedback
    }

class StartInterviewRequest(BaseModel):
    candidate_name: str
    candidate_email: str

class StartInterviewResponse(BaseModel):
    session_id: str
    candidate_name: str
    first_question: str
    question_number: int
    total_questions: int

class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer: str

class SubmitAnswerResponse(BaseModel):
    session_id: str
    next_question: Optional[str] = None
    question_number: int
    total_questions: int
    is_complete: bool
    score: Optional[float] = None
    feedback: Optional[str] = None
    final_score: Optional[float] = None

@router.post("/interview/start", response_model=StartInterviewResponse)
def start_interview(request: StartInterviewRequest):
    """Start a new interview session - matches Chatbot.py"""
    
    session_id = str(uuid.uuid4())
    
    interview_sessions[session_id] = {
        "candidate_name": request.candidate_name,
        "candidate_email": request.candidate_email,
        "started_at": datetime.now().isoformat(),
        "current_question": 0,
        "answers": [],
        "scores": [],
        "feedbacks": [],
        "completed": False
    }
    
    return StartInterviewResponse(
        session_id=session_id,
        candidate_name=request.candidate_name,
        first_question=QUESTIONS[0],
        question_number=1,
        total_questions=len(QUESTIONS)
    )

@router.post("/interview/answer", response_model=SubmitAnswerResponse)
def submit_answer(request: SubmitAnswerRequest):
    """Submit an answer and get next question - matches Chatbot.py"""
    
    if request.session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = interview_sessions[request.session_id]
    current_q_index = session["current_question"]
    total = len(QUESTIONS)
    
    # Evaluate the answer
    evaluation = evaluate_answer(request.answer, current_q_index + 1)
    
    # Store the answer
    session["answers"].append({
        "question": QUESTIONS[current_q_index],
        "answer": request.answer,
        "score": evaluation["score"],
        "percentage": evaluation["percentage"],
        "feedback": evaluation["feedback"],
        "timestamp": datetime.now().isoformat()
    })
    session["scores"].append(evaluation["percentage"])
    session["feedbacks"].append(evaluation["feedback"])
    
    # Move to next question
    next_q_index = current_q_index + 1
    session["current_question"] = next_q_index
    
    # Check if interview is complete
    if next_q_index >= total:
        # Calculate final score
        final_score = sum(session["scores"]) / len(session["scores"])
        session["completed"] = True
        session["completed_at"] = datetime.now().isoformat()
        session["final_score"] = final_score
        
        return SubmitAnswerResponse(
            session_id=request.session_id,
            next_question=None,
            question_number=next_q_index,
            total_questions=total,
            is_complete=True,
            score=evaluation["percentage"],
            feedback=evaluation["feedback"],
            final_score=round(final_score, 2)
        )
    
    # Return next question
    return SubmitAnswerResponse(
        session_id=request.session_id,
        next_question=QUESTIONS[next_q_index],
        question_number=next_q_index + 1,
        total_questions=total,
        is_complete=False,
        score=evaluation["percentage"],
        feedback=evaluation["feedback"],
        final_score=None
    )

@router.get("/interview/session/{session_id}")
def get_session_status(session_id: str):
    """Get current session status"""
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = interview_sessions[session_id]
    
    return {
        "session_id": session_id,
        "candidate_name": session["candidate_name"],
        "completed": session["completed"],
        "question_number": session["current_question"] + 1,
        "total_questions": len(QUESTIONS),
        "answers_so_far": len(session["answers"]),
        "average_score": sum(session["scores"]) / len(session["scores"]) if session["scores"] else 0,
        "final_score": session.get("final_score")
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
                "total_answers": len(session["answers"]),
                "answers": session["answers"]
            })
    
    return {"candidate_name": candidate_name, "sessions": history}