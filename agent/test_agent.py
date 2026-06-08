import os
import sys

# Ensure the agent directory is in Python path for absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph import build_graph

def test_interview_flow():
    graph = build_graph()
    
    initial_state = {
        "candidate_id": "test-002",
        "candidate_name": "Test Candidate",
        "current_topic": "",
        "topics_covered": [],
        "questions_asked": [],
        "answers": [],
        "scores": {},
        "missing_info": [],
        "last_question": "",
        "last_answer": "",
        "turn_count": 0,
        "is_complete": False,
        "final_report": None,
    }
    
    config = {"configurable": {"thread_id": "test-002"}}
    
    # Start graph (runs init and generates first question, then interrupts)
    result = graph.invoke(initial_state, config)
    
    mock_answers = {
        "background": "My background is in Computer Science.",
        "education": "I graduated from KFUPM.",
        "experience": "I have 3 years of software development experience.",
        "skills": "I am proficient in Python, SQL, and Machine Learning basics.",
        "projects": "I built an automated agent using LangGraph."
    }
    
    # Loop to simulate the interview turn-by-turn
    while not result["is_complete"]:
        current_topic = result["current_topic"]
        assert current_topic in mock_answers, f"Topic '{current_topic}' not in mock answers"
        
        answer = mock_answers[current_topic]
        
        # Resume the graph by supplying the answer to the checkpoint and calling invoke(None)
        graph.update_state(config, {"last_answer": answer})
        result = graph.invoke(None, config)
        
    # Assertions to verify the final complete state
    assert result["is_complete"] is True
    assert result["final_report"] is not None
    assert result["final_report"]["candidate_id"] == "test-002"
    assert 1.0 <= result["final_report"]["overall"] <= 5.0
    assert len(result["topics_covered"]) == 5
    assert len(result["questions_asked"]) == 5
    assert len(result["answers"]) == 5
    print("All updated interview flow assertions passed successfully!")

if __name__ == "__main__":
    test_interview_flow()
