from typing import TypedDict, List, Optional

class InterviewState(TypedDict):
    candidate_id: str
    candidate_name: str
    session_id: str                  # UUID tracking current interview session
    program_id: str                  # UUID tracking program criteria
    current_topic: str               # e.g. "experience", "skills", "projects"
    topics_covered: List[str]
    questions_asked: List[str]
    answers: List[str]               # parallel list to questions_asked
    scores: dict                     # {"experience": 3, "skills": 4, ...}
    missing_info: List[str]          # topics not yet sufficiently covered
    last_question: str
    last_answer: str
    turn_count: int
    probe_count: int                 # tracks consecutive follow-up probes for current topic
    needs_probe: bool                # flag from Evaluation Agent to Interviewer Agent
    extracted_skills: List[str]      # technical skills extracted in last turn
    extracted_info: dict             # structured profile details extracted in last turn
    feedback: str                    # evaluation feedback of last turn
    is_complete: bool
    final_report: Optional[dict]

