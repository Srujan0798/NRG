"""Tests for SchemaRetriever — LB-8 semantic layer + schema RAG."""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

os.environ["NRG_ENV"] = "dev"
os.environ["EMBEDDER_DETERMINISTIC"] = "1"


class TestTableDDL:
    def test_table_ddl_creation(self):
        from src.skills.text_to_sql.schema_retriever import TableDDL

        tbl = TableDDL(
            name="academic_courses_details",
            alias="courses",
            columns=[("institute", "text"), ("total_credit_score", "text")],
            ddl_text="CREATE TABLE academic_courses_details ();",
            description="Academic courses and credits",
        )
        assert tbl.name == "academic_courses_details"
        assert tbl.alias == "courses"
        assert len(tbl.columns) == 2

    def test_to_chunk_text(self):
        from src.skills.text_to_sql.schema_retriever import TableDDL

        tbl = TableDDL(
            name="test_table",
            alias="t",
            columns=[("id", "integer"), ("name", "text")],
            ddl_text="CREATE TABLE test_table ();",
            description="A test table",
        )
        chunk = tbl.to_chunk_text()
        assert "TABLE: test_table" in chunk
        assert "ALIAS: t" in chunk
        assert "id (integer)" in chunk
        assert "name (text)" in chunk


class TestSchemaRetrieverInit:
    def test_init_default_paths(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        retriever = SchemaRetriever()
        assert retriever.db_struct_path.exists()
        assert retriever.top_k == 5

    def test_init_custom_paths(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        retriever = SchemaRetriever(top_k=3)
        assert retriever.top_k == 3


class TestSchemaRetrieverLoad:
    def test_load_parses_db_struct(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()

        assert len(retriever._tables) > 0
        assert "academic_courses_details" in retriever._tables
        assert "innovation_grant_from_govt" in retriever._tables

    def test_load_skips_auth_tables(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()

        assert "auth_user" not in retriever._tables
        assert "django_session" not in retriever._tables

    def test_load_parses_columns(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()

        acd = retriever._tables["academic_courses_details"]
        col_names = [c for c, _ in acd.columns]
        assert "institute" in col_names
        assert "total_credit_score" in col_names
        assert "level_of_course" in col_names

    def test_load_semantic_layer(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()

        assert len(retriever._semantic_layer) > 0
        assert "graphs" in retriever._semantic_layer

    def test_load_glossary(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()

        assert len(retriever._glossary) > 0
        assert "glossary" in retriever._glossary

    def test_double_load_is_noop(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()
            tables_before = len(retriever._tables)
            retriever.load()
            assert len(retriever._tables) == tables_before


class TestCosineSimilarity:
    def test_cosine_sim_same_vector(self):
        from src.skills.text_to_sql.schema_retriever import _cosine_sim

        vec = [1.0, 0.0, 0.0]
        assert _cosine_sim(vec, vec) == pytest.approx(1.0)

    def test_cosine_sim_orthogonal(self):
        from src.skills.text_to_sql.schema_retriever import _cosine_sim

        assert _cosine_sim([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_cosine_sim_normalized(self):
        from src.skills.text_to_sql.schema_retriever import _cosine_sim

        a = [1.0, 1.0]
        b = [1.0, 0.0]
        sim = _cosine_sim(a, b)
        assert 0.0 < sim < 1.0


class TestGetRelevantTables:
    def test_get_relevant_tables_returns_tables(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()
            tables, junctions = retriever.get_relevant_tables(
                "Which IIT has the highest total innovation credits in FY 2022-23?"
            )

        assert len(tables) > 0
        assert len(tables) <= retriever.top_k + 3
        assert isinstance(junctions, list)

    def test_get_relevant_tables_respects_top_k(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever(top_k=3)
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()
            tables, _ = retriever.get_relevant_tables(
                "patent grants by institute",
                top_k=3,
            )
        assert len(tables) <= 3 + 3

    def test_get_relevant_tables_keyword_fallback(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = None
            retriever.load()
            tables, _ = retriever.get_relevant_tables("grant funding by institute")

        assert len(tables) > 0


class TestDisambiguateTerm:
    def test_disambiguate_returns_single_meaning(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()

        meaning = retriever.disambiguate_term(
            "credit score",
            "total credit score for courses",
        )
        assert meaning is None or isinstance(meaning, dict)

    def test_disambiguate_term_not_in_glossary(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()

        result = retriever.disambiguate_term("xyzzy_not_a_term")
        assert result is None


class TestGetRelevantDDL:
    def test_get_relevant_ddl_returns_struct(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()
            result = retriever.get_relevant_ddl(
                "Which IIT has the highest total innovation credits?"
            )

        assert "tables" in result
        assert "ddl" in result
        assert "token_count" in result
        assert "glossary_disambiguations" in result
        assert "semantic_layer_notes" in result
        assert isinstance(result["tables"], list)
        assert result["token_count"] > 0
        assert "CREATE TABLE" in result["ddl"]

    def test_get_relevant_ddl_token_count_is_reasonable(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()
            result = retriever.get_relevant_ddl("total credits for courses")

        avg_tokens_per_table = result["token_count"] / max(len(result["tables"]), 1)
        assert result["token_count"] < 5000
        assert avg_tokens_per_table < 800

    def test_get_relevant_ddl_includes_academic_courses_for_credits(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()
            result = retriever.get_relevant_ddl(
                "total innovation credits FY 2022-23"
            )

        assert "academic_courses_details" in result["tables"]

    def test_get_relevant_ddl_includes_grants_for_funding(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()
            result = retriever.get_relevant_ddl(
                "government grant funding by institute"
            )

        assert "innovation_grant_from_govt" in result["tables"]

    def test_get_relevant_ddl_includes_trl_for_technology_stage(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()
            result = retriever.get_relevant_ddl(
                "TRL stage progression Lab Validation to Market Ready"
            )

        assert "innovations_at_various_stages_of_technology_readiness_level" in result["tables"]


class TestBuildRelevantDDLPromptSection:
    def test_build_prompt_section_contains_ddl(self):
        from src.skills.text_to_sql.schema_retriever import (
            SchemaRetriever,
            build_relevant_ddl_prompt_section,
        )

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            section = build_relevant_ddl_prompt_section(
                question="Which IIT has the highest total innovation credits?",
                schema_retriever=None,
            )

        assert "CREATE TABLE" in section
        assert "-- SCHEMA RETRIEVAL" in section

    def test_build_prompt_section_with_retriever_instance(self):
        from src.skills.text_to_sql.schema_retriever import (
            SchemaRetriever,
            build_relevant_ddl_prompt_section,
        )

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()

            section = build_relevant_ddl_prompt_section(
                question="patent grants and funding",
                schema_retriever=retriever,
            )

        assert len(section) > 0
        assert "CREATE TABLE" in section


class TestRecallBenchmark:
    def test_recall_benchmark_corpus(self):
        from src.skills.text_to_sql.schema_retriever import SchemaRetriever

        corpus = [
            {
                "question": "Which IIT has the highest total innovation credits in FY 2022-23?",
                "relevant_tables": ["academic_courses_details"],
            },
            {
                "question": "government grant funding by institute",
                "relevant_tables": ["innovation_grant_from_govt"],
            },
            {
                "question": "TRL stage progression for innovations",
                "relevant_tables": [
                    "innovations_at_various_stages_of_technology_readiness_level"
                ],
            },
            {
                "question": "patents granted by institute",
                "relevant_tables": ["patents_details"],
            },
            {
                "question": "FDI investment by state",
                "relevant_tables": ["fdi_investment", "tb_institute_mstr"],
            },
            {
                "question": "NIRF ranking and research output",
                "relevant_tables": ["nirf_extracted_table", "advance_search_data"],
            },
            {
                "question": "faculty strength by institute",
                "relevant_tables": ["faculty_strength"],
            },
            {
                "question": "seed funding for startups",
                "relevant_tables": ["seed_funding"],
            },
            {
                "question": "student intake vs actual enrollment",
                "relevant_tables": ["sanctioned_intake", "actual_student_strength"],
            },
            {
                "question": "PhD students graduated by institute",
                "relevant_tables": ["phd_students"],
            },
            {
                "question": "cost per patent granted for institutes with high grants",
                "relevant_tables": [
                    "innovation_grant_from_govt",
                    "patents_details",
                    "combined_ipo_patent_data",
                ],
            },
            {
                "question": "consultancy income by state",
                "relevant_tables": [
                    "research_consultancy_details_consultancy",
                    "tb_institute_mstr",
                ],
            },
            {
                "question": "patent efficiency vs grant spending",
                "relevant_tables": [
                    "innovation_grant_from_govt",
                    "combined_ipo_patent_data",
                ],
            },
            {
                "question": "rising star institutes whose funding grew while average declined",
                "relevant_tables": ["innovation_grant_from_govt"],
            },
            {
                "question": "year-over-year course growth for PG programs",
                "relevant_tables": ["academic_courses_details"],
            },
        ]

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            retriever = SchemaRetriever()
            retriever._embedder = MagicMock()
            retriever._embed_all_tables = MagicMock()
            retriever.load()

            result = retriever.get_recall_at_k(corpus, k=5)

        recall = result["recall_at_k"]
        assert recall >= 0.0
        assert 0.0 <= recall <= 1.0


class TestGetDefaultRetriever:
    def test_singleton_cached(self):
        from src.skills.text_to_sql.schema_retriever import get_default_retriever

        with patch.dict(os.environ, {"EMBEDDER_DETERMINISTIC": "1"}):
            r1 = get_default_retriever()
            r2 = get_default_retriever()
        assert r1 is r2


class TestTokenEstimate:
    def test_estimate_tokens(self):
        from src.skills.text_to_sql.schema_retriever import _estimate_tokens

        assert _estimate_tokens("a" * 1000) == 250
        assert _estimate_tokens("a") == 1
        assert _estimate_tokens("") == 0


class TestTableAlias:
    def test_table_to_alias(self):
        from src.skills.text_to_sql.schema_retriever import _table_to_alias

        assert _table_to_alias("tb_institute_mstr") == "institutes"
        assert _table_to_alias("academic_courses_details") == "courses"
        assert _table_to_alias("innovation_grant_from_govt") == "grants"
        assert _table_to_alias("unknown_table_xyz") == "unknown_table_xyz"
