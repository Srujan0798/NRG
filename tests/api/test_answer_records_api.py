from pathlib import Path

from src.services.answer_records import AnswerRecordStore


def test_answer_record_store_round_trip(tmp_path: Path):
    store = AnswerRecordStore(tmp_path / "answers.sqlite")
    store.save(
        user_id="user-1",
        session_id="session-1",
        payload={
            "answer_id": "answer-1",
            "query_id": "query-1",
            "question": "Top funding agencies",
            "final_answer": "DST leads [1].",
            "tier": 1,
            "audit_event_id": "audit-1",
            "confidence": {"level": "high", "reason": "Verified."},
            "citations": [{"id": "1"}],
        },
    )

    rows = store.list_for_session(user_id="user-1", session_id="session-1")

    assert len(rows) == 1
    assert rows[0]["answer_id"] == "answer-1"
    assert rows[0]["payload"]["final_answer"] == "DST leads [1]."
