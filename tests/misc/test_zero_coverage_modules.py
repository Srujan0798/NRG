"""Minimal tests for modules previously at 0% coverage."""

import os
import tempfile
import pytest


class TestReflectorNode:
    def test_validate_output_completeness_pass(self):
        from src.orchestration.nodes.reflector import ReflectorNode
        node = ReflectorNode()
        output = {
            "query_intent": "test",
            "results": [{"data": 1}],
            "confidence_score": 0.9,
            "execution_time": 5.0,
        }
        assert node.validate_output_completeness(output) is True

    def test_validate_output_completeness_missing_field(self):
        from src.orchestration.nodes.reflector import ReflectorNode
        node = ReflectorNode()
        assert node.validate_output_completeness({"results": [], "confidence_score": 0}) is False

    def test_validate_output_completeness_insufficient_results(self):
        from src.orchestration.nodes.reflector import ReflectorNode
        node = ReflectorNode()
        output = {
            "query_intent": "test",
            "results": [],
            "confidence_score": 0.9,
        }
        assert node.validate_output_completeness(output) is False

    def test_validate_output_completeness_timeout(self):
        from src.orchestration.nodes.reflector import ReflectorNode
        node = ReflectorNode()
        output = {
            "query_intent": "test",
            "results": [{"data": 1}],
            "confidence_score": 0.9,
            "execution_time": 999.0,
        }
        assert node.validate_output_completeness(output) is False


class TestRetryHandler:
    def test_handle_retry_success(self):
        from src.orchestration.nodes.retry_handler import RetryHandler
        handler = RetryHandler(max_retries=2)
        result = handler.handle_retry(lambda: "ok")
        assert result == "ok"

    def test_handle_retry_failure(self):
        from src.orchestration.nodes.retry_handler import RetryHandler
        handler = RetryHandler(max_retries=2)
        with pytest.raises(RuntimeError):
            handler.handle_retry(lambda: (_ for _ in ()).throw(RuntimeError("fail")))

    def test_handle_retry_eventual_success(self):
        from src.orchestration.nodes.retry_handler import RetryHandler
        handler = RetryHandler(max_retries=3)
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) < 2:
                raise RuntimeError("fail")
            return "ok"

        result = handler.handle_retry(flaky)
        assert result == "ok"
        assert len(calls) == 2


class TestMultiHopWorkflow:
    def test_execute_multi_hop_query_fails_closed(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from src.orchestration.workflows.multi_hop import MultiHopWorkflow
        wf = MultiHopWorkflow()
        with pytest.raises(RuntimeError, match="compatibility shim is disabled"):
            wf.execute_multi_hop_query("SELECT 1", "vector query")

    def test_validate_multi_hop_results_fails_closed(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from src.orchestration.workflows.multi_hop import MultiHopWorkflow
        wf = MultiHopWorkflow()
        with pytest.raises(RuntimeError, match="compatibility shim is disabled"):
            wf.validate_multi_hop_results([{"type": "multi_hop_result"}])


class TestSeedDatabase:
    def test_seed_database_runs(self):
        from src.db.seed import seed_database
        # Should not raise even if DB is missing / already seeded
        seed_database()


class TestAccessControlLabels:
    def test_access_tier_values(self):
        from src.data.metadata.access_control_labels import AccessTier
        assert AccessTier.TIER_1 == 1
        assert AccessTier.TIER_2 == 2
        assert AccessTier.TIER_3 == 3

    def test_labeler_researcher_fields(self):
        from src.data.metadata.access_control_labels import AccessControlLabeler
        labeler = AccessControlLabeler()
        assert labeler.label_researcher_field("state", "Gujarat") == 3
        assert labeler.label_researcher_field("email", "a@b.com") == 1
        assert labeler.label_researcher_field("name", "Dr X") == 2

    def test_labeler_publication_fields(self):
        from src.data.metadata.access_control_labels import AccessControlLabeler
        labeler = AccessControlLabeler()
        assert labeler.label_publication_field("title", "Paper") == 3
        assert labeler.label_publication_field("author_order", "1") == 2

    def test_labeler_funding_fields(self):
        from src.data.metadata.access_control_labels import AccessControlLabeler
        labeler = AccessControlLabeler()
        assert labeler.label_funding_field("agency", "DST") == 3
        assert labeler.label_funding_field("amount", "100000") == 2

    def test_create_access_label(self):
        from src.data.metadata.access_control_labels import AccessControlLabeler
        labeler = AccessControlLabeler()
        label = labeler.create_access_label("researchers", "state", "Gujarat")
        assert label["access_tier"] == 3
        assert label["source_table"] == "researchers"
        assert label["field_name"] == "state"

    def test_get_access_tier_description(self):
        from src.data.metadata.access_control_labels import get_access_tier_description
        assert "Full access" in get_access_tier_description(1)
        assert "Public access" in get_access_tier_description(3)
        assert get_access_tier_description(99) == "Unknown access tier"

    def test_validate_access_tier(self):
        from src.data.metadata.access_control_labels import validate_access_tier
        assert validate_access_tier(1) is True
        assert validate_access_tier(2) is True
        assert validate_access_tier(3) is True
        assert validate_access_tier(4) is False


class TestCheckpoint:
    def test_sqlite_saver_crud(self):
        from src.orchestration.checkpoint import SqliteSaver
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_checks.db")
            saver = SqliteSaver(db_path=db_path)

            config = {"configurable": {"thread_id": "t1"}}
            checkpoint = {"session_id": "s1", "thread_id": "t1", "data": "hello"}

            # put
            saver.put(config, checkpoint)

            # get
            got = saver.get(config)
            assert got is not None
            assert got["data"] == "hello"

            # list
            listed = saver.list(config)
            assert len(listed) == 1

            # delete
            saver.delete(config)
            assert saver.get(config) is None

    def test_get_checkpointer(self):
        from src.orchestration.checkpoint import get_checkpointer, SqliteSaver
        # Default env should return SqliteSaver
        cp = get_checkpointer()
        assert isinstance(cp, SqliteSaver)
