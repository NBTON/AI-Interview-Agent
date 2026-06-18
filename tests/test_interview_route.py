from types import SimpleNamespace


def test_submit_answer_resumes_from_interviewer_node(monkeypatch):
    from backend.routes import interview
    from backend.security import create_candidate_token

    class FakeGraph:
        def __init__(self):
            self.updated_as_node = None

        def get_state(self, config):
            return SimpleNamespace(
                values={
                    "last_question": "First question?",
                    "current_topic": "background",
                    "turn_count": 0,
                }
            )

        def update_state(self, config, values, as_node=None):
            self.updated_as_node = as_node
            assert values == {"last_answer": "My answer"}

        def invoke(self, input_value, config):
            return {
                "last_question": "Second question?",
                "current_topic": "skills",
                "turn_count": 1,
                "scores": {
                    "summary_metrics": {"overall_score": 3.0, "total_turns_taken": 1, "tier_assigned": ""},
                    "topic_scores": {
                        "background": {
                            "final_topic_score": 4.0,
                            "turn_scores": [{"turn_number": 1, "score": 4.0}],
                        }
                    },
                },
                "feedback": "Clear answer.",
                "is_complete": False,
            }

    fake_graph = FakeGraph()
    monkeypatch.setattr(
        interview,
        "_fetch_session",
        lambda session_id: {"id": session_id, "candidate_id": "candidate-1", "turn_count": 1},
    )
    monkeypatch.setattr(interview, "_fetch_candidate", lambda candidate_id: {"email": "candidate@example.com"})
    monkeypatch.setattr(interview, "_get_graph", lambda: fake_graph)
    monkeypatch.setattr(interview, "_question_limit", lambda: 10)

    response = interview.submit_answer(
        interview.SubmitAnswerRequest(
            session_id="session-1",
            answer="My answer",
            candidate_email="candidate@example.com",
            candidate_token=create_candidate_token("candidate@example.com"),
        )
    )

    assert fake_graph.updated_as_node == "interviewer"
    assert response.next_question == "Second question?"
    assert response.current_topic == "skills"
    assert response.question_number == 2
    assert response.is_complete is False
