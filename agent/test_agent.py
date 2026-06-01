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
        "current_topic": "background",
        "topics_covered": [],
        "questions_asked": [],
        "answers": [],
        "scores": {},
        "missing_info": ["background", "education", "experience", "skills", "projects"],
        "last_question": "",
        "last_answer": "",
        "turn_count": 0,
        "is_complete": False,
        "final_report": None,
    }
    
    config = {"configurable": {"thread_id": "test-002"}}
    
    result = graph.invoke(initial_state, config)
    
    # Assertions to verify the structure and state transitions
    assert result["is_complete"] is True
    assert result["final_report"] is not None
    assert result["final_report"]["candidate_id"] == "test-002"
    assert result["final_report"]["overall_score"] == 3.0
    assert len(result["topics_covered"]) == 5
    assert len(result["questions_asked"]) == 5
    assert len(result["answers"]) == 5
    print("All interview flow assertions passed successfully!")

if __name__ == "__main__":
    test_interview_flow()
