"""Comprehensive tests for the LLM Router with 2-stage routing and confidence scoring.

Phase 1 - Fortify: Edge cases, confidence thresholds, SQL injection defense
Phase 2 - Elevate: 2-stage routing, multi-intent detection
Phase 3 - Immortalize: Self-calibration, metrics
"""

import importlib
import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.orchestration.nodes.router import (
    router_node,
    _classify_intent_with_confidence,
    _detect_ambiguity,
    _detect_multi_intent,
    _is_sql_injection_attempt,
    _sanitize_query,
    _stage1_regex_classification,
    _apply_default_clarifications,
    RoutingMetrics,
    CONFIDENCE_THRESHOLD_LOW,
    CONFIDENCE_THRESHOLD_HIGH,
    RoutingDecision,
)


class TestRouterEdgeCases:
    """Phase 1 - Edge case handling tests."""

    def test_empty_query_returns_hybrid_safe_mode(self):
        """Empty query should route to hybrid with low confidence and security flag."""
        result = router_node({"user_query": ""})
        assert result["intent"] == "hybrid"
        assert result["routing_decision"] == "text_to_sql+rag"
        assert result["routing_confidence"] == 0.3
        assert result["is_ambiguous"] is True
        assert "empty_query" in result["ambiguity_issues"]
        assert result["stage"] == "edge_case"

    def test_whitespace_only_query_returns_hybrid(self):
        """Whitespace-only query should be treated as empty."""
        result = router_node({"user_query": "   \n\t  "})
        assert result["intent"] == "hybrid"
        assert result["routing_confidence"] == 0.3

    def test_single_word_query_routes_to_rag(self):
        """Single-word queries should default to RAG for document search."""
        result = router_node({"user_query": "AI"})
        assert result["intent"] == "unstructured"
        assert result["routing_decision"] == "rag"
        assert result["routing_confidence"] == 0.4
        assert result["is_ambiguous"] is True
        assert "single_word_query" in result["ambiguity_issues"]

    def test_sql_injection_detected_routes_safe(self):
        """SQL injection attempts should be caught and routed safely."""
        malicious_queries = [
            "'; DROP TABLE researchers; --",
            "OR 1=1",
            "UNION SELECT password FROM users--",
            "' OR ''='",
            "'; DELETE FROM grants; --",
        ]
        for query in malicious_queries:
            result = router_node({"user_query": query})
            assert result["intent"] == "hybrid", f"SQL injection not caught: {query}"
            assert result["routing_confidence"] == 0.2, f"Wrong confidence for: {query}"
            assert result["stage"] == "security", f"Not flagged as security: {query}"
            assert "sql_injection_detected" in result["ambiguity_issues"]

    def test_extremely_long_query_truncated(self):
        """10,000+ char queries should be truncated."""
        long_query = "AI research " * 2000
        assert len(long_query) > 10000

        with patch("src.orchestration.nodes.router.MAX_QUERY_LENGTH", 1000):
            sanitized = _sanitize_query(long_query)
            assert len(sanitized) <= 1000

    def test_query_normalized_whitespace(self):
        """Queries should have normalized whitespace."""
        query = "AI    research\n\nin\n\nIndia"
        sanitized = _sanitize_query(query)
        assert "\n" not in sanitized
        assert "  " not in sanitized


class TestRouterConfidenceThresholds:
    """Phase 1 - Confidence threshold enforcement tests."""

    def test_high_confidence_structured(self):
        """High confidence structured query routes correctly."""
        result = router_node({"user_query": "List all researchers in Gujarat working on AI"})
        assert result["intent"] == "structured"
        assert result["routing_confidence"] >= CONFIDENCE_THRESHOLD_HIGH
        assert result["routing_decision"] == "text_to_sql"

    def test_low_confidence_upgraded_to_hybrid(self):
        """Queries with confidence < 0.6 should be upgraded to hybrid."""
        result = router_node({"user_query": "Who is doing the best research?"})
        assert result["intent"] == "hybrid"
        assert result["routing_confidence"] >= CONFIDENCE_THRESHOLD_LOW
        assert result["routing_decision"] == "text_to_sql+rag"

    def test_confidence_threshold_configurable(self):
        """Confidence thresholds should be configurable via environment variables."""
        with patch.dict(os.environ, {"ROUTER_CONFIDENCE_THRESHOLD_LOW": "0.7"}):
            result = router_node({"user_query": "What is AI?"})
            if result["routing_confidence"] < 0.7:
                assert result["intent"] == "hybrid"


class TestRouterAmbiguityDetection:
    """Phase 1 - Ambiguity detection tests."""

    def test_detect_ambiguous_best(self):
        """'best' keyword should trigger ambiguity detection."""
        is_amb, issues = _detect_ambiguity("Who is the best researcher?")
        assert is_amb is True
        assert "best" in issues

    def test_detect_ambiguous_compare(self):
        """'compare' keyword should trigger ambiguity detection."""
        is_amb, issues = _detect_ambiguity("Compare IIT Delhi vs IIT Bombay")
        assert is_amb is True
        assert any("compar" in i or "versus" in i for i in issues)

    def test_detect_ambiguous_recent(self):
        """'recent' keyword should trigger ambiguity detection."""
        is_amb, issues = _detect_ambiguity("What are recent trends in AI?")
        assert is_amb is True

    def test_detect_not_ambiguous_simple_query(self):
        """Simple unambiguous queries should not trigger ambiguity."""
        is_amb, issues = _detect_ambiguity("List all publications in 2023")
        assert is_amb is False


class TestRouterMultiIntent:
    """Phase 2 - Multi-intent detection and decomposition tests."""

    def test_multi_intent_detected(self):
        """Multi-intent queries (with AND) should be detected."""
        is_multi, subqueries = _detect_multi_intent(
            "Find researchers in ML and explain their recent work"
        )
        assert is_multi is True
        assert len(subqueries) >= 2

    def test_multi_intent_with_comma(self):
        """Multi-intent queries separated by comma should be detected."""
        is_multi, subqueries = _detect_multi_intent(
            "list top funded projects, Analyze their impact"
        )
        assert is_multi is True

    def test_single_intent_not_flagged(self):
        """Single-intent queries should not be flagged as multi-intent."""
        is_multi, subqueries = _detect_multi_intent(
            "What are the latest trends in AI?"
        )
        assert is_multi is False or len(subqueries) <= 1


class TestRouter2StageRouting:
    """Phase 2 - 2-stage routing tests."""

    def test_stage1_regex_classification(self):
        """Stage 1 should perform fast regex classification."""
        intent, conf, details, is_amb, issues = _stage1_regex_classification(
            "List all researchers in Gujarat"
        )
        assert intent == "structured"
        assert conf > 0
        assert details["stage"] == "regex"

    def test_llm_confirmation_disabled_by_env(self):
        """LLM confirmation should be disabled when 2-stage routing is off."""
        with patch.dict(os.environ, {"ROUTER_ENABLE_2STAGE": "false"}):
            mod = importlib.import_module("src.orchestration.nodes.router")
            importlib.reload(mod)
            result = mod.router_node({"user_query": "Who is doing the best research?"})
            assert result["llm_enhanced"] is False

    def test_high_confidence_skips_llm(self):
        """High confidence queries should skip LLM confirmation."""
        with patch.dict(os.environ, {"ROUTER_ENABLE_2STAGE": "true"}):
            result = router_node(
                {"user_query": "List all researchers in Gujarat working on AI"}
            )
            if result["routing_confidence"] >= CONFIDENCE_THRESHOLD_HIGH:
                assert result["llm_enhanced"] is False or result["is_ambiguous"] is True


class TestRouterPlannerIntegration:
    """Tests for planner integration with router."""

    def test_planner_desired_skills_used(self):
        """Router should respect planner's desired_skills."""
        plan = {"desired_skills": ["sql", "rag"]}
        result = router_node({"user_query": "test", "plan": plan})
        assert result["intent"] == "hybrid"
        assert result["plan_skills_used"] is True
        assert result["routing_confidence"] == 0.95

    def test_planner_sql_only(self):
        """Planner SQL-only requests should route to text_to_sql."""
        plan = {"desired_skills": ["sql"]}
        result = router_node({"user_query": "test", "plan": plan})
        assert result["intent"] == "structured"
        assert result["routing_decision"] == "text_to_sql"

    def test_planner_rag_only(self):
        """Planner RAG-only requests should route to rag."""
        plan = {"desired_skills": ["rag"]}
        result = router_node({"user_query": "test", "plan": plan})
        assert result["intent"] == "unstructured"
        assert result["routing_decision"] == "rag"


class TestRouterDefaultClarifications:
    """Tests for default clarification application."""

    def test_clarification_best(self):
        """'best' should add clarification about most publications."""
        clarifications = _apply_default_clarifications(
            "Who is doing the best research in AI?"
        )
        assert any("most publications" in c for c in clarifications)

    def test_clarification_compare(self):
        """'compare' should add clarification about comparison criteria."""
        clarifications = _apply_default_clarifications(
            "Compare IIT Delhi versus IIT Bombay"
        )
        assert any("publication count" in c for c in clarifications)

    def test_clarification_recent(self):
        """'recent' should add clarification about time window."""
        clarifications = _apply_default_clarifications(
            "What are recent trends in AI?"
        )
        assert any("last 3 years" in c for c in clarifications)


class TestRouterMetrics:
    """Phase 3 - Self-calibration and metrics tests."""

    def setup_method(self):
        """Reset metrics singleton before each test."""
        RoutingMetrics.reset()

    def test_metrics_singleton(self):
        """RoutingMetrics should be a singleton."""
        metrics1 = RoutingMetrics()
        metrics2 = RoutingMetrics()
        assert metrics1 is metrics2

    def test_metrics_record(self):
        """Metrics should record routing decisions."""
        metrics = RoutingMetrics()
        metrics.record("structured", 0.9, False, False)

        result = metrics.get_metrics()
        assert result["total_routes"] == 1
        assert result["route_distribution"]["structured"] == 1

    def test_metrics_ambiguity_rate(self):
        """Metrics should track ambiguity rate."""
        metrics = RoutingMetrics()
        metrics.record("structured", 0.9, True, False)
        metrics.record("unstructured", 0.8, False, False)

        result = metrics.get_metrics()
        assert result["ambiguity_rate"] == 0.5

    def test_metrics_llm_enhancement_rate(self):
        """Metrics should track LLM enhancement rate."""
        metrics = RoutingMetrics()
        metrics.record("hybrid", 0.85, True, True)
        metrics.record("structured", 0.9, False, False)

        result = metrics.get_metrics()
        assert result["llm_enhancement_rate"] == 0.5

    def test_self_calibration_data_collection(self):
        """Self-calibration data should be collected when enabled."""
        with patch.dict(os.environ, {"ROUTER_ENABLE_SELF_CALIBRATION": "true"}):
            metrics = RoutingMetrics()
            metrics.record("structured", 0.9, False, False, was_correct=True)
            metrics.record("structured", 0.85, False, False, was_correct=False)

            assert len(metrics.self_calibration_data) == 2


class TestRouterIntentClassification:
    """Tests for intent classification."""

    def test_structured_intent_high_confidence(self):
        """Structured queries should get high confidence."""
        query = "List all researchers in Gujarat with funding above 1 crore"
        intent, conf, details = _classify_intent_with_confidence(query)
        assert intent == "structured"
        assert conf >= 0.6

    def test_unstructured_intent_high_confidence(self):
        """Unstructured queries should get high confidence."""
        query = "What are the latest trends in hydrogen catalysis?"
        intent, conf, details = _classify_intent_with_confidence(query)
        assert intent == "unstructured"
        assert conf >= 0.6

    def test_hybrid_intent_when_both_keywords_present(self):
        """Queries with both hybrid and other keywords should be hybrid."""
        query = "synthesize and find the latest ML research"  # hybrid + structured
        intent, conf, details = _classify_intent_with_confidence(query)
        assert intent == "hybrid", f"Expected hybrid but got {intent}"

    def test_no_match_defaults_to_unstructured(self):
        """Queries with no pattern match should default to unstructured."""
        query = "xyzabc123unknown"
        intent, conf, details = _classify_intent_with_confidence(query)
        assert intent == "unstructured"
        assert conf == 0.5


class TestRouterSQLInjectionDefense:
    """Phase 1 - SQL injection defense tests."""

    def test_sql_injection_patterns_detected(self):
        """Common SQL injection patterns should be detected."""
        malicious = [
            "'; DROP TABLE users; --",
            "OR 1=1",
            "UNION SELECT",
            "' OR ''='",
            "admin'--",
            "1; DELETE FROM grants",
        ]
        for query in malicious:
            assert _is_sql_injection_attempt(query) is True, f"Not detected: {query}"

    def test_normal_query_not_flagged(self):
        """Normal queries should not be flagged as SQL injection."""
        normal_queries = [
            "List all researchers in Gujarat",
            "What are the latest trends?",
            "Show me publications in 2023",
        ]
        for query in normal_queries:
            assert _is_sql_injection_attempt(query) is False, f"Falsely flagged: {query}"


class TestRouterRoutingDecisionStructure:
    """Tests for routing decision return structure."""

    def test_all_required_fields_present(self):
        """All required fields should be present in routing decision."""
        result = router_node({"user_query": "What is AI?"})

        required_fields = [
            "intent",
            "routing_decision",
            "routing_confidence",
            "routing_rationale",
            "plan_skills_used",
            "multi_intent",
            "subqueries",
            "is_ambiguous",
            "ambiguity_issues",
            "clarifications",
            "llm_enhanced",
            "stage",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    def test_routing_rationale_is_informative(self):
        """Routing rationale should contain decision information."""
        result = router_node({"user_query": "What is AI?"})

        rationale_text = " ".join(result["routing_rationale"])
        assert "Intent:" in rationale_text
        assert "Confidence:" in rationale_text
        assert "Stage:" in rationale_text


class TestRouterConfiguration:
    """Tests for router configuration via environment variables."""

    def test_confidence_thresholds_from_env(self):
        """Confidence thresholds should be configurable."""
        with patch.dict(
            os.environ,
            {
                "ROUTER_CONFIDENCE_THRESHOLD_LOW": "0.7",
                "ROUTER_CONFIDENCE_THRESHOLD_HIGH": "0.85",
            },
        ):
            mod = importlib.import_module("src.orchestration.nodes.router")
            importlib.reload(mod)
            assert mod.CONFIDENCE_THRESHOLD_LOW == 0.7
            assert mod.CONFIDENCE_THRESHOLD_HIGH == 0.85

    def test_2stage_routing_toggle(self):
        """2-stage routing should be toggleable."""
        with patch.dict(os.environ, {"ROUTER_ENABLE_2STAGE": "false"}):
            mod = importlib.import_module("src.orchestration.nodes.router")
            importlib.reload(mod)
            assert mod.ENABLE_2STAGE_ROUTING is False

    def test_self_calibration_toggle(self):
        """Self-calibration should be toggleable."""
        with patch.dict(os.environ, {"ROUTER_ENABLE_SELF_CALIBRATION": "false"}):
            mod = importlib.import_module("src.orchestration.nodes.router")
            importlib.reload(mod)
            assert mod.ENABLE_SELF_CALIBRATION is False


class TestRouterEvaluationDataset:
    """Tests using the routing evaluation dataset."""

    @pytest.fixture
    def eval_dataset(self):
        """Load the routing evaluation dataset."""
        dataset_path = (
            Path(__file__).parent.parent
            / "fixtures"
            / "routing"
            / "routing_eval.json"
        )
        with open(dataset_path) as f:
            return json.load(f)

    def test_dataset_has_50_queries(self, eval_dataset):
        """Dataset should have exactly 50 queries."""
        assert len(eval_dataset["test_cases"]) == 50

    def test_dataset_covers_all_categories(self, eval_dataset):
        """Dataset should cover all expected categories."""
        categories = {tc["category"] for tc in eval_dataset["test_cases"]}
        expected = {
            "structured_data",
            "document_analysis",
            "hybrid",
            "ambiguous",
            "comparison",
            "edge_case",
            "sql_injection",
        }
        assert expected.issubset(categories)

    def test_dataset_has_sql_injection_cases(self, eval_dataset):
        """Dataset should have SQL injection test cases."""
        sql_injection_cases = [
            tc
            for tc in eval_dataset["test_cases"]
            if tc.get("security_flag") is True
        ]
        assert len(sql_injection_cases) >= 3

    def test_dataset_has_edge_cases(self, eval_dataset):
        """Dataset should have edge case queries."""
        edge_cases = [
            tc for tc in eval_dataset["test_cases"] if tc.get("edge_case") is True
        ]
        assert len(edge_cases) >= 3

    def test_routing_dataset_structured_queries(self, eval_dataset):
        """Structured queries in dataset should route correctly."""
        structured_cases = [
            tc for tc in eval_dataset["test_cases"] if tc["category"] == "structured_data"
        ]

        for tc in structured_cases[:3]:
            result = router_node({"user_query": tc["query"]})
            assert result["intent"] == tc["expected_intent"], (
                f"Query: {tc['query']}\n"
                f"Expected: {tc['expected_intent']}\n"
                f"Got: {result['intent']}"
            )

    def test_routing_dataset_security_queries(self, eval_dataset):
        """Security-flagged queries should be handled safely."""
        security_cases = [
            tc
            for tc in eval_dataset["test_cases"]
            if tc.get("security_flag") is True
        ]

        for tc in security_cases:
            result = router_node({"user_query": tc["query"]})
            assert result["intent"] == "hybrid", (
                f"SQL injection not handled safely: {tc['query']}"
            )
            assert result["stage"] == "security"


class TestRouterAgainstEvaluationDataset:
    """Full evaluation of router against the 50-query dataset."""

    @pytest.fixture
    def eval_dataset(self):
        """Load the routing evaluation dataset."""
        dataset_path = (
            Path(__file__).parent.parent
            / "fixtures"
            / "routing"
            / "routing_eval.json"
        )
        with open(dataset_path) as f:
            return json.load(f)

    def test_accuracy_on_dataset(self, eval_dataset):
        """Router should achieve > 85% accuracy on evaluation dataset."""
        correct = 0
        total = 0
        failures = []

        for tc in eval_dataset["test_cases"]:
            result = router_node({"user_query": tc["query"]})
            expected = tc["expected_intent"]

            total += 1
            if result["intent"] == expected:
                correct += 1
            else:
                failures.append(
                    {
                        "id": tc["id"],
                        "query": tc["query"][:50],
                        "expected": expected,
                        "got": result["intent"],
                        "confidence": result["routing_confidence"],
                    }
                )

        accuracy = correct / total if total > 0 else 0
        target_accuracy = eval_dataset["accuracy_target"]

        if failures:
            print(f"\nRouting failures ({len(failures)}):")
            for f in failures[:5]:
                print(f"  {f['id']}: {f['query']}... expected={f['expected']} got={f['got']} conf={f['confidence']}")

        assert (
            accuracy >= target_accuracy
        ), f"Accuracy {accuracy:.2%} below target {target_accuracy:.0%} ({correct}/{total} correct)"

    def test_security_queries_all_safe(self, eval_dataset):
        """All security-flagged queries should be handled safely."""
        security_cases = [
            tc
            for tc in eval_dataset["test_cases"]
            if tc.get("security_flag") is True
        ]

        for tc in security_cases:
            result = router_node({"user_query": tc["query"]})
            assert result["intent"] == "hybrid", (
                f"Security issue: {tc['id']} not routed safely"
            )
            assert result["routing_confidence"] <= 0.3

    def test_edge_cases_handled_gracefully(self, eval_dataset):
        """Edge cases should be handled without crashing."""
        edge_cases = [
            tc for tc in eval_dataset["test_cases"] if tc.get("edge_case") is True
        ]

        for tc in edge_cases:
            try:
                result = router_node({"user_query": tc["query"]})
                assert "intent" in result
                assert "routing_confidence" in result
            except Exception as e:
                pytest.fail(f"Edge case {tc['id']} crashed: {e}")

    def test_multi_intent_detection(self, eval_dataset):
        """Multi-intent queries should be detected and decomposed."""
        multi_intent_cases = [
            tc
            for tc in eval_dataset["test_cases"]
            if tc.get("multi_intent") is True
        ]

        detected = 0
        for tc in multi_intent_cases:
            result = router_node({"user_query": tc["query"]})
            if result.get("multi_intent") is True or len(result.get("subqueries", [])) > 1:
                detected += 1

        detection_rate = detected / len(multi_intent_cases) if multi_intent_cases else 0
        assert (
            detection_rate >= 0.7
        ), f"Multi-intent detection rate {detection_rate:.0%} too low ({detected}/{len(multi_intent_cases)})"
