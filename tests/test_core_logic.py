# tests/test_core_logic.py
import pytest
import json
import uuid
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "agent"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tools import (
    generate_question,
    generate_probe_question,
    evaluate_answer,
    generate_report,
    record_turn_and_update_profile,
    ensure_candidate_and_session,
    calculate_score,
    identify_missing_info,
    get_program_requirements,
    empty_score_payload,
    append_turn_score,
    normalize_scores_payload,
    _db_client
)


class TestBootcampAdmissionInterview:
    """Tests for bootcamp admission interview flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self, db_client, test_session, rubric, required_topics):
        """Setup using fixtures from conftest.py"""
        self.db_client = db_client
        self.rubric = rubric
        self.required_topics = required_topics
        
        if test_session:
            self.db_candidate_id = test_session["candidate_id"]
            self.db_session_id = test_session["session_id"]
        else:
            self.db_candidate_id = str(uuid.uuid4())
            self.db_session_id = str(uuid.uuid4())

    # ============================================================
    # 1. Bootcamp Application Questions
    # ============================================================

    def test_generate_question_returns_valid_json(self):
        """Test bootcamp admission question generation"""
        context = {
            "skills_to_assess": ["Python", "ML basics", "problem solving"],
            "rubric": {"excellent": "Detailed", "good": "Good", "weak": "Weak"}
        }
        result = generate_question("background", context, [], None)
        parsed = json.loads(result)
        
        assert "type" in parsed
        assert "text" in parsed
        assert parsed["type"] in ["open_ended", "multiple_choice", "true_false", "coding"]
        assert len(parsed["text"]) > 10

    def test_generate_question_fallback(self):
        """Test question generation fallback when LLM fails"""
        context = {"skills_to_assess": ["Python"], "rubric": {}}
        result = generate_question("background", context, [], None)
        parsed = json.loads(result)
        
        assert parsed["type"] in ["open_ended", "multiple_choice", "true_false"]
        assert len(parsed["text"]) > 10

    def test_generate_question_for_all_bootcamp_topics(self):
        """Test question generation for all bootcamp topics"""
        context = {"skills_to_assess": ["Python", "ML basics"], "rubric": {}}
        bootcamp_topics = ["background", "education", "experience", "skills", "projects"]
        
        for topic in bootcamp_topics:
            result = generate_question(topic, context, [], None)
            parsed = json.loads(result)
            assert "type" in parsed
            assert "text" in parsed
            assert len(parsed["text"]) > 10

    def test_generate_probe_question_fallback(self):
        """Test follow-up probe question for weak answers"""
        result = generate_probe_question(
            topic="python",
            last_question='{"text": "Tell me about your Python experience"}',
            last_answer="I know some Python"
        )
        parsed = json.loads(result)
        assert parsed["type"] == "open_ended"
        assert len(parsed["text"]) > 10

    # ============================================================
    # 2. Bootcamp Application Evaluation
    # ============================================================

    def test_evaluate_answer_empty(self):
        """Test empty applicant answer"""
        result = evaluate_answer(
            "Tell me about your Python experience",
            "",
            self.rubric
        )
        assert result["score"] == 1
        feedback = result["feedback"].lower()
        assert "no response" in feedback or "did not provide" in feedback

    def test_evaluate_answer_brief(self):
        """Test brief applicant answer - should trigger probe"""
        result = evaluate_answer(
            "Tell me about your Python experience",
            "I know Python",
            self.rubric
        )
        assert result["score"] <= 3
        if result.get("needs_probe") is not None:
            assert result["needs_probe"] is True or result["score"] <= 2

    def test_evaluate_answer_detailed(self):
        """Test detailed applicant answer - should score high"""
        result = evaluate_answer(
            "Tell me about your Python experience",
            "I have 3+ years of Python experience with Django, FastAPI, and data analysis. I've built several projects including a chatbot and a data visualization dashboard.",
            self.rubric
        )
        assert result["score"] >= 3

    def test_evaluate_answer_multiple_choice(self):
        """Test MCQ evaluation for bootcamp screening"""
        question = json.dumps({
            "type": "multiple_choice",
            "text": "Which of these is a Python web framework?",
            "options": ["Django", "React", "Angular", "Vue"],
            "correct_answer": "Django"
        })
        result = evaluate_answer(question, "Django", {})
        assert result["score"] == 5

    # ============================================================
    # 3. Bootcamp Scoring
    # ============================================================

    def test_calculate_score_with_nested_payload(self):
        """Test overall bootcamp score calculation"""
        scores = empty_score_payload()
        scores["topic_scores"]["background"] = {"final_topic_score": 4}
        scores["topic_scores"]["experience"] = {"final_topic_score": 3}
        
        result = calculate_score(scores)
        assert result == 3.5

    def test_calculate_score_empty(self):
        """Test score calculation with no scores"""
        assert calculate_score({}) == 0.0
        assert calculate_score({"topic_scores": {}}) == 0.0

    def test_identify_missing_topics(self):
        """Test identifying missing bootcamp topics"""
        required = ["background", "education", "experience", "skills", "projects"]
        covered = ["background", "education"]
        
        missing = identify_missing_info(covered, required)
        assert missing == ["experience", "skills", "projects"]

    def test_append_turn_score(self):
        """Test appending a turn score during interview"""
        scores = empty_score_payload()
        eval_result = {
            "score": 4,
            "feedback": "Good understanding of Python fundamentals",
            "extracted_skills": ["Python"],
            "extracted_info": {}
        }
        
        updated = append_turn_score(scores, "skills", 1, eval_result)
        
        assert "skills" in updated["topic_scores"]
        assert updated["topic_scores"]["skills"]["final_topic_score"] == 4.0
        assert len(updated["topic_scores"]["skills"]["turn_scores"]) == 1

    def test_empty_score_payload_structure(self):
        """Test empty score payload structure"""
        payload = empty_score_payload()
        assert "summary_metrics" in payload
        assert "topic_scores" in payload
        assert payload["summary_metrics"]["overall_score"] == 0.0
        assert payload["topic_scores"] == {}

    # ============================================================
    # 4. Bootcamp Admission Report
    # ============================================================

    def test_generate_report_structure(self):
        """Test bootcamp admission report structure"""
        scores = empty_score_payload()
        scores["topic_scores"]["background"] = {"final_topic_score": 4}
        scores["topic_scores"]["experience"] = {"final_topic_score": 3}
        scores["topic_scores"]["skills"] = {"final_topic_score": 5}
        
        report = generate_report(
            session_id=str(uuid.uuid4()),
            candidate_id=str(uuid.uuid4()),
            scores=scores,
            candidate_name="Bootcamp Applicant"
        )
        
        assert "summary" in report
        assert "recommendation" in report
        # Bootcamp admission decisions
        assert report["recommendation"] in ["accept", "review", "reject"]
        assert "strengths" in report
        assert "weaknesses" in report
        assert "overall_score" in report

    def test_generate_report_for_weak_applicant(self):
        """Test admission report for weak bootcamp applicant"""
        scores = empty_score_payload()
        scores["topic_scores"]["background"] = {"final_topic_score": 1}
        scores["topic_scores"]["experience"] = {"final_topic_score": 1}
        scores["topic_scores"]["skills"] = {"final_topic_score": 1}
        
        report = generate_report(
            session_id=str(uuid.uuid4()),
            candidate_id=str(uuid.uuid4()),
            scores=scores,
            candidate_name="Weak Applicant"
        )
        
        # Weak applicants should be rejected
        assert report["recommendation"] == "reject"
        assert report["overall_score"] <= 2.0

    # ============================================================
    # 5. Bootcamp Applicant Session
    # ============================================================

    def test_ensure_applicant_and_session(self):
        """Test bootcamp applicant session creation in DB"""
        if not self.db_client:
            pytest.skip("No database connection available")
        
        test_id = f"bootcamp_applicant_{uuid.uuid4().hex[:8]}"
        
        result = ensure_candidate_and_session(
            candidate_id=test_id,
            candidate_name="Bootcamp Applicant",
            program_id=None
        )
        
        assert "candidate_id" in result
        assert "session_id" in result
        assert "program_id" in result
        
        # Verify applicant exists in DB
        candidate_uuid = result["candidate_id"]
        candidate_result = self.db_client.table("candidates").select("*").eq("id", candidate_uuid).execute()
        assert len(candidate_result.data) == 1
        assert candidate_result.data[0]["id"] == candidate_uuid
        
        # Verify session exists in DB
        session_uuid = result["session_id"]
        session_result = self.db_client.table("interview_sessions").select("*").eq("id", session_uuid).execute()
        assert len(session_result.data) == 1
        assert session_result.data[0]["id"] == session_uuid

    # ============================================================
    # 6. Bootcamp Interview Turn Recording
    # ============================================================

    def test_record_interview_turn(self):
        """Test recording a bootcamp interview turn in DB"""
        if not self.db_client:
            pytest.skip("No database connection available")
        
        test_id = f"bootcamp_interview_{uuid.uuid4().hex[:8]}"
        db_result = ensure_candidate_and_session(
            candidate_id=test_id,
            candidate_name="Bootcamp Applicant",
            program_id=None
        )
        
        candidate_id = db_result["candidate_id"]
        session_id = db_result["session_id"]
        
        eval_result = {
            "score": 4,
            "feedback": "Good bootcamp applicant",
            "needs_probe": False,
            "extracted_skills": ["Python", "Problem Solving"],
            "extracted_info": {"years": 3}
        }
        
        result, scores = record_turn_and_update_profile(
            session_id=session_id,
            candidate_id=candidate_id,
            turn_number=1,
            topic="background",
            question="Tell me about your programming background",
            answer="I have 3 years of Python experience building web apps",
            eval_result=eval_result
        )
        
        assert result is True
        assert "topic_scores" in scores
        
        # Verify turn was saved
        turn_result = self.db_client.table("interview_turns").select("*").eq("session_id", session_id).execute()
        assert len(turn_result.data) == 1
        assert turn_result.data[0]["turn_number"] == 1
        assert turn_result.data[0]["score"] == 4

    def test_record_multiple_interview_turns(self):
        """Test recording multiple turns for one bootcamp applicant"""
        if not self.db_client:
            pytest.skip("No database connection available")
        
        test_id = f"bootcamp_full_interview_{uuid.uuid4().hex[:8]}"
        db_result = ensure_candidate_and_session(
            candidate_id=test_id,
            candidate_name="Full Interview Applicant",
            program_id=None
        )
        
        candidate_id = db_result["candidate_id"]
        session_id = db_result["session_id"]
        
        # Turn 1: Background
        result1, _ = record_turn_and_update_profile(
            session_id=session_id,
            candidate_id=candidate_id,
            turn_number=1,
            topic="background",
            question="Tell me about your background",
            answer="I studied Computer Science and have been coding for 4 years",
            eval_result={"score": 4, "feedback": "Good background", "needs_probe": False, "extracted_skills": ["CS"], "extracted_info": {}}
        )
        assert result1 is True
        
        # Turn 2: Skills
        result2, _ = record_turn_and_update_profile(
            session_id=session_id,
            candidate_id=candidate_id,
            turn_number=2,
            topic="skills",
            question="What technologies do you know?",
            answer="Python, Django, SQL, and some ML with Scikit-Learn",
            eval_result={"score": 5, "feedback": "Strong technical skills", "needs_probe": False, "extracted_skills": ["Python", "Django", "SQL"], "extracted_info": {}}
        )
        assert result2 is True
        
        # Verify both turns saved
        turns = self.db_client.table("interview_turns").select("*").eq("session_id", session_id).execute()
        assert len(turns.data) == 2