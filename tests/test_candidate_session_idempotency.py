import uuid
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "agent"))

import tools


class FakeQuery:
    def __init__(self, table_name, client):
        self.table_name = table_name
        self.client = client
        self.operation = None
        self.payload = None
        self.filters = {}

    def select(self, *_args):
        self.operation = "select"
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.operation = "update"
        self.payload = payload
        return self

    def upsert(self, payload, **kwargs):
        self.operation = "upsert"
        self.payload = payload
        self.client.upsert_kwargs.append(kwargs)
        return self

    def eq(self, column, value):
        self.filters[column] = value
        return self

    def limit(self, _value):
        return self

    def execute(self):
        self.client.calls.append((self.table_name, self.operation, self.payload, self.filters))
        if self.table_name == "candidates" and self.operation == "select":
            return type("Result", (), {"data": [{"id": self.client.existing_candidate_id}]})()
        return type("Result", (), {"data": []})()


class FakeClient:
    def __init__(self, existing_candidate_id):
        self.existing_candidate_id = existing_candidate_id
        self.calls = []
        self.upsert_kwargs = []

    def table(self, table_name):
        return FakeQuery(table_name, self)


def test_ensure_candidate_and_session_reuses_existing_candidate_by_email(monkeypatch):
    existing_candidate_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    fake_client = FakeClient(existing_candidate_id)

    monkeypatch.setattr(tools, "_db_client", fake_client)
    monkeypatch.setattr(
        tools,
        "get_program_requirements",
        lambda: {
            "id": "00000000-0000-0000-0000-000000000000",
            "required_topics": ["background", "education"],
        },
    )

    result = tools.ensure_candidate_and_session(
        candidate_id="omar.alqahtani@interview.test",
        candidate_name="Omar Alqahtani",
        session_id=session_id,
    )

    assert result["candidate_id"] == existing_candidate_id
    assert ("candidates", "insert") not in [(table, operation) for table, operation, *_ in fake_client.calls]
    session_inserts = [
        payload
        for table, operation, payload, _filters in fake_client.calls
        if table == "interview_sessions" and operation == "insert"
    ]
    assert session_inserts[0]["candidate_id"] == existing_candidate_id
    assert fake_client.upsert_kwargs == [{"on_conflict": "candidate_id"}]
