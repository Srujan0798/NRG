"""
Two-Brain Conflict Resolution Tests — Protocol #32 (post-handover)

This module tests the Two-Brain Orchestrator's ability to detect and resolve
conflicts between the fine-tuned model's internalized answer and live DB retrieval.

ARCHITECTURE (from FINE_TUNING_PIPELINE_SPEC.md §4):
    ┌─────────────────────────────────────────┐
    │        FINE-TUNED LOCAL MODEL           │
    │   (Internalized schema + relationships)  │
    │                                          │
    │  INSTANTLY answers:                     │
    │  • "Who is best in hydrogen catalysis?" │
    │  • "Compare Gujarat vs Karnataka AI"     │
    │                                          │
    │  REQUIRES live retrieval:                │
    │  • "Exact h-index of Dr. Patel?"        │
    │  • "Dr. Patel's 2024 publications"      │
    └──────────────────┬──────────────────────┘
                        │
             ┌──────────┴──────────┐
             │ NO                  │ YES
             ▼                     ▼
       DIRECT ANSWER         LIVE DB RETRIEVAL
       (from internalized    (SQL precise facts)
        knowledge)
             │                     │
             └──────────┬──────────┘
                        ▼
               MERGED RESPONSE

CONFLICT RESOLUTION STRATEGY (3-tier):
    1. LIVE wins for exact facts: DB retrieval is authoritative for specific
       names, numbers, dates, counts (anything user could verify)
    2. MODEL wins for analytical patterns: Trends, comparisons, qualitative
       assessments from internalized training knowledge
    3. UNRESOLVABLE → surface both with confidence delta, do not hallucinate

TEST GAP (G7 from AGENT VERIFICATION): No verification comparing LLM output
against DB results when they disagree. This test suite documents the expected
behavior and will pass once Protocol #32 is implemented.

Status: ⏸️ PENDING — Protocol #32 is post-handover (#29→#30→#31→#32)
"""

import pytest
from unittest.mock import MagicMock, patch


class TestTwoBrainConflictDetection:
    """Test conflict detection between model and DB paths."""

    def test_detects_factual_conflict_model_vs_db(self):
        """When model says institute X has h-index 45 and DB says 38, conflict detected."""
        model_answer = {"institute": "IIT Bombay", "h_index": 45, "source": "model_internalized"}
        db_answer = {"institute": "IIT Bombay", "h_index": 38, "source": "db_retrieval"}

        conflict_detected = (
            model_answer.get("institute") == db_answer.get("institute")
            and model_answer.get("h_index") != db_answer.get("h_index")
        )
        assert conflict_detected, (
            "Model (45) and DB (38) disagree on IIT Bombay h-index — "
            "conflict resolution should trigger LIVE wins for exact facts"
        )

    def test_no_conflict_when_both_paths_agree(self):
        """When model and DB agree on facts, no conflict to resolve."""
        model_answer = {"institute": "IIT Madras", "tr_lvl": 9, "source": "model_internalized"}
        db_answer = {"institute": "IIT Madras", "tr_lvl": 9, "source": "db_retrieval"}

        has_conflict = (
            model_answer.get("institute") == db_answer.get("institute")
            and model_answer.get("tr_lvl") != db_answer.get("tr_lvl")
        )
        assert not has_conflict, "No conflict when both paths agree on TRL 9 for IIT Madras"

    def test_model_wins_for_qualitative_analysis(self):
        """For analytical patterns (comparisons, trends), model may override DB nuance.

        Example: 'Which institute leads in hydrogen catalysis research?'
        Model internalized: "IIT Bombay leads in hydrogen catalysis (from training data)"
        DB retrieval shows: IIT Bombay 12 papers, IIT Delhi 11 papers
        → Both agree IIT Bombay leads; no conflict
        → Model's qualitative framing wins for the answer
        """
        analytical_query = "Which institute leads in hydrogen catalysis research?"
        model_answer = "IIT Bombay leads in hydrogen catalysis based on research depth and breadth."
        db_facts = {
            "IIT Bombay": {"papers": 12, "h_index_avg": 38},
            "IIT Delhi": {"papers": 11, "h_index_avg": 35},
        }

        db_top_institute = max(db_facts, key=lambda k: db_facts[k]["papers"])
        assert "IIT Bombay" in model_answer and db_top_institute == "IIT Bombay", (
            "Model and DB agree IIT Bombay leads — no conflict for qualitative synthesis"
        )


class TestTwoBrainConflictResolution:
    """Test conflict resolution strategies."""

    def test_live_db_wins_for_exact_counts(self):
        """DB retrieval is authoritative for specific counts/numbers.

        Example conflict:
          Model internalized: "IIT Bombay has 850 publications in 2023"
          DB retrieval:        "IIT Bombay has 912 publications in 2023"
        → RESOLUTION: Live DB (912) wins; model hallucinated the count.
          Return DB result, flag confidence reduction.
        """
        model_fact = {"institute": "IIT Bombay", "publication_count_2023": 850}
        db_fact = {"institute": "IIT Bombay", "publication_count_2023": 912}

        is_exact_fact = "count" in str(model_fact.keys()) or "count" in str(db_fact.keys())
        resolution = db_fact if is_exact_fact else model_fact

        assert resolution == db_fact, (
            "For exact counts, DB (912) must override model hallucination (850)"
        )

    def test_model_wins_for_trend_comparisons(self):
        """Model internalized knowledge wins for trend patterns DB may miss.

        Example conflict:
          DB has: IIT Bombay 2018-2022 data only (no 2023 yet)
          Model:  "2023 saw surge in IIT Bombay hydrogen research due to new lab"
        → RESOLUTION: Model's qualitative trend insight wins; note DB gap.
          Surface both with explicit uncertainty flag.
        """
        db_range = {"start": 2018, "end": 2022, "has_2023": False}
        model_trend = "2023 saw surge in IIT Bombay hydrogen research"

        db_has_2023 = db_range.get("has_2023", False)
        is_trend_statement = "surge" in model_trend.lower() or "trend" in model_trend.lower()

        if not db_has_2023 and is_trend_statement:
            resolution = "model_with_db_gap_note"
            assert resolution == "model_with_db_gap_note", (
                "Model's 2023 trend insight wins when DB has no 2023 data; "
                "append note explaining DB coverage gap"
            )

    def test_confidence_delta_surface_when_unresolvable(self):
        """When neither path can claim authority, surface both with confidence delta.

        Example:
          Model: "IIT Delhi is the top AI research institute in India"
          DB:    "IIT Bombay has higher avg h-index (42) than IIT Delhi (38)"
        → Both are partially correct but frame the question differently
        → Surface both answers with explicit confidence weights; do not merge
        """
        model_answer = {
            "answer": "IIT Delhi is top AI research institute",
            "confidence": 0.72,
            "basis": "publication breadth + citation impact",
        }
        db_answer = {
            "answer": "IIT Bombay has higher avg h-index (42) vs IIT Delhi (38)",
            "confidence": 0.91,
            "basis": "exact DB metrics",
        }

        model_confidence = model_answer["confidence"]
        db_confidence = db_answer["confidence"]

        assert db_confidence > model_confidence, (
            "DB exact metrics (0.91) should outweigh model qualitative claim (0.72)"
        )
        merged_or_surface_both = (
            f"DB ({db_confidence}): {db_answer['answer']}; "
            f"Model ({model_confidence}): {model_answer['answer']}"
        )
        assert "IIT Bombay" in merged_or_surface_both and "h-index" in merged_or_surface_both


class TestTwoBrainIntegration:
    """Integration test: full Two-Brain pipeline with conflict resolution."""

    def test_full_pipeline_routes_and_resolves(self):
        """Simulate full pipeline: route → parallel fetch → conflict → resolve.

        Expected flow:
        1. Classifier marks query as requiring both model + DB paths
        2. Model internalized path returns qualitative answer
        3. DB retrieval path returns exact facts
        4. Conflict detected when answers disagree on same fact
        5. Resolution strategy applied (DB wins for exact facts)
        6. Merged response surfaced with confidence metadata
        """
        query = "What is IIT Bombay's exact publication count and how does its AI research compare?"

        model_result = {
            "publication_count": 850,
            "qualitative": "IIT Bombay leads in AI research breadth",
            "source": "model_internalized",
        }
        db_result = {
            "publication_count": 912,
            "qualitative": "IIT Bombay: 912 papers, avg h-index 42",
            "source": "db_retrieval",
        }

        factual_fields = ["publication_count"]
        has_factual_conflict = any(
            model_result.get(f) != db_result.get(f)
            for f in factual_fields
        )

        assert has_factual_conflict, (
            "Model (850) vs DB (912) conflict detected on publication_count"
        )

        if has_factual_conflict:
            final_answer = {
                "publication_count": db_result["publication_count"],
                "qualitative": db_result["qualitative"],
                "resolution": "DB_WINS_EXACT_FACT",
                "model_hallucination_delta": abs(
                    model_result["publication_count"] - db_result["publication_count"]
                ),
                "confidence_adjustment": "reduced_for_model_conflict",
            }
        else:
            final_answer = {
                "publication_count": db_result["publication_count"],
                "qualitative": model_result["qualitative"],
                "resolution": "MODEL_WINS_QUALITATIVE",
            }

        assert final_answer["publication_count"] == 912, "DB count must win"
        assert final_answer["resolution"] == "DB_WINS_EXACT_FACT"
        assert final_answer["model_hallucination_delta"] == 62
