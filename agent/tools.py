def get_program_requirements() -> dict:
    """
    Static replacement for RAG. Returns bootcamp requirements,
    required topics, and evaluation rubric as a plain dict.
    Do NOT call any external API or vector DB.
    """
    return {
        "required_topics": ["background", "education", "experience", "skills", "projects"],
        "skills_to_assess": ["Python", "ML basics", "problem solving", "communication"],
        "rubric": {
            "excellent": "Clear, detailed, relevant answer with examples.",
            "good": "Mostly relevant, minor gaps.",
            "weak": "Vague or off-topic, needs probing.",
        }
    }

def generate_question(topic: str, context: dict, asked_so_far: list) -> str:
    """STUB — M2 will replace this."""
    return f"[STUB] Tell me about your {topic}."

def evaluate_answer(question: str, answer: str, rubric: dict) -> dict:
    """
    STUB — M2 will replace this.
    Must return: {"score": int (1-5), "feedback": str, "needs_probe": bool, "extracted_skills": list}
    """
    return {"score": 3, "feedback": "stub feedback", "needs_probe": False, "extracted_skills": []}

def update_candidate_profile(candidate_id: str, topic: str, answer: str, score: int) -> bool:
    """STUB — M3 will replace this. Must persist to PostgreSQL."""
    print(f"[STUB] Saving profile for {candidate_id}: {topic} = {score}")
    return True

def identify_missing_info(topics_covered: list, required_topics: list) -> list:
    """STUB — M3 will replace this."""
    return [t for t in required_topics if t not in topics_covered]

def calculate_score(scores: dict) -> float:
    """STUB — M3 will replace this."""
    return round(sum(scores.values()) / len(scores), 2) if scores else 0.0

def generate_report(candidate_id: str, scores: dict, answers: list) -> dict:
    """STUB — M3 will replace this."""
    return {"candidate_id": candidate_id, "scores": scores, "overall": calculate_score(scores), "summary": "stub report"}
