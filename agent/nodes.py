from state import InterviewState
from tools import (get_program_requirements, generate_question, evaluate_answer,
                   update_candidate_profile, identify_missing_info,
                   calculate_score, generate_report)

def node_ask_question(state: InterviewState) -> dict:
    reqs = get_program_requirements()
    topic = state["missing_info"][0] if state["missing_info"] else state["current_topic"]
    question = generate_question(topic, reqs, state["questions_asked"])
    return {"last_question": question, "current_topic": topic}

def node_evaluate_answer(state: InterviewState) -> dict:
    reqs = get_program_requirements()
    result = evaluate_answer(state["last_question"], state["last_answer"], reqs["rubric"])
    new_scores = {**state["scores"], state["current_topic"]: result["score"]}
    new_questions = state["questions_asked"] + [state["last_question"]]
    new_answers = state["answers"] + [state["last_answer"]]
    new_covered = list(set(state["topics_covered"] + [state["current_topic"]]))
    return {
        "scores": new_scores,
        "questions_asked": new_questions,
        "answers": new_answers,
        "topics_covered": new_covered,
    }

def node_update_profile(state: InterviewState) -> dict:
    update_candidate_profile(
        state["candidate_id"],
        state["current_topic"],
        state["last_answer"],
        state["scores"].get(state["current_topic"], 0)
    )
    return {}

def node_check_gaps(state: InterviewState) -> dict:
    reqs = get_program_requirements()
    missing = identify_missing_info(state["topics_covered"], reqs["required_topics"])
    return {"missing_info": missing, "turn_count": state["turn_count"] + 1}

def node_terminate(state: InterviewState) -> dict:
    report = generate_report(state["candidate_id"], state["scores"], state["answers"])
    score = calculate_score(state["scores"])
    return {"is_complete": True, "final_report": {**report, "overall_score": score}}
