import os
import sys

# Ensure the agent directory is in Python path for absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure stdout/stdin encoding to support UTF-8 (emojis, etc.) on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from graph import build_graph

def test_interview_flow():
    print("🧪 Starting Automated Multi-Agent Flow Verification...")
    graph = build_graph()
    
    initial_state = {
        "candidate_id": "test-002",
        "candidate_name": "Test Candidate",
        "session_id": "",
        "program_id": "",
        "current_topic": "",
        "topics_covered": [],
        "questions_asked": [],
        "answers": [],
        "scores": {},
        "missing_info": [],
        "last_question": "",
        "last_answer": "",
        "turn_count": 0,
        "probe_count": 0,
        "needs_probe": False,
        "extracted_skills": [],
        "extracted_info": {},
        "feedback": "",
        "is_complete": False,
        "final_report": None,
    }
    
    config = {"configurable": {"thread_id": "test-002"}}
    
    # Start graph (runs init and generates first question, then interrupts before evaluation)
    result = graph.invoke(initial_state, config)
    
    # Check that init correctly set up UUID session and program IDs
    assert result["session_id"] != "", "session_id was not initialized"
    assert result["candidate_id"] != "test-002", "candidate_id was not converted to a valid UUID format"
    
    mock_answers = {
        "background": "My background is in Computer Science with a strong interest in AI technologies.",
        "education": "I graduated from KFUPM with a Bachelor's degree in Software Engineering.",
        "experience": "I have 3 years of software development experience working on Python backends.",
        "skills": "I am highly proficient in Python, SQL databases, and Machine Learning basics like Scikit-Learn.",
        "projects": "I built an automated agent using LangGraph and integrated it with PostgreSQL."
    }
    
    # Loop to simulate the interview turn-by-turn
    while not result["is_complete"]:
        current_topic = result["current_topic"]
        assert current_topic in mock_answers, f"Topic '{current_topic}' not in mock answers"
        
        answer = mock_answers[current_topic]
        print(f"\n[Simulator] Current Topic: {current_topic}")
        print(f"[Agent Question]: {result['last_question']}")
        print(f"[Candidate Answer]: {answer}")
        
        # Resume the graph by supplying the answer to the checkpoint and calling invoke(None)
        graph.update_state(config, {"last_answer": answer})
        result = graph.invoke(None, config)
        
        # Output evaluation details from the nodes
        print(f"[Evaluation Feedback]: {result.get('feedback')}")
        print(f"[Extracted Skills]: {result.get('extracted_skills')}")
        print(f"[Extracted Info]: {result.get('extracted_info')}")
        print(f"[Topic Scores]: {result.get('scores')}")
        print(f"[Needs Probe?]: {result.get('needs_probe')} | [Probe Count]: {result.get('probe_count')}")
        
    # Assertions to verify the final complete state
    assert result["is_complete"] is True, "Graph failed to complete"
    report = result["final_report"]
    assert report is not None, "Report was not generated"
    assert report["candidate_id"] == result["candidate_id"], "Candidate UUID in report mismatch"
    assert report["session_id"] == result["session_id"], "Session UUID in report mismatch"
    assert 1.0 <= report["overall_score"] <= 5.0, "Overall score out of bounds"
    
    # Verify report structure
    assert "summary" in report, "Summary missing in report"
    assert "recommendation" in report, "Recommendation missing in report"
    assert report["recommendation"] in ["accept", "reject", "review"], f"Invalid recommendation: {report['recommendation']}"
    assert "strengths" in report, "Strengths missing in report"
    assert "weaknesses" in report, "Weaknesses missing in report"
    assert "decision_notes" in report, "Decision notes missing in report"
    
    print("\n✅ All multi-agent automated integration tests passed successfully!")

if __name__ == "__main__":
    test_interview_flow()
