"""
Tests for citation validation: DB resolution, stripping, enrichment, coverage.
Phase 1: Fortify — zero hallucinated citations pass through.
"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import src.orchestration.nodes.verifier as verifier_module
from src.orchestration.state import NRGState
from src.orchestration.nodes.verifier import verifier_node


def test_nrg_state_carries_answer_engine_v1_fields():
    state = NRGState(
        user_query="Who is best in hydrogen catalysis?",
        assumptions=["Interpreted best as recent evidence-backed composite score."],
        caveats=["Citation data is incomplete for 2026."],
        follow_up_suggestions=["Change time range"],
        freshness={"database_snapshot": "2026-04-29"},
    )

    data = state.to_dict()

    assert data["assumptions"]
    assert data["caveats"]
    assert data["follow_up_suggestions"] == ["Change time range"]
    assert data["freshness"]["database_snapshot"] == "2026-04-29"


def test_verifier_marks_unsupported_numeric_answer_low_confidence():
    state = {
        "user_query": "Top grants",
        "synthesized_response": "DST disbursed 999 crore [cite:structured:0].",
        "sql_results": [{"agency": "DST", "total": 10}],
        "citations": [{"pub_id": "structured", "chunk_id": "0"}],
        "user_tier": 1,
    }

    result = verifier_node(state)

    assert result["answer_confidence"] in {"low", "needs_clarification"}
    assert result["caveats"]
    assert result["unsupported_claims"]


class FakeVerifierClient:
    model = "fake-verifier"

    def __init__(self, ok=True):
        self.ok = ok

    def generate(self, system_prompt, user_prompt, conversation_history):
        return json.dumps({"ok": self.ok, "unsupported_claims": [] if self.ok else ["bad claim"]})


class FakeDB:
    def __init__(self, valid_pub_ids=None):
        self.valid_pub_ids = valid_pub_ids or {"PUB_001", "PUB_002", "PUB_003"}
        self.executed: list[str] = []

    def execute(self, query, *args, **kwargs):
        self.executed.append(query)
        class Row:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                for k, v in zip(["title", "authors", "year", "venue", "doi", "citations", "abstract", "research_area"], self._data, strict=False):
                    if k == key:
                        return v
                raise KeyError(key)
        if "SELECT" in query and "publication_id" in query:
            pub_id = (args[0] if args else kwargs.get("parameters", (None,)))[0]
            if pub_id in self.valid_pub_ids:
                return MagicMock(fetchone=MagicMock(return_value=Row(["Test Paper", "John Doe, Jane Smith", 2023, "Nature", "10.1234/test", 42, "Abstract text", "AI"])))
            return MagicMock(fetchone=MagicMock(return_value=None))
        return MagicMock(fetchone=MagicMock(return_value=None), rowcount=0)

    def commit(self):
        pass

    def close(self):
        pass


@pytest.fixture
def mock_db(monkeypatch):
    fake = FakeDB()
    monkeypatch.setattr(verifier_module, "_get_db_connection", lambda: fake)
    return fake


class TestCitationValidation:
    """Phase 1: Every [cite:pub_id:chunk_id] must resolve to a real DB record."""

    def test_valid_pub_id_passes_validation(self, mock_db, monkeypatch):
        """PUB_001 exists in DB — citation is valid, citation_validity = 1.0."""
        monkeypatch.setattr(verifier_module, "get_llm_client", lambda: None)

        result = verifier_module.verifier_node({
            "synthesized_response": "Robotics research is active [cite:PUB_001:0].",
            "retrieved_chunks": [],
            "sql_results": [],
            "verification_retries": 0,
        })

        assert result["citation_validity"] == 1.0
        assert result["verification_status"] == "ok"
        assert len(result["invalid_citations"]) == 0

    def test_hallucinated_pub_id_fails_validation(self, mock_db, monkeypatch):
        """PUB_HALLUCINATED does NOT exist in DB — citation is stripped, logged."""
        monkeypatch.setattr(verifier_module, "get_llm_client", lambda: None)

        result = verifier_module.verifier_node({
            "synthesized_response": "Robotics research is active [cite:PUB_HALLUCINATED:0].",
            "retrieved_chunks": [],
            "sql_results": [],
            "verification_retries": 0,
        })

        assert result["citation_validity"] == 0.0
        assert "[cite:PUB_HALLUCINATED:0]" not in result["synthesized_response"]
        assert len(result["invalid_citations"]) == 1
        assert result["invalid_citations"][0]["pub_id"] == "PUB_HALLUCINATED"

    def test_mixed_valid_and_invalid_citations(self, mock_db, monkeypatch):
        """One valid, one hallucinated — citation_validity = 0.5, invalid stripped."""
        monkeypatch.setattr(verifier_module, "get_llm_client", lambda: None)

        result = verifier_module.verifier_node({
            "synthesized_response": "AI research [cite:PUB_001:0] and robotics [cite:PUB_FAKE:0].",
            "retrieved_chunks": [],
            "sql_results": [],
            "verification_retries": 0,
        })

        assert result["citation_validity"] == 0.5
        assert "[cite:PUB_001:0]" in result["synthesized_response"]
        assert "[cite:PUB_FAKE:0]" not in result["synthesized_response"]
        assert result["invalid_citations"][0]["pub_id"] == "PUB_FAKE"

    def test_structured_citation_always_valid(self, mock_db, monkeypatch):
        """Structured citations [cite:structured:0] don't need DB validation."""
        monkeypatch.setattr(verifier_module, "get_llm_client", lambda: None)

        result = verifier_module.verifier_node({
            "synthesized_response": "There are 42 researchers [cite:structured:0].",
            "retrieved_chunks": [],
            "sql_results": [{"count": 42}],
            "verification_retries": 0,
        })

        assert result["citation_validity"] == 1.0
        assert result["verification_status"] == "ok"

    def test_chunk_id_citation_always_valid(self, mock_db, monkeypatch):
        """Chunk citations [cite:chunk_1:0] don't need DB validation."""
        monkeypatch.setattr(verifier_module, "get_llm_client", lambda: None)

        result = verifier_module.verifier_node({
            "synthesized_response": "Document analysis [cite:chunk_abc:0].",
            "retrieved_chunks": [{"chunk_id": "chunk_abc", "content": "Some text"}],
            "sql_results": [],
            "verification_retries": 0,
        })

        assert result["citation_validity"] == 1.0
        assert result["verification_status"] == "ok"

    def test_malformed_citation_type_stripped(self, mock_db, monkeypatch):
        """Citation with unknown type prefix is stripped and logged."""
        monkeypatch.setattr(verifier_module, "get_llm_client", lambda: None)

        result = verifier_module.verifier_node({
            "synthesized_response": "Claim [cite:FAKE_ID_123:0].",
            "retrieved_chunks": [],
            "sql_results": [],
            "verification_retries": 0,
        })

        assert "[cite:FAKE_ID_123:0]" not in result["synthesized_response"]
        assert len(result["invalid_citations"]) >= 1

    def test_duplicate_citations_deduplicated(self, mock_db, monkeypatch):
        """Same citation appearing twice is counted once and deduplicated."""
        monkeypatch.setattr(verifier_module, "get_llm_client", lambda: None)

        result = verifier_module.verifier_node({
            "synthesized_response": "AI research [cite:PUB_001:0] and more AI [cite:PUB_001:0].",
            "retrieved_chunks": [],
            "sql_results": [],
            "verification_retries": 0,
        })

        assert result["citation_validity"] == 1.0
        assert result["verification_status"] == "ok"
        cited_responses = result["synthesized_response"].count("[cite:PUB_001:0]")
        assert cited_responses == 1, "Duplicate citation should be removed"

    def test_duplicate_structured_citations_with_sql_rows_are_verified(self, mock_db, monkeypatch):
        """Repeated [cite:structured:0] tokens from SQL fast paths should dedupe, not force retry."""
        monkeypatch.setattr(verifier_module, "get_llm_client", lambda: None)

        result = verifier_module.verifier_node({
            "synthesized_response": (
                "Found 3 records [cite:structured:0]. "
                "IIT Delhi capital_expense_crore is 412.4 [cite:structured:0]. "
                "IIT Kanpur capital_expense_crore is 351.2 [cite:structured:0]."
            ),
            "sql_results": [
                {"institute": "IIT Delhi", "capital_expense_crore": 412.4},
                {"institute": "IIT Kharagpur", "capital_expense_crore": 388.7},
                {"institute": "IIT Kanpur", "capital_expense_crore": 351.2},
            ],
            "verification_retries": 0,
        })

        assert result["citation_validity"] == 1.0
        assert result["verification_status"] == "ok"
        assert result["synthesized_response"].count("[cite:structured:0]") == 1

    def test_enriched_citations_contain_metadata(self, mock_db, monkeypatch):
        """Valid publication citations are enriched with title, authors, year, DOI."""
        monkeypatch.setattr(verifier_module, "get_llm_client", lambda: None)

        result = verifier_module.verifier_node({
            "synthesized_response": "AI research [cite:PUB_001:0].",
            "retrieved_chunks": [],
            "sql_results": [],
            "verification_retries": 0,
        })

        assert len(result["citations"]) == 1
        cite = result["citations"][0]
        assert cite.get("enriched") is True
        assert cite.get("title") == "Test Paper"
        assert cite.get("authors") == ["John Doe", "Jane Smith"]
        assert cite.get("year") == 2023

    def test_invalid_citation_logged(self, monkeypatch, tmp_path):
        """Invalid citations are appended to invalid_citations.jsonl."""
        log_path = tmp_path / "invalid_citations.jsonl"
        monkeypatch.setattr(verifier_module, "_INVALID_CITATION_LOG_PATH", log_path)
        monkeypatch.setattr(verifier_module, "_get_db_connection", lambda: FakeDB())

        verifier_module.verifier_node({
            "synthesized_response": "Claim [cite:PUB_FAKE:0].",
            "retrieved_chunks": [],
            "sql_results": [],
            "verification_retries": 0,
        })

        if log_path.exists():
            lines = log_path.read_text().strip().split("\n")
            assert len(lines) >= 1
            entry = json.loads(lines[-1])
            assert entry["event"] == "invalid_citation"
            assert entry["pub_id"] == "PUB_FAKE"


class TestCitationStripping:
    """Invalid citations are stripped from synthesized_response text."""

    def test_strip_function_removes_invalid_only(self):
        """_strip_invalid_citations removes only invalid tokens."""
        valid_ids = {"PUB_001:0", "PUB_002:0"}
        response = "AI [cite:PUB_001:0] and ML [cite:PUB_999:0]. Also [cite:PUB_002:0]."
        cleaned, stripped = verifier_module._strip_invalid_citation_tokens(response, valid_ids)

        assert "[cite:PUB_001:0]" in cleaned
        assert "[cite:PUB_002:0]" in cleaned
        assert "[cite:PUB_999:0]" not in cleaned
        assert len(stripped) == 1
        assert stripped[0]["pub_id"] == "PUB_999"

    def test_stripped_response_preserves_text_around(self):
        """Stripping doesn't break surrounding text."""
        valid_ids = {"PUB_001:0"}
        response = "Before [cite:PUB_001:0] after and also [cite:FAKE:0] done."
        cleaned, stripped = verifier_module._strip_invalid_citation_tokens(response, valid_ids)

        assert "Before" in cleaned
        assert "after" in cleaned
        assert "FAKE" not in cleaned or stripped  # the cite token removed


class TestCitationCoverage:
    """Phase 2: Citation coverage metric — % of sentences with at least one citation."""

    def test_coverage_calculation(self):
        """_calculate_citation_coverage returns fraction of cited sentences."""
        response = "Sentence one [cite:PUB_001:0]. Sentence two [cite:PUB_002:0]. Sentence three."
        coverage = verifier_module._calculate_citation_coverage(response, [{"pub_id": "PUB_001"}, {"pub_id": "PUB_002"}])
        assert coverage == pytest.approx(2 / 3, rel=0.01)


class TestCitationDeduplication:
    """Phase 2: Same source cited multiple times consolidates into one reference."""

    def test_deduplicate_removes_duplicates(self):
        """_deduplicate_citations keeps first occurrence only."""
        citations = [
            {"id": "PUB_001:0", "pub_id": "PUB_001", "chunk_id": "0"},
            {"id": "PUB_002:0", "pub_id": "PUB_002", "chunk_id": "0"},
            {"id": "PUB_001:0", "pub_id": "PUB_001", "chunk_id": "0"},
        ]
        deduped = verifier_module._deduplicate_citations(citations)
        assert len(deduped) == 2
        assert deduped[0]["pub_id"] == "PUB_001"
        assert deduped[1]["pub_id"] == "PUB_002"
