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

config = {"configurable": {"thread_id": "test-001"}}

# Simulate a full interview turn by turn
while True:
    result = graph.invoke(initial_state, config)
    print(f"\n🤖 Agent: {result['last_question']}")
    if result["is_complete"]:
        print("\n✅ Interview complete.")
        print(result["final_report"])
        break
    user_input = input("You: ")
    initial_state = {**result, "last_answer": user_input}
