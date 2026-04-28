"""Hot-path latency guards for PERF-B7 query execution."""

from __future__ import annotations

import time

from src.orchestration import graph as graph_module
from src.orchestration.graph import NRGWorkflow
from src.orchestration.nodes import planner as planner_module
from src.orchestration.nodes import router as router_module
from src.orchestration.nodes import synthesizer as synthesizer_module
from src.skills.text_to_sql import skill as skill_module
from src.skills.text_to_sql.skill import (
    QueryCompletenessValidator,
    QueryContext,
    TextToSQLSkill,
    TierAwareSqlRewriter,
)


class CountingExtractor:
    def __init__(self) -> None:
        self.relevant_calls = 0
        self.schema_calls = 0
        self.prompt_calls = 0

    def get_relevant_tables(self, query: str) -> list[str]:
        self.relevant_calls += 1
        return ["researchers"]

    def get_schema_metadata(self, tables: list[str]) -> dict:
        self.schema_calls += 1
        return {"tables": {table: {"columns": []} for table in tables}}

    def generate_llm_prompt(self, schema: dict) -> str:
        self.prompt_calls += 1
        return "schema prompt"

    def close(self) -> None:
        pass


class FastSandbox:
    def execute_readonly(self, sql: str, user_tier: int) -> dict:
        return {
            "query": sql,
            "columns": ["name"],
            "results": [{"name": "Ada"}],
            "row_count": 1,
        }

    def close(self) -> None:
        pass


def _build_fast_sql_skill(extractor: CountingExtractor) -> TextToSQLSkill:
    skill = TextToSQLSkill.__new__(TextToSQLSkill)
    skill.llm_provider = None
    skill._db_type = "sqlite"
    skill._db_url = "sqlite:///fake.db"
    skill._context = QueryContext()
    skill._completeness_validator = QueryCompletenessValidator()
    skill.extractor = extractor
    skill.sandbox = FastSandbox()
    skill._sql_rewriter = TierAwareSqlRewriter()
    return skill


def test_text_to_sql_query_plan_cache_reuses_schema_prompt() -> None:
    assert hasattr(skill_module, "clear_query_plan_cache")
    skill_module.clear_query_plan_cache()
    extractor = CountingExtractor()
    skill = _build_fast_sql_skill(extractor)

    query = "List researchers in Gujarat"
    first = skill.execute(query, user_tier=1)
    second = skill.execute(query, user_tier=1)

    assert first["row_count"] == 1
    assert second["row_count"] == 1
    assert extractor.relevant_calls == 1
    assert extractor.schema_calls == 1
    assert extractor.prompt_calls == 1


def test_text_to_sql_llm_timeout_falls_back_quickly(monkeypatch) -> None:
    class SlowProvider:
        model = "slow-provider"

        def chat(self, messages):
            time.sleep(1.0)

            class Response:
                content = "SELECT name FROM researchers LIMIT 10"

            return Response()

    monkeypatch.setenv("LLM_TIMEOUT_MS", "10")
    extractor = CountingExtractor()
    skill = _build_fast_sql_skill(extractor)
    skill.llm_provider = SlowProvider()

    start = time.perf_counter()
    sql = skill.generate_sql("List researchers in Gujarat", "schema prompt")
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 800
    assert sql.startswith("SELECT")


def test_structured_sql_only_synthesis_bypasses_cloud_llm(monkeypatch) -> None:
    calls = {"mesh": 0}

    def forbidden_mesh():
        calls["mesh"] += 1
        raise AssertionError("SQL-only synthesis should not call cloud mesh")

    monkeypatch.setenv("CLOUD_SYNTHESIS_ALLOWED", "true")
    monkeypatch.setattr(synthesizer_module, "get_llm_mesh", forbidden_mesh)

    result = synthesizer_module.synthesizer_node(
        {
            "user_query": "Top 5 funding agencies by grant amount",
            "sql_results": [{"agency": "DST", "total_grant": 100}],
            "retrieved_chunks": [],
            "user_tier": 1,
            "routing_decision": "text_to_sql",
            "intent": "structured",
            "complexity": "moderate",
        }
    )

    assert calls["mesh"] == 0
    assert result["synthesis_method"] == "rule_based_sql_fast_path"
    assert "[cite:structured:0]" in result["synthesized_response"]


def test_router_applies_tier_complexity_limit(monkeypatch) -> None:
    monkeypatch.setattr(router_module, "ENABLE_2STAGE_ROUTING", False)

    result = router_module.router_node(
        {
            "user_query": (
                "Synthesize comprehensive research funding output gap trends "
                "comparison with patents, institutions, labs, and publications"
            ),
            "user_tier": 1,
        }
    )

    assert result["complexity"] == "moderate"
    assert result["complexity_limit_applied"] is True
    assert result["complexity_limit"] == "moderate"


def test_planner_heuristic_path_skips_schema_extractor_when_llm_disabled(monkeypatch) -> None:
    monkeypatch.setattr(planner_module, "_get_planner_client", lambda: None)

    def forbidden_extractor(*args, **kwargs):
        raise AssertionError("Heuristic planner should not build full schema prompt")

    monkeypatch.setattr(planner_module, "SQLiteSchemaExtractor", forbidden_extractor)

    result = planner_module.planner_node(
        {"user_query": "Which IIT has high capital expense but low innovation courses?"}
    )

    assert result["planner_metadata"]["mode"] == "heuristic_fallback"
    assert "financial_expenses_capital" in result["plan"]["schema_tables"]
    assert "academic_courses_details" in result["plan"]["schema_tables"]


def test_pipeline_node_latency_budget_documents_sub_3s_target() -> None:
    expected_nodes = {"receiver", "planner", "router", "executor", "synthesizer", "verifier"}
    assert hasattr(graph_module, "PIPELINE_NODE_LATENCY_BUDGET_MS")

    budgets = graph_module.PIPELINE_NODE_LATENCY_BUDGET_MS
    assert set(budgets) == expected_nodes
    assert sum(budgets.values()) <= 3000
    assert budgets["executor"] >= 1000
    assert budgets["synthesizer"] >= 1000


def test_dhairya_benchmark_workflow_p95_under_3s() -> None:
    queries = [
        "Which IIT moved the most projects from Lab Validation to Market Ready?",
        "Top 5 funding agencies by grant amount",
        "Which institutes had grant drops but patent growth?",
        "Which institutes are above the national average for innovation credits?",
        "Which IIT has high capital expense but low innovation courses?",
    ]
    workflow = NRGWorkflow(test_mode=False)
    latencies_ms: list[float] = []
    timings_by_query: list[dict] = []

    for idx, query in enumerate(queries):
        start = time.perf_counter()
        result = workflow.run.__wrapped__(
            workflow,
            query,
            user_tier=1,
            session_id=f"perf-b7-test-{idx}",
        )
        latencies_ms.append((time.perf_counter() - start) * 1000)
        timings_by_query.append(result.get("node_timings") or {})
        if result.get("sql_results"):
            assert result.get("synthesis_method") == "rule_based_sql_fast_path"

    p95_ms = sorted(latencies_ms)[int(len(latencies_ms) * 0.95)]
    assert p95_ms < 3000, {
        "p95_ms": round(p95_ms, 2),
        "latencies_ms": [round(value, 2) for value in latencies_ms],
        "node_timings": timings_by_query,
    }
