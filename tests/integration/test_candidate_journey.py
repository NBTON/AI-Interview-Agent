import io
import os
from types import SimpleNamespace

import pandas as pd
from fastapi.testclient import TestClient


class FakeGraph:
    def __init__(self):
        self.states = {}

    def invoke(self, input_value, config):
        session_id = config["configurable"]["thread_id"]
        if input_value:
            self.states[session_id] = {
                **input_value,
                "last_question": '{"type":"open_ended","text":"Tell me about your background."}',
                "current_topic": "background",
                "turn_count": 0,
                "scores": {"summary_metrics": {"overall_score": 0.0}, "topic_scores": {}},
                "is_complete": False,
            }
            return self.states[session_id]

        state = self.states[session_id]
        turn = state["turn_count"] + 1
        topics = ["background", "skills", "projects"]
        topic = topics[min(turn, len(topics) - 1)]
        is_complete = turn >= 3
        state.update(
            {
                "turn_count": turn,
                "current_topic": topic,
                "last_answer": "",
                "last_question": None
                if is_complete
                else '{"type":"open_ended","text":"Next question for %s."}' % topic,
                "feedback": "Recorded.",
                "scores": {
                    "summary_metrics": {
                        "overall_score": 4.0,
                        "total_turns_taken": turn,
                        "tier_assigned": "advanced_track",
                    },
                    "topic_scores": {
                        "background": {
                            "final_topic_score": 4.0,
                            "turn_scores": [{"turn_number": turn, "score": 4.0}],
                        }
                    },
                },
                "is_complete": is_complete,
                "final_report": {
                    "session_id": session_id,
                    "candidate_id": "candidate-1",
                    "overall_score": 4.0,
                    "recommendation": "accept",
                }
                if is_complete
                else None,
            }
        )
        return state

    def get_state(self, config):
        return SimpleNamespace(values=self.states.get(config["configurable"]["thread_id"], {}))

    def update_state(self, config, values, as_node=None):
        self.states[config["configurable"]["thread_id"]].update(values)


def test_full_candidate_journey_with_email_verification(monkeypatch):
    os.environ["CANDIDATE_TOKEN_SECRET"] = "test-secret"

    from backend.main import app
    from backend.routes import candidates, interview

    client = TestClient(app)
    fake_graph = FakeGraph()
    known_code = "123456"

    monkeypatch.setattr(
        candidates,
        "load_candidates_data",
        lambda: pd.DataFrame(
            [{"name": "Omar Candidate", "email": "omar@example.com", "status": "Pending", "score": 0}]
        ),
    )
    monkeypatch.setattr(
        candidates,
        "_issue_verification_code",
        lambda email: candidates._verification_codes.update(
            {
                email: {
                    "code_hash": candidates._hash_code(email, known_code),
                    "expires_at": candidates.datetime.now(candidates.timezone.utc)
                    + candidates.timedelta(minutes=10),
                }
            }
        ),
    )
    monkeypatch.setattr(interview, "_get_graph", lambda: fake_graph)
    monkeypatch.setattr(candidates, "update_candidate_score", lambda candidate_name, score: {"success": True})
    monkeypatch.setattr(interview, "_fetch_candidate", lambda candidate_id: {"email": "omar@example.com", "full_name": "Omar Candidate"})
    monkeypatch.setattr(
        interview,
        "_fetch_session",
        lambda session_id: {
            "id": session_id,
            "candidate_id": "candidate-1",
            "status": "completed" if fake_graph.states.get(session_id, {}).get("is_complete") else "in_progress",
            "turn_count": fake_graph.states.get(session_id, {}).get("turn_count", 0),
            "scores": fake_graph.states.get(session_id, {}).get("scores", {}),
        },
    )
    monkeypatch.setattr(interview, "_question_limit", lambda: 3)

    verify = client.post("/api/candidates/verify", json={"email": "omar@example.com"})
    assert verify.status_code == 200
    assert verify.json()["verification_required"] is True

    code_response = client.post("/api/candidates/verify-code", json={"email": "omar@example.com", "code": known_code})
    assert code_response.status_code == 200
    token = code_response.json()["candidate_token"]

    start = client.post(
        "/api/interview/start",
        json={"candidate_name": "Omar Candidate", "candidate_email": "omar@example.com", "candidate_token": token},
    )
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    first_answer = client.post("/api/interview/answer", json={"session_id": session_id, "answer": "A detailed answer."})
    assert first_answer.status_code == 401

    completed = False
    for answer in ["I have Python experience.", "I built a LangGraph agent.", "Here is a final project answer."]:
        response = client.post(
            "/api/interview/answer",
            json={
                "session_id": session_id,
                "answer": answer,
                "candidate_email": "omar@example.com",
                "candidate_token": token,
            },
        )
        assert response.status_code == 200
        payload = response.json()
        completed = payload["is_complete"]
        if not completed:
            assert payload["next_question"]
            assert payload["question_number"] >= 2

    assert completed is True
    assert payload["final_score"] == 80.0


def test_recruiter_excel_import_reports_row_errors(monkeypatch):
    from backend.main import app
    from backend.routes import candidates

    saved = {}
    monkeypatch.setattr(candidates, "_db_client", None)
    monkeypatch.setattr(candidates, "EXCEL_PATH", candidates.PROJECT_ROOT / "tmp" / "test-import-candidates.xlsx")
    monkeypatch.setattr(candidates, "save_candidates_data", lambda df: saved.setdefault("df", df.copy()))

    workbook = io.BytesIO()
    pd.DataFrame(
        [
            {"name": "Valid Student", "email": "valid@example.com", "program": "Agentic AI", "session": "S1"},
            {"name": "", "email": "missing-name@example.com", "program": "Agentic AI"},
            {"name": "Bad Email", "email": "not-an-email", "program": "Agentic AI"},
        ]
    ).to_excel(workbook, index=False)
    workbook.seek(0)

    client = TestClient(app)
    response = client.post(
        "/api/candidates/import-excel",
        files={"file": ("candidates.xlsx", workbook.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["inserted"] == 1
    assert payload["skipped"] == 2
    assert len(payload["errors"]) == 2
    assert saved["df"].iloc[0]["email"] == "valid@example.com"


def test_scoring_payloads_are_predictable_for_answer_types():
    from agent import tools

    tools._llm = None
    evaluate_answer = tools.evaluate_answer

    mcq = evaluate_answer(
        '{"type":"multiple_choice","text":"Which option is Python?","options":["Python","HTML"],"correct_answer":"Python"}',
        "Python",
        {},
    )
    empty = evaluate_answer("Tell me about your background.", "", {})
    code = evaluate_answer(
        '{"type":"coding","text":"Return 2","solution_test":"assert answer() == 2"}',
        "def answer():\n    return 2",
        {},
    )
    malformed = evaluate_answer("{not-json", "", {})

    assert mcq["score"] == 5
    assert empty["score"] == 1
    assert code["score"] >= 4
    assert "score" in malformed and "feedback" in malformed
