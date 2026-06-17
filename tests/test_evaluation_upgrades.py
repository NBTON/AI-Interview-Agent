import os
import sys
from pathlib import Path

# Ensure the agent directory is in Python path for absolute imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
AGENT_DIR = SRC_DIR / "agent"

if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from tools import evaluate_objective_answer, execute_and_test_code, evaluate_answer

def test_deterministic_mcq():
    print("[Test] Testing deterministic MCQ evaluation...")
    
    question_obj = {
        "type": "multiple_choice",
        "text": "What is the capital of France?",
        "options": ["A) London", "B) Berlin", "C) Paris", "D) Madrid"],
        "correct_answer": "C) Paris"
    }
    
    # Positive case: exact match
    res = evaluate_objective_answer(question_obj, "C) Paris")
    assert res["score"] == 5
    assert "Paris" in res["feedback"]
    
    # Positive case: letter index match
    res = evaluate_objective_answer(question_obj, "C")
    assert res["score"] == 5
    
    # Positive case: lower case substring match
    res = evaluate_objective_answer(question_obj, "paris")
    assert res["score"] == 5
    
    # Negative case: incorrect answer
    res = evaluate_objective_answer(question_obj, "A) London")
    assert res["score"] == 1
    assert "London" in res["feedback"]

def test_deterministic_true_false():
    print("[Test] Testing deterministic True/False evaluation...")
    
    question_obj = {
        "type": "true_false",
        "text": "Is Python a compiled language?",
        "options": ["True", "False"],
        "correct_answer": "False"
    }
    
    # Positive case
    res = evaluate_objective_answer(question_obj, "False")
    assert res["score"] == 5
    
    # Negative case
    res = evaluate_objective_answer(question_obj, "True")
    assert res["score"] == 1

def test_code_execution_success():
    print("[Test] Testing code execution success...")
    
    code = "def add(a, b):\n    return a + b"
    test_script = "add(2, 3) == 5"
    
    res = execute_and_test_code(code, test_script)
    assert res["success"] is True
    assert res["score"] == 5
    assert "passed all tests" in res["feedback"]

def test_code_execution_assertion_failure():
    print("[Test] Testing code execution assertion failure...")
    
    code = "def add(a, b):\n    return a - b" # logical error
    test_script = "add(2, 3) == 5"
    
    res = execute_and_test_code(code, test_script)
    assert res["success"] is False
    assert res["score"] == 3
    assert "failed logical assertions" in res["feedback"]

def test_code_execution_syntax_error():
    print("[Test] Testing code execution syntax error...")
    
    code = "def add(a, b)\n    return a + b" # missing colon
    test_script = "add(2, 3) == 5"
    
    res = execute_and_test_code(code, test_script)
    assert res["success"] is False
    assert res["score"] == 2
    assert "SyntaxError" in res["feedback"] or "failed due to" in res["feedback"]

def test_evaluate_answer_integration():
    print("[Test] Testing evaluate_answer integration for coding and MCQs...")
    
    # MCQ
    mcq_question = '{"type": "multiple_choice", "text": "Capital of France?", "correct_answer": "C) Paris"}'
    res = evaluate_answer(mcq_question, "c", {})
    assert res["score"] == 5
    
    # Coding passing
    coding_question = '{"type": "coding", "text": "Add function", "solution_test": "add(1, 2) == 3"}'
    res = evaluate_answer(coding_question, "def add(a, b):\n    return a + b", {})
    assert res["score"] == 5
    assert "passed all tests" in res["feedback"]

if __name__ == "__main__":
    test_deterministic_mcq()
    test_deterministic_true_false()
    test_code_execution_success()
    test_code_execution_assertion_failure()
    test_code_execution_syntax_error()
    test_evaluate_answer_integration()
    print("All custom tests passed successfully!")
