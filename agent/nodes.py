from state import InterviewState
from tools import (get_program_requirements, generate_question, evaluate_answer,
                   update_candidate_profile, identify_missing_info,
                   calculate_score, generate_report)

MAX_TURNS = 15

def node_init(state: InterviewState) -> dict:
    reqs = get_program_requirements()
    last_question = "Hello! Welcome to the interview. Let's get started."
    missing_info = reqs["required_topics"]
    return {
        "last_question": last_question,
        "missing_info": missing_info,
    }

def node_router(state: InterviewState) -> str:
    # "evaluate" — if last_answer is non-empty (user just replied)
    if state.get("last_answer"):
        return "evaluate"
    # "generate_question" — if missing_info is non-empty and turn limit not reached
    if state.get("missing_info") and state.get("turn_count", 0) < MAX_TURNS:
        return "generate_question"
    # "wrap_up" — if missing_info is empty OR turn_count >= MAX_TURNS
    return "wrap_up"

def node_evaluate_and_extract(state: InterviewState) -> dict:
    reqs = get_program_requirements()
    result = evaluate_answer(state["last_question"], state["last_answer"], reqs["rubric"])
    
    current_topic = state["current_topic"]
    
    new_scores = {**state["scores"], current_topic: result["score"]}
    new_questions = state["questions_asked"] + [state["last_question"]]
    new_answers = state["answers"] + [state["last_answer"]]
    new_covered = list(set(state["topics_covered"] + [current_topic]))
    
    # Save candidate profile (PostgreSQL stub)
    update_candidate_profile(
        state["candidate_id"],
        current_topic,
        state["last_answer"],
        result["score"]
    )
    
    # Identify missing info
    new_missing = identify_missing_info(new_covered, reqs["required_topics"])
    
    return {
        "scores": new_scores,
        "questions_asked": new_questions,
        "answers": new_answers,
        "topics_covered": new_covered,
        "missing_info": new_missing,
        "turn_count": state["turn_count"] + 1,
        "last_answer": "",  # Clear last_answer to prevent re-evaluation
    }

def node_generate_question(state: InterviewState) -> dict:
    reqs = get_program_requirements()
    
    # Pick next topic from missing_info[0]
    topic = state["missing_info"][0] if state["missing_info"] else state["current_topic"]
    
    # Generate question stub
    question = generate_question(topic, reqs, state["questions_asked"])
    
    return {
        "last_question": question,
        "current_topic": topic,
    }

def node_wrap_up(state: InterviewState) -> dict:
    score = calculate_score(state["scores"])
    report = generate_report(state["candidate_id"], state["scores"], state["answers"])
    report["overall"] = score
    
    return {
        "is_complete": True,
        "final_report": report,
    }
