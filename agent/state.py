from typing import TypedDict, List, Optional

class InterviewState(TypedDict):
    candidate_id: str
    candidate_name: str
    current_topic: str               # e.g. "experience", "skills", "projects"
    topics_covered: List[str]
    questions_asked: List[str]
    answers: List[str]               # parallel list to questions_asked
    scores: dict                     # {"experience": 3, "skills": 4, ...}
    missing_info: List[str]          # topics not yet sufficiently covered
    last_question: str
    last_answer: str
    turn_count: int
    is_complete: bool
    final_report: Optional[dict]
