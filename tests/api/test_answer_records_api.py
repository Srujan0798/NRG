from pathlib import Path

from src.services.answer_records import AnswerRecordStore, _default_answer_records_path


def test_answer_record_default_path_prefers_runtime_dir(monkeypatch, tmp_path: Path):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    monkeypatch.delenv("NRG_ANSWER_RECORDS_DB", raising=False)
    monkeypatch.setenv("NRG_RUNTIME_DIR", str(runtime_dir))

    assert _default_answer_records_path() == runtime_dir / "answer_records.sqlite"


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
