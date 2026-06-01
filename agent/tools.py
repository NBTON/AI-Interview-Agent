def get_program_requirements() -> dict:
    """Returns static bootcamp requirements. Replaces RAG for v1."""
    return {
        "required_topics": ["background", "education", "experience", "skills", "projects"],
        "skills_to_assess": ["Python", "ML basics", "problem solving", "communication"],
        "rubric": {
            "excellent": "Clear, detailed, relevant answer with examples.",
            "good": "Mostly relevant, minor gaps.",
            "weak": "Vague or off-topic, needs probing.",
        }
    }

# --- Stubs for M2 (replace with real functions in Week 2) ---
def generate_question(topic: str, context: dict, asked_so_far: list) -> str:
    return f"[STUB] Tell me about your {topic}."

def evaluate_answer(question: str, answer: str, rubric: dict) -> dict:
    return {"score": 3, "feedback": "stub feedback", "needs_probe": False}

# --- Stubs for M3 ---
def update_candidate_profile(candidate_id: str, topic: str, answer: str, score: int) -> bool:
    return True

def identify_missing_info(topics_covered: list, required_topics: list) -> list:
    return [t for t in required_topics if t not in topics_covered]

def calculate_score(scores: dict) -> float:
    return sum(scores.values()) / len(scores) if scores else 0.0

def generate_report(candidate_id: str, scores: dict, answers: list) -> dict:
    return {"candidate_id": candidate_id, "scores": scores, "summary": "stub report"}
