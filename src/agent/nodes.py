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
    calculate_score,
    generate_report
)

def node_init(state: InterviewState) -> dict:
    print("🚀 [System] Initializing interview session...")
    reqs = get_program_requirements()
    
    # Initialize DB candidate registry and session state
    db_info = ensure_candidate_and_session(
        candidate_id=state["candidate_id"],
        candidate_name=state["candidate_name"]
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
        "scores": {},
        "probe_count": 0,
        "needs_probe": False,
        "turn_count": 0,
        "is_complete": False,
        "feedback": "",
        "extracted_skills": [],
        "extracted_info": {},
        "last_answer": ""
    }


def node_router(state: InterviewState) -> str:
    # Route to evaluate if the candidate has just provided an answer
    if state.get("last_answer"):
        return "evaluate"
        
    reqs = get_program_requirements()
    max_turns = reqs.get("max_turns", 15)
    
    # Wrap up if all topics are covered or turn count limit reached
    if not state.get("missing_info") or state.get("turn_count", 0) >= max_turns:
        return "wrap_up"
        
    return "generate_question"


def node_evaluation(state: InterviewState) -> dict:
    reqs = get_program_requirements()
    current_topic = state["current_topic"]
    
    print(f"🕵️‍♂️ [Evaluation Agent] Evaluating response for topic '{current_topic}'...")
    
    eval_result = evaluate_answer(
        question=state["last_question"],
        answer=state["last_answer"],
        rubric=reqs["rubric"]
    )
    
    new_scores = {**state["scores"], current_topic: eval_result["score"]}
    
    return {
        "feedback": eval_result["feedback"],
        "needs_probe": eval_result["needs_probe"],
        "extracted_skills": eval_result["extracted_skills"],
        "extracted_info": eval_result["extracted_info"],
        "scores": new_scores
    }


def node_profile_builder(state: InterviewState) -> dict:
    current_topic = state["current_topic"]
    print(f"🗂️ [Profile Builder Agent] Saving details & updating memory for '{current_topic}'...")
    
    eval_result = {
        "score": state["scores"].get(current_topic, 3),
        "feedback": state["feedback"],
        "needs_probe": state["needs_probe"],
        "extracted_skills": state["extracted_skills"],
        "extracted_info": state["extracted_info"]
    }
    
    # Save the turn details and update candidate_profiles structured memory (long-term memory)
    record_turn_and_update_profile(
        session_id=state["session_id"],
        candidate_id=state["candidate_id"],
        turn_number=state["turn_count"] + 1,
        topic=current_topic,
        question=state["last_question"],
        answer=state["last_answer"],
        eval_result=eval_result
    )
    
    reqs = get_program_requirements()
    
    # Determine if we should probe or finalize coverage of this topic
    if state["needs_probe"] and state["probe_count"] < 2:
        new_covered = state["topics_covered"]
        new_missing = state["missing_info"]
        new_probe_count = state["probe_count"] + 1
        print(f"🔍 [Profile Builder Agent] Topic '{current_topic}' requires follow-up probing (consecutive probes: {new_probe_count}/2).")
    else:
        new_covered = list(set(state["topics_covered"] + [current_topic]))
        if current_topic == "background":
            bg_score = state["scores"].get("background", 3)
            # Inspect candidate response for work experience indicators
            ans_text = state["last_answer"].lower() if state.get("last_answer") else ""
            is_experienced = bg_score >= 4 or any(w in ans_text for w in ["work", "job", "developer", "engineer", "years", "senior", "lead"])
            
            if is_experienced:
                # Experienced path: Skip education, go to experience -> projects -> skills
                new_missing = [t for t in ["experience", "projects", "skills"] if t not in new_covered]
                print("🔀 [Branching] Candidate identified as EXPERIENCED. Path: experience -> projects -> skills. Skipping education.")
            else:
                # Beginner/Student path: Go to education -> skills -> projects
                new_missing = [t for t in ["education", "skills", "projects"] if t not in new_covered]
                print("🔀 [Branching] Candidate identified as BEGINNER/STUDENT. Path: education -> skills -> projects. Skipping experience.")
        else:
            new_missing = identify_missing_info(new_covered, state["missing_info"])
            
        new_probe_count = 0
        print(f"✅ [Profile Builder Agent] Topic '{current_topic}' coverage completed. Next topics remaining: {new_missing}")
        
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
        scores=state["scores"]
    )
    
    return {
        "topics_covered": new_covered,
        "missing_info": new_missing,
        "probe_count": new_probe_count,
        "questions_asked": new_questions,
        "answers": new_answers,
        "turn_count": new_turn_count,
        "last_answer": "",  # Clear to avoid re-evaluation on loop
    }


def node_interviewer(state: InterviewState) -> dict:
    reqs = get_program_requirements()
    topic = state["current_topic"]
    
    if state["probe_count"] > 0:
        # Generate follow-up probe question
        print(f"🎤 [Interviewer Agent] Generating follow-up probing question for topic '{topic}'...")
        prev_question = state["questions_asked"][-1] if state["questions_asked"] else state["last_question"]
        prev_answer = state["answers"][-1] if state["answers"] else ""
        question = generate_probe_question(topic, prev_question, prev_answer)
    else:
        # Generate a new question on the next missing topic
        topic = state["missing_info"][0] if state["missing_info"] else state["current_topic"]
        print(f"🎤 [Interviewer Agent] Generating fresh question for topic '{topic}'...")
        
        # Build context dict with scores and requirements
        context_dict = {
            **reqs,
            "scores": state.get("scores", {}),
            "topics_covered": state.get("topics_covered", []),
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
    print("📊 [Decision Support Agent] Compiling final candidate report and recommendations...")
    
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
