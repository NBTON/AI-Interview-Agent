from state import InterviewState
from tools import (
    get_program_requirements,
    ensure_candidate_and_session,
    generate_question,
    generate_probe_question,
    evaluate_answer,
    record_turn_and_update_profile,
    log_message,
    update_db_session_state,
    identify_missing_info,
    generate_report,
    empty_score_payload,
    normalize_scores_payload,
    append_turn_score
)

def node_init(state: InterviewState) -> dict:
    print("[System] Initializing interview session...")
    reqs = get_program_requirements()
    
    # Initialize DB candidate registry and session state
    db_info = ensure_candidate_and_session(
        candidate_id=state["candidate_id"],
        candidate_name=state["candidate_name"],
        session_id=state.get("session_id") or None
    )
    
    greeting_question = "Hello! Welcome to the interview. Let's get started."
    log_message(db_info["session_id"], "assistant", greeting_question)
    
    return {
        "candidate_id": db_info["candidate_id"],
        "session_id": db_info["session_id"],
        "program_id": db_info["program_id"],
        "last_question": greeting_question,
        "missing_info": reqs["required_topics"],
        "topics_covered": [],
        "questions_asked": [],
        "answers": [],
        "scores": empty_score_payload(),
        "probe_count": 0,
        "needs_probe": False,
        "turn_count": 0,
        "is_complete": False,
        "feedback": "",
        "extracted_skills": [],
        "extracted_info": {},
        "last_answer": "",
        "tier_assigned": "",
        "skills_max_turns": 3,
        "topic_depths": {}
    }


def node_router(state: InterviewState) -> str:
    # Route to evaluate if the candidate has just provided an answer
    if state.get("last_answer"):
        return "evaluate"
        
    reqs = get_program_requirements()
    min_turns = reqs.get("min_turns", 10)
    max_turns = reqs.get("max_turns", 30)
    turn_count = state.get("turn_count", 0)
    
    # Wrap up only after the adaptive minimum is satisfied, or at the hard cap.
    if turn_count >= max_turns:
        return "wrap_up"
    if not state.get("missing_info") and turn_count >= min_turns:
        return "wrap_up"
        
    return "generate_question"


def node_evaluation(state: InterviewState) -> dict:
    reqs = get_program_requirements()
    current_topic = state["current_topic"]
    
    print(f"[Evaluation Agent] Evaluating response for topic '{current_topic}'...")
    
    eval_result = evaluate_answer(
        question=state["last_question"],
        answer=state["last_answer"],
        rubric=reqs["rubric"]
    )
    
    scores = append_turn_score(
        state.get("scores"),
        current_topic,
        state["turn_count"] + 1,
        eval_result,
        state.get("tier_assigned", "")
    )
    
    return {
        "feedback": eval_result["feedback"],
        "needs_probe": eval_result["needs_probe"],
        "extracted_skills": eval_result["extracted_skills"],
        "extracted_info": eval_result["extracted_info"],
        "scores": scores
    }


def node_profile_builder(state: InterviewState) -> dict:
    current_topic = state["current_topic"]
    print(f"[Profile Builder Agent] Saving details & updating memory for '{current_topic}'...")
    
    scores = normalize_scores_payload(state.get("scores"), state.get("tier_assigned", ""))
    topic_score = scores.get("topic_scores", {}).get(current_topic, {}).get("final_topic_score", 3.0)
    
    eval_result = {
        "score": int(round(topic_score)),
        "feedback": state["feedback"],
        "needs_probe": state["needs_probe"],
        "extracted_skills": state["extracted_skills"],
        "extracted_info": state["extracted_info"]
    }
    
    # Save the turn details and update candidate_profiles structured memory (long-term memory)
    success, updated_scores = record_turn_and_update_profile(
        session_id=state["session_id"],
        candidate_id=state["candidate_id"],
        turn_number=state["turn_count"] + 1,
        topic=current_topic,
        question=state["last_question"],
        answer=state["last_answer"],
        eval_result=eval_result,
        current_scores=scores
    )
    
    reqs = get_program_requirements()
    
    # STEP 6: Skills turn count limit constraint
    topic_depths = dict(state.get("topic_depths") or {})
    topic_depth = topic_depths.get(current_topic, "standard")
    max_probes = 0 if topic_depth == "light" else 2
    if current_topic == "skills":
        skills_limit = state.get("skills_max_turns", 3)
        max_probes = max(0, skills_limit - 1)
    
    # Determine if we should probe or finalize coverage of this topic
    if state["needs_probe"] and state["probe_count"] < max_probes:
        new_covered = state["topics_covered"]
        new_missing = state["missing_info"]
        new_probe_count = state["probe_count"] + 1
        print(f"[Profile Builder Agent] Topic '{current_topic}' requires follow-up probing (consecutive probes: {new_probe_count}/{max_probes}).")
    else:
        new_covered = list(dict.fromkeys(state["topics_covered"] + [current_topic]))
        if current_topic == "background":
            bg_score = updated_scores.get("topic_scores", {}).get("background", {}).get("final_topic_score", 3.0)
            # Inspect candidate response for work experience indicators
            ans_text = state["last_answer"].lower() if state.get("last_answer") else ""
            is_experienced = bg_score >= 4.0 or any(w in ans_text for w in ["work", "job", "developer", "engineer", "years", "senior", "lead"])
            
            if is_experienced:
                # Experienced path: cover education lightly instead of omitting it.
                topic_depths = {
                    "background": "standard",
                    "experience": "deep",
                    "projects": "deep",
                    "skills": "deep",
                    "education": "light",
                }
                new_missing = [t for t in ["experience", "projects", "skills", "education"] if t not in new_covered]
                print("[Branching] Candidate identified as EXPERIENCED. Path: experience -> projects -> skills -> light education.")
            else:
                # Beginner/student path: cover experience lightly instead of omitting it.
                topic_depths = {
                    "background": "standard",
                    "education": "standard",
                    "skills": "standard",
                    "projects": "standard",
                    "experience": "light",
                }
                new_missing = [t for t in ["education", "skills", "projects", "experience"] if t not in new_covered]
                print("[Branching] Candidate identified as BEGINNER/STUDENT. Path: education -> skills -> projects -> light experience.")
        else:
            new_missing = identify_missing_info(new_covered, state["missing_info"])
            
        new_probe_count = 0
        print(f"[Profile Builder Agent] Topic '{current_topic}' coverage completed. Next topics remaining: {new_missing}")
        
    new_questions = state["questions_asked"] + [state["last_question"]]
    new_answers = state["answers"] + [state["last_answer"]]
    new_turn_count = state["turn_count"] + 1
    
    # Sync status to Supabase interview_sessions
    update_db_session_state(
        session_id=state["session_id"],
        current_topic=current_topic if new_probe_count > 0 else (new_missing[0] if new_missing else ""),
        covered=new_covered,
        missing=new_missing,
        count=new_turn_count,
        scores=updated_scores
    )
    
    return {
        "topics_covered": new_covered,
        "missing_info": new_missing,
        "probe_count": new_probe_count,
        "questions_asked": new_questions,
        "answers": new_answers,
        "turn_count": new_turn_count,
        "current_topic": current_topic if new_probe_count > 0 else (new_missing[0] if new_missing else current_topic),
        "last_answer": "",  # Clear to avoid re-evaluation on loop
        "scores": updated_scores,
        "topic_depths": topic_depths
    }


def node_interviewer(state: InterviewState) -> dict:
    reqs = get_program_requirements()
    topic = state["current_topic"]
    
    if state["probe_count"] > 0:
        # Generate follow-up probe question
        print(f"[Interviewer Agent] Generating follow-up probing question for topic '{topic}'...")
        prev_question = state["questions_asked"][-1] if state["questions_asked"] else state["last_question"]
        prev_answer = state["answers"][-1] if state["answers"] else ""
        question = generate_probe_question(topic, prev_question, prev_answer)
    else:
        # Generate a new question on the next missing topic
        if state["missing_info"]:
            topic = state["missing_info"][0]
        else:
            required_topics = reqs.get("required_topics", ["skills", "projects"])
            turn_count = state.get("turn_count", 0)
            topic = required_topics[turn_count % len(required_topics)]
        print(f"[Interviewer Agent] Generating fresh question for topic '{topic}'...")
        
        # Build context dict with scores and requirements
        context_dict = {
            **reqs,
            "scores": state.get("scores", {}),
            "topics_covered": state.get("topics_covered", []),
            "topic_depths": state.get("topic_depths", {}),
            "tier_assigned": state.get("tier_assigned", ""),
            "candidate_name": state.get("candidate_name", "")
        }
        question = generate_question(topic, context_dict, state["questions_asked"], state["candidate_id"])
        
    # Log the question to conversation_messages
    log_message(state["session_id"], "assistant", question)
    
    return {
        "last_question": question,
        "current_topic": topic,
    }


def node_wrap_up(state: InterviewState) -> dict:
    print("[Decision Support Agent] Compiling final candidate report and recommendations...")
    
    report = generate_report(
        session_id=state["session_id"],
        candidate_id=state["candidate_id"],
        scores=state["scores"],
        candidate_name=state["candidate_name"]
    )
    
    return {
        "is_complete": True,
        "final_report": report
    }


def determine_next_topic_routing(state: InterviewState) -> dict:
    """
    LangGraph routing node that inspects background score and assigns adaptive track and constraints.
    """
    scores = normalize_scores_payload(state.get("scores"), state.get("tier_assigned", ""))
    topic_scores = scores.get("topic_scores", {})
    bg_info = topic_scores.get("background", {})
    bg_score = bg_info.get("final_topic_score")
    
    tier = state.get("tier_assigned", "")
    skills_limit = state.get("skills_max_turns", 3)
    
    if bg_score is not None and not tier:
        if bg_score >= 4.0:
            tier = "advanced_track"
            skills_limit = 5
            print(f"[Adaptive Routing] Background score is {bg_score} >= 4.0. Assigning candidate to 'advanced_track' (up to 5 turns for skills).")
        else:
            tier = "beginner_adaptive"
            skills_limit = 2
            print(f"[Adaptive Routing] Background score is {bg_score} < 4.0. Assigning candidate to 'beginner_adaptive' (up to 2 turns for skills).")
            
    updated_scores = normalize_scores_payload(scores, tier)
    updated_scores["summary_metrics"]["tier_assigned"] = tier
        
    return {
        "scores": updated_scores,
        "tier_assigned": tier,
        "skills_max_turns": skills_limit,
        "topic_depths": state.get("topic_depths", {})
    }
