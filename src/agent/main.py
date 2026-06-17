import os
import sys

# Ensure the agent directory is in Python path for absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure stdout/stdin encoding to support UTF-8 (emojis, etc.) on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from graph import build_graph

graph = build_graph()

initial_state = {
    "candidate_id": "test-001",
    "candidate_name": "Omar",
    "session_id": "",
    "program_id": "",
    "current_topic": "",
    "topics_covered": [],
    "questions_asked": [],
    "answers": [],
    "scores": {
        "summary_metrics": { "overall_score": 0.0, "total_turns_taken": 0, "tier_assigned": "" },
        "topic_scores": {}
    },
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
    "tier_assigned": "",
    "skills_max_turns": 3
}

config = {"configurable": {"thread_id": "test-001"}}

# First invocation to start the graph and execute up to the first question generation interrupt
result = graph.invoke(initial_state, config)

# Simulate a full interview turn by turn
while True:
    if result["is_complete"]:
        print("\n✅ Interview complete.")
        import json
        print(json.dumps(result["final_report"], indent=2))
        break
        
    print(f"\n🤖 Agent: {result['last_question']}")
    user_input = input("You: ")
    
    # Standard LangGraph resume pattern: 
    # 1. Update the state of the thread checkpoint
    graph.update_state(config, {"last_answer": user_input})
    # 2. Resume execution from the checkpoint
    result = graph.invoke(None, config)
