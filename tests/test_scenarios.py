import os
import sys
from pathlib import Path

# Ensure the agent directory is in Python path for absolute imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
AGENT_DIR = SRC_DIR / "agent"

# Move any paths containing the local 'supabase' folder to the end of sys.path to avoid shadowing the third-party library
shadowing_paths = [str(PROJECT_ROOT), str(SRC_DIR), "", "."]
for path in shadowing_paths:
    while path in sys.path:
        sys.path.remove(path)
    sys.path.append(path)

# Add AGENT_DIR, SRC_DIR, and PROJECT_ROOT to sys.path so we can import internal modules
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Configure stdout/stdin encoding to support UTF-8 (emojis, etc.) on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from graph import build_graph

def generate_mock_candidate_answer(scenario: str, topic: str, question: str, probe_count: int) -> str:
    from tools import _llm
    from langchain_core.messages import HumanMessage
    
    if scenario == "Strong Candidate":
        system_instructions = (
            "You are roleplaying as a strong candidate for an elite AI and Software Engineering bootcamp. "
            "You have solid technical knowledge and practical experience. "
            "Your profile details are:\n"
            "- Background: 5 years of software engineering. Built a real-time recommendation engine using PySpark, ALS collaborative filtering, and Redis caching. Used Great Expectations for data validation.\n"
            "- Education: Bachelor's degree in Software Engineering from King Fahd University of Petroleum and Minerals (KFUPM). Applied Python and ML to build a predictive model for student academic performance, presenting regression models using simplified flowcharts.\n"
            "- Experience: 3 years at TechCorp as a backend developer. Optimized PostgreSQL query plans using EXPLAIN ANALYZE and composite indexes, reducing response times by 40%. Implemented FastAPI connection pooling with SQLAlchemy.\n"
            "- Skills: Proficient in Python, SQL (PostgreSQL), Scikit-Learn, PyTorch, and LangGraph. Recently debugged a memory leak in a Python background worker using memory_profiler and pdb, resolving the leak in a pandas DataFrame loop.\n"
            "- Projects: Built an AI customer support agent using LangGraph and PostgreSQL with pgvector, OpenAI embeddings, and cosine similarity. Validated queries with regex and measured Precision@K.\n\n"
            "An interviewer is asking you a question. Answer the question in a highly detailed, professional, and technically deep manner, using the profile facts above. "
            "Make sure you answer the specific details requested in the question. "
            "Return only your direct answer to the question. Do not include any preamble, quotes, or meta-commentary."
        )
    elif scenario == "Improving Candidate":
        if probe_count == 0:
            # First turn on this topic: give a very brief/simple answer
            system_instructions = (
                "You are roleplaying as a candidate for an AI bootcamp. "
                "For the first question on a topic, you must give a very brief, simple, or vague answer (e.g. 'I work with AI', 'I went to KFUPM', 'I am a programmer', 'I know Python and ML', or 'I made a chatbot'). "
                "Keep it to one short sentence. Do not elaborate. "
                "Return only your direct answer to the question. Do not include any preamble, quotes, or meta-commentary."
            )
        else:
            # Probed turn: give a detailed and strong answer
            system_instructions = (
                "You are roleplaying as a candidate for an AI bootcamp. "
                "Since the interviewer is asking a follow-up probing question, you must now elaborate and provide a strong, detailed, and technically competent response. "
                "Your profile details are:\n"
                "- Background: 2 years building computer vision models in Python, focusing on object detection using YOLOv8 on AWS.\n"
                "- Education: Bachelor's in Software Engineering from KFUPM. Coursework covered database design, software engineering lifecycle, and AI core courses.\n"
                "- Experience: 2 years as a backend developer building APIs with Flask/Django and managing Postgres databases. Helped migrate databases and rewrote SQL using Django's ORM.\n"
                "- Skills: Python, SQL, Git, Docker, and Scikit-Learn. Daily preprocessing and modeling.\n"
                "- Projects: Chatbot using LangChain, Streamlit, and FAISS vector database to answer questions from internal PDFs using RetrievalQA.\n\n"
                "Answer the interviewer's follow-up question in a detailed, professional, and technically deep manner using these facts. "
                "Return only your direct answer to the question. Do not include any preamble, quotes, or meta-commentary."
            )
    else:  # Weak Candidate
        system_instructions = (
            "You are roleplaying as a weak candidate for an AI bootcamp. "
            "You must provide extremely brief, vague, and generic answers that do not address the specific technical details requested by the interviewer. "
            "Even if probed, repeat the same generic or vague responses without adding new details. "
            "Keep your answers to one short, general sentence (e.g. 'My background is in Computer Science with a strong interest in AI', 'I graduated from KFUPM with a Software Engineering degree', 'I have 3 years of software experience on Python backends', 'I am highly proficient in Python, SQL, and ML', or 'I built an agent using LangGraph and PostgreSQL'). "
            "Return only your direct answer to the question. Do not include any preamble, quotes, or meta-commentary."
        )

    prompt = f"{system_instructions}\n\nInterviewer's Question:\n\"{question}\""
    
    try:
        response = _llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        print(f"[Fallback Mode] Candidate simulation LLM failed: {e}")
        if scenario == "Strong Candidate":
            fallbacks = {
                "background": "My background is in Computer Science with 5 years of software engineering. I built a real-time recommendation engine using PySpark, ALS collaborative filtering, and Redis caching. I used Great Expectations for data validation.",
                "education": "I graduated from KFUPM with a Bachelor's degree in Software Engineering. I applied Python and ML to build a predictive model for student academic performance, presenting regression models using simplified flowcharts.",
                "experience": "I have 3 years of software development experience at TechCorp as a backend developer. I optimized PostgreSQL query plans using EXPLAIN ANALYZE and composite indexes, reducing response times by 40%. Implemented FastAPI connection pooling with SQLAlchemy.",
                "skills": "I am highly proficient in Python, SQL (PostgreSQL), Scikit-Learn, PyTorch, and LangGraph. Recently debugged a memory leak in a Python background worker using memory_profiler and pdb, resolving the leak in a pandas DataFrame loop.",
                "projects": "I built an AI customer support agent using LangGraph and PostgreSQL with pgvector, OpenAI embeddings, and cosine similarity. I validated queries with regex and measured Precision@K."
            }
            return fallbacks.get(topic, "I am a strong candidate with good technical experience.")
        elif scenario == "Improving Candidate":
            if probe_count == 0:
                fallbacks = {
                    "background": "I work with AI.",
                    "education": "I went to KFUPM.",
                    "experience": "I am a programmer.",
                    "skills": "I know Python and ML.",
                    "projects": "I made a chatbot."
                }
                return fallbacks.get(topic, "Yes, I have some basic experience.")
            else:
                fallbacks = {
                    "background": "I have 2 years building computer vision models in Python, focusing on object detection using YOLOv8 on AWS.",
                    "education": "I have a Bachelor's in Software Engineering from KFUPM. Coursework covered database design, software engineering lifecycle, and AI core courses.",
                    "experience": "I have 2 years as a backend developer building APIs with Flask/Django and managing Postgres databases. I helped migrate databases and rewrote SQL using Django's ORM.",
                    "skills": "I am proficient in Python, SQL, Git, Docker, and Scikit-Learn. I perform daily preprocessing and modeling.",
                    "projects": "I built a chatbot using LangChain, Streamlit, and FAISS vector database to answer questions from internal PDFs using RetrievalQA."
                }
                return fallbacks.get(topic, "Here are more details about my experience.")
        else:  # Weak Candidate
            fallbacks = {
                "background": "My background is in Computer Science with a strong interest in AI.",
                "education": "I graduated from KFUPM with a Software Engineering degree.",
                "experience": "I have 3 years of software experience on Python backends.",
                "skills": "I am highly proficient in Python, SQL, and ML.",
                "projects": "I built an agent using LangGraph and PostgreSQL."
            }
            return fallbacks.get(topic, "I don't have much to add to that.")

def run_scenario(scenario_name: str, expected_recommendation: list, thread_id: str):
    print(f"\n======================================================================")
    print(f"🎬 Running Scenario: {scenario_name}")
    print(f"======================================================================")
    
    graph = build_graph()
    
    initial_state = {
        "candidate_id": thread_id,
        "candidate_name": f"{scenario_name} Candidate",
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
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Start graph (runs init and generates first question, then interrupts before evaluation)
    result = graph.invoke(initial_state, config)
    
    # Check that init correctly set up UUID session and program IDs
    assert result["session_id"] != "", "session_id was not initialized"
    assert result["candidate_id"] != thread_id, "candidate_id was not converted to UUID format"
    
    # Loop to simulate the interview turn-by-turn
    while not result["is_complete"]:
        current_topic = result["current_topic"]
        probe_count = result["probe_count"]
        question = result["last_question"]
        
        # Generate answer using LLM candidate simulator
        answer = generate_mock_candidate_answer(scenario_name, current_topic, question, probe_count)
            
        print(f"\n[Simulator] Turn {result['turn_count'] + 1} | Topic: {current_topic} | Probe Count: {probe_count}")
        print(f"[Agent Question]: {question}")
        print(f"[Candidate Answer]: {answer}")
        
        # Resume the graph by supplying the answer to the checkpoint and calling invoke(None)
        graph.update_state(config, {"last_answer": answer})
        result = graph.invoke(None, config)
        
        # Output evaluation details from the nodes
        print(f"[Evaluation Score]: {result.get('scores', {}).get(current_topic)}")
        print(f"[Evaluation Feedback]: {result.get('feedback')}")
        print(f"[Extracted Skills]: {result.get('extracted_skills')}")
        print(f"[Needs Probe?]: {result.get('needs_probe')} | [Probe Count]: {result.get('probe_count')}")
        
    # Assertions to verify the final complete state
    assert result["is_complete"] is True, "Graph failed to complete"
    report = result["final_report"]
    assert report is not None, "Report was not generated"
    assert report["candidate_id"] == result["candidate_id"], "Candidate UUID in report mismatch"
    assert report["session_id"] == result["session_id"], "Session UUID in report mismatch"
    
    print(f"\n----------------------------------------------------------------------")
    print(f"📊 Final Evaluation Summary for {scenario_name}:")
    print(f"  Overall Score: {report['overall_score']}/5.0")
    print(f"  Recommendation: {report['recommendation'].upper()}")
    print(f"  Summary: {report['summary']}")
    print(f"  Strengths: {report['strengths']}")
    print(f"  Weaknesses: {report['weaknesses']}")
    print(f"  Decision Notes: {report['decision_notes']}")
    print(f"----------------------------------------------------------------------")
    
    assert report["recommendation"] in expected_recommendation, \
        f"Expected recommendation {expected_recommendation}, but got '{report['recommendation']}'"
    print(f"✅ Scenario '{scenario_name}' passed validation!")

def run_all_scenarios():
    print("🧪 Starting Multi-Agent Scenario Verification Suite...")
    
    # Strong candidate should get 'accept'
    run_scenario("Strong Candidate", ["accept"], "test-strong-001")
    
    # Improving candidate should get 'accept' or 'review' (usually score 3-4 on first or second turn)
    run_scenario("Improving Candidate", ["accept", "review"], "test-improving-001")
    
    # Weak candidate should get 'reject' (scores 1-2 on all topics)
    run_scenario("Weak Candidate", ["reject"], "test-weak-001")
    
    print("\n🎉 All 3 scenarios completed and validated successfully!")

if __name__ == "__main__":
    run_all_scenarios()
