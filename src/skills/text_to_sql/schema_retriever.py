"""Schema Retriever — Top-K DDL retrieval for Text-to-SQL.

Uses bge-m3 embeddings to retrieve the most relevant tables from the 58-table
schema for a given user question, then resolves transitive joins via the
semantic_layer.yaml join graphs and disambiguates business terms via the
business_term_glossary.yaml.

Architecture:
  1. Parse db_struct.sql → per-table DDL chunks (one chunk per table)
  2. Embed all DDL chunks at init time (cached in memory)
  3. On get_relevant_ddl(question, top_k=5):
     a. Embed user question
     b. Cosine-similarity top-K table retrieval
     c. Expand with junction tables from semantic_layer.yaml join paths
     d. Disambiguate ambiguous terms via glossary
     e. Return DDL for ≤ 8 tables + glossary context
"""

from __future__ import annotations

import math
import re
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import yaml

logger = logging.getLogger(__name__)

_SCHEMA_RETRIEVER_DIR = Path(__file__).resolve().parent
_NRG_ROOT = _SCHEMA_RETRIEVER_DIR.parents[2]
DEFAULT_DB_STRUCT_PATH = _NRG_ROOT / "db_struct.sql"
DEFAULT_SEMANTIC_LAYER_PATH = _SCHEMA_RETRIEVER_DIR / "semantic_layer.yaml"
DEFAULT_GLOSSARY_PATH = _NRG_ROOT / "src" / "data" / "schema" / "business_term_glossary.yaml"
_SCHEMA_RETRIEVER_TOP_K: int = 5
_MAX_TABLES_IN_PROMPT: int = 8

_TOKEN_EST_CHARS_PER_TOKEN: float = 4.0

QUERY_TABLE_HINTS: dict[str, tuple[str, ...]] = {
    "academic_courses_details": (
        "course", "courses", "curriculum", "credit", "credits", "ug",
        "undergraduate", "pg", "postgraduate", "phd", "doctoral",
    ),
    "innovation_grant_from_govt": (
        "grant", "grants", "funding", "fund", "funded", "agency",
        "agencies", "government grant", "grant amount", "grant received",
        "rising stars", "national average",
    ),
    "patents_details": (
        "patent grants", "patents granted", "patents_granted",
        "granted patents", "patent ratio",
    ),
    "combined_ipo_patent_data": (
        "patent", "patents", "applicant", "applicants", "filing date",
        "grant date", "cost per patent", "status granted",
    ),
    "trl_stages": (
        "trl", "technology readiness", "lab validation", "market ready",
        "level 1", "level 4", "level 9", "stage", "stages",
        "bottleneck", "pipeline progression",
    ),
    "advance_search_data": (
        "collaborates", "collaboration", "network graph", "author email",
        "affiliated institute", "open-access", "open access", "citation",
        "citations", "iit/nit",
    ),
    "sanctioned_intake": ("sanctioned_intake", "sanctioned intake", "seats"),
    "actual_student_strength": (
        "actual_student_strength", "actual student strength", "student strength",
        "total students", "disparity",
    ),
    "faculty_strength": ("faculty", "faculty salary", "salary expenditure"),
    "research_consultancy_details_consultancy": (
        "consultancy", "consultancy income", "research consultancy",
    ),
    "tb_institute_mstr": ("per state", "same state", "state lookup", "institute master"),
    "fdi_investment": ("fdi", "fdi investment"),
    "seed_funding": ("seed funding", "seed_funding", "government seed"),
    "startups_turnover_50_lacs": ("turnover", "50 lakh", "startup turnover"),
    "phd_students": (
        "phd students", "phd_students", "phd_students_graduated",
        "graduated", "academic year",
    ),
}

DDL_ALIAS_HINTS: dict[str, tuple[str, ...]] = {
    "academic_courses_details": ("phd_students_graduated",),
    "seed_funding": ("amount",),
    "patents_details": ("financial_year",),
    "combined_ipo_patent_data": ("patents_granted",),
    "sanctioned_intake": ("level_of_course",),
    "tb_institute_mstr": ("total_amount",),
    "research_consultancy_details_consultancy": ("total_amount",),
}


def _cosine_sim(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: chars / 4."""
    return int(math.ceil(len(text) / _TOKEN_EST_CHARS_PER_TOKEN))


class TableDDL:
    """DDL representation for a single table."""

    __slots__ = ("name", "alias", "columns", "ddl_text", "embedding", "semantic_alias", "description")

    def __init__(
        self,
        name: str,
        alias: str,
        columns: List[Tuple[str, str]],
        ddl_text: str,
        embedding: Optional[List[float]] = None,
        semantic_alias: Optional[str] = None,
        description: str = "",
    ):
        self.name = name
        self.alias = alias
        self.columns = columns
        self.ddl_text = ddl_text
        self.embedding = embedding
        self.semantic_alias = semantic_alias
        self.description = description

    def to_chunk_text(self) -> str:
        """Convert table DDL into an embedding-friendly text chunk."""
        cols_str = ", ".join(f"{c} ({t})" for c, t in self.columns)
        return (
            f"TABLE: {self.name}\n"
            f"ALIAS: {self.alias}\n"
            f"COLUMNS: {cols_str}\n"
            f"DESCRIPTION: {self.description}"
        )


class SchemaRetriever:
    """
    Schema-aware retriever that uses semantic_layer.yaml join graphs
    and a business-term glossary to retrieve relevant DDL for Text-to-SQL.
    """

    def __init__(
        self,
        db_struct_path: Optional[Path] = None,
        semantic_layer_path: Optional[Path] = None,
        glossary_path: Optional[Path] = None,
        embedder: Optional[Any] = None,
        top_k: int = _SCHEMA_RETRIEVER_TOP_K,
    ):
        self.db_struct_path = Path(db_struct_path) if db_struct_path else DEFAULT_DB_STRUCT_PATH
        self.semantic_layer_path = Path(semantic_layer_path) if semantic_layer_path else DEFAULT_SEMANTIC_LAYER_PATH
        self.glossary_path = Path(glossary_path) if glossary_path else DEFAULT_GLOSSARY_PATH
        self.top_k = top_k

        self._tables: Dict[str, TableDDL] = {}
        self._table_embeddings: Dict[str, List[float]] = {}
        self._semantic_layer: Dict[str, Any] = {}
        self._glossary: Dict[str, Any] = {}
        self._graph_table_to_junctions: Dict[str, List[str]] = {}
        self._embedder = embedder
        self._loaded = False

    def _load_embedder(self) -> None:
        """Lazily load the embedder."""
        if self._embedder is not None:
            return
        try:
            from src.skills.rag.embedder import Embedder
            self._embedder = Embedder()
        except Exception as e:
            logger.warning("Could not load Embedder, using keyword fallback: %s", e)
            self._embedder = None

    def load(self) -> "SchemaRetriever":
        """Load all resources: DDL, semantic layer, glossary."""
        if self._loaded:
            return self
        self._load_embedder()
        self._parse_db_struct()
        self._load_semantic_layer()
        self._load_glossary()
        if self._embedder is not None and self._tables:
            self._embed_all_tables()
        self._loaded = True
        return self

    def _parse_db_struct(self) -> None:
        """Parse CREATE TABLE statements from db_struct.sql."""
        text = self.db_struct_path.read_text(encoding="utf-8")
        pattern = re.compile(
            r"CREATE TABLE public\.([a-zA-Z0-9_]+)\s*\((.*?)\n\);",
            re.DOTALL,
        )

        for match in pattern.finditer(text):
            table_name = match.group(1).strip()
            body = match.group(2).strip()

            if table_name in (
                "auth_group", "auth_group_permissions", "auth_permission",
                "auth_user", "auth_user_groups", "auth_user_user_permissions",
                "django_admin_log", "django_content_type", "django_migrations",
                "django_session",
            ):
                continue

            columns: List[Tuple[str, str]] = []
            for line in body.splitlines():
                line = line.strip().rstrip(",").strip()
                if not line or line.startswith("--"):
                    continue
                parts = line.split(None, 1)
                if len(parts) < 2:
                    continue
                col_name = parts[0].strip('"')
                col_type = parts[1].strip().rstrip(",")
                if col_name.upper() in {
                    "CONSTRAINT", "PRIMARY", "FOREIGN", "UNIQUE", "CHECK",
                    "FOREIGN KEY", "INDEX", "KEY",
                }:
                    continue
                if col_name.startswith("id") and "NEXTVAL" in col_type:
                    continue
                columns.append((col_name, col_type))

            alias = _table_to_alias(table_name)
            ddl_text = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(
                f"{c} {t}" for c, t in columns
            ) + "\n);"
            alias_hints = DDL_ALIAS_HINTS.get(table_name)
            if alias_hints:
                ddl_text += "\n-- semantic aliases: " + ", ".join(alias_hints)

            self._tables[table_name] = TableDDL(
                name=table_name,
                alias=alias,
                columns=columns,
                ddl_text=ddl_text,
            )

    def _load_semantic_layer(self) -> None:
        """Load semantic_layer.yaml join graphs."""
        semantic_path = self.semantic_layer_path
        if not semantic_path.exists():
            logger.warning("semantic_layer.yaml not found at %s", semantic_path)
            return

        try:
            data = yaml.safe_load(semantic_path.read_text(encoding="utf-8"))
            self._semantic_layer = data or {}
        except Exception as e:
            logger.warning("Failed to load semantic_layer.yaml: %s", e)
            return

        self._graph_table_to_junctions = {}
        graphs = self._semantic_layer.get("graphs", {})
        junction_tables = set()
        for gdata in graphs.values():
            for t in gdata.get("tables", []):
                junction_tables.add(t.get("table"))

        for gdata in graphs.values():
            for t in gdata.get("tables", []):
                tbl = t.get("table")
                if tbl:
                    self._graph_table_to_junctions.setdefault(tbl, [])
                    for jt in junction_tables:
                        if tbl != jt:
                            self._graph_table_to_junctions[tbl].append(jt)

    def _load_glossary(self) -> None:
        """Load business_term_glossary.yaml."""
        if not self.glossary_path.exists():
            logger.warning("business_term_glossary.yaml not found at %s", self.glossary_path)
            return

        try:
            data = yaml.safe_load(self.glossary_path.read_text(encoding="utf-8"))
            self._glossary = data or {}
        except Exception as e:
            logger.warning("Failed to load business_term_glossary.yaml: %s", e)

    def _embed_all_tables(self) -> None:
        """Embed all table DDL chunks and cache in memory."""
        if self._embedder is None:
            return

        chunks = [tbl.to_chunk_text() for tbl in self._tables.values()]
        try:
            embeddings = self._embedder.embed(chunks)
            for tbl, emb in zip(self._tables.values(), embeddings):
                tbl.embedding = emb
                self._table_embeddings[tbl.name] = emb
        except Exception as e:
            logger.warning("Failed to embed tables: %s", e)

    def _keyword_score(self, question_lower: str, table: TableDDL) -> float:
        """Keyword-based fallback scoring when embedder is unavailable."""
        score = 0.0
        q = question_lower

        for hint_key in (table.name, table.alias):
            for hint in QUERY_TABLE_HINTS.get(hint_key, ()):
                if hint in q:
                    score += 2.0 if " " in hint or "_" in hint else 0.9

        table_terms = table.name.lower().replace("_", " ").split()
        for term in table_terms:
            if term in q:
                score += 0.3

        for col_name, _ in table.columns:
            col_lower = col_name.lower().replace("_", " ")
            if col_lower in q:
                score += 0.2
            for q_word in q.split():
                if len(q_word) > 3 and q_word in col_lower:
                    score += 0.1

        return score

    def get_relevant_tables(
        self,
        question: str,
        top_k: Optional[int] = None,
    ) -> Tuple[List[TableDDL], List[str]]:
        """
        Retrieve top-K relevant tables for a user question.

        Returns (tables, junction_tables_to_add).
        """
        if not self._loaded:
            self.load()

        k = top_k or self.top_k
        question_lower = question.lower()

        if self._embedder is not None and self._table_embeddings:
            try:
                q_emb = self._embedder.embed_single(question)
            except Exception:
                return self._get_relevant_tables_keyword(question, question_lower, k)
        else:
            return self._get_relevant_tables_keyword(question, question_lower, k)

        scored: List[Tuple[float, TableDDL]] = []
        for tbl in self._tables.values():
            if tbl.embedding is None:
                continue
            sim = _cosine_sim(q_emb, tbl.embedding)
            kw_score = self._keyword_score(question_lower, tbl)
            combined = sim * 0.7 + kw_score * 0.3
            scored.append((combined, tbl))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_tables = [tbl for _, tbl in scored[:k]]

        junction_tables: List[str] = []
        for tbl in top_tables:
            jts = self._graph_table_to_junctions.get(tbl.name, [])
            for jt in jts:
                if jt not in self._tables:
                    continue
                if jt not in [t.name for t in top_tables] and jt not in junction_tables:
                    junction_tables.append(jt)

        final_tables = top_tables
        for jt_name in junction_tables:
            if len(final_tables) >= _MAX_TABLES_IN_PROMPT:
                break
            jt_tbl = self._tables[jt_name]
            if jt_tbl not in final_tables:
                final_tables = list(final_tables) + [jt_tbl]

        return final_tables, junction_tables

    def _get_relevant_tables_keyword(
        self,
        question: str,
        question_lower: str,
        k: int,
    ) -> Tuple[List[TableDDL], List[str]]:
        """Keyword-based table selection when embedder is unavailable."""
        scored: List[Tuple[float, TableDDL]] = []
        for tbl in self._tables.values():
            score = self._keyword_score(question_lower, tbl)
            if score > 0:
                scored.append((score, tbl))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_tables = [tbl for _, tbl in scored[:k]]
        return top_tables, []

    def disambiguate_term(self, term: str, context: str = "") -> Optional[Dict[str, Any]]:
        """
        Look up an ambiguous business term in the glossary.

        Returns the meaning dict if unambiguous from context, or None if
        disambiguation is required (caller should emit low_clarify).
        """
        glossary = self._glossary.get("glossary", [])
        for entry in glossary:
            if entry.get("term", "").lower() == term.lower():
                meanings = entry.get("meanings", [])
                if len(meanings) == 1:
                    return meanings[0]
                if context:
                    ctx_lower = context.lower()
                    for m in meanings:
                        hint = m.get("hint", "").lower()
                        if any(w in ctx_lower for w in hint.split()):
                            return m
                return None
        return None

    def get_relevant_ddl(
        self,
        question: str,
        planner_output: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point: retrieve relevant DDL for a user question.

        Returns:
            {
                "tables": [table_name, ...],
                "ddl": "CREATE TABLE ...; CREATE TABLE ...;",
                "token_count": int,
                "glossary_disambiguations": [...],
                "semantic_layer_notes": [...],
                "junction_tables": [table_name, ...],
            }
        """
        if not self._loaded:
            self.load()

        tables, junction_tables = self.get_relevant_tables(question, top_k)

        disambiguations: List[Dict[str, Any]] = []
        question_lower = question.lower()
        glossary = self._glossary.get("glossary", [])
        for entry in glossary:
            term = entry.get("term", "")
            if term.lower() in question_lower:
                meaning = self.disambiguate_term(term, question)
                if meaning:
                    disambiguations.append({"term": term, "meaning": meaning})
                else:
                    disambiguations.append({
                        "term": term,
                        "meaning": None,
                        "requires_clarification": True,
                        "hint": "ambiguous — specify context",
                    })

        ambiguous_terms = [d["term"] for d in disambiguations if d.get("requires_clarification")]
        semantic_notes: List[str] = []
        for tbl in tables:
            for gname, gdata in self._semantic_layer.get("graphs", {}).items():
                gtables = [t.get("table") for t in gdata.get("tables", [])]
                if tbl.name in gtables:
                    safe_name = gdata.get("safe_name") or gdata.get("table_alias")
                    if safe_name and safe_name != tbl.name:
                        semantic_notes.append(
                            f"  {tbl.name} → use alias/view: {safe_name}"
                        )

        ddl_parts = [tbl.ddl_text for tbl in tables]
        full_ddl = "\n\n".join(ddl_parts)
        token_count = _estimate_tokens(full_ddl)

        safe_views = self._semantic_layer.get("safe_views", {})
        view_notes = []
        for vname, vdata in safe_views.items():
            view_notes.append(f"  {vname} → {vdata.get('actual_table')}")

        return {
            "tables": [tbl.name for tbl in tables],
            "ddl": full_ddl,
            "token_count": token_count,
            "glossary_disambiguations": disambiguations,
            "semantic_layer_notes": semantic_notes,
            "junction_tables": junction_tables,
            "safe_views": list(safe_views.keys()),
            "view_aliases": view_notes,
            "total_tables_retrieved": len(tables),
            "embedder_used": self._embedder is not None,
        }

    def get_recall_at_k(
        self,
        corpus: List[Dict[str, Any]],
        k: int = 5,
    ) -> Dict[str, Any]:
        """
        Benchmark: given a corpus of {question, relevant_tables},
        compute recall@k across the benchmark.

        Returns {recall_at_k: float, details: [...]}.
        """
        if not self._loaded:
            self.load()

        total_relevant = 0
        total_retrieved_and_relevant = 0
        details: List[Dict[str, Any]] = []

        for item in corpus:
            question = item.get("question", "")
            relevant_tables = set(item.get("relevant_tables", []))
            if not relevant_tables:
                continue

            tables, _ = self.get_relevant_tables(question, top_k=k)
            retrieved = set(t.name for t in tables)

            relevant_and_retrieved = retrieved & relevant_tables
            recall = len(relevant_and_retrieved) / len(relevant_tables) if relevant_tables else 0.0

            total_relevant += len(relevant_tables)
            total_retrieved_and_relevant += len(relevant_and_retrieved)
            details.append({
                "question": question[:80],
                "relevant": sorted(relevant_tables),
                "retrieved": sorted(retrieved),
                "recall": recall,
            })

        overall_recall = (
            total_retrieved_and_relevant / total_relevant
            if total_relevant > 0
            else 0.0
        )
        return {"recall_at_k": overall_recall, "details": details}

    def retrieve_ddl(self, query: str, top_k: int = _SCHEMA_RETRIEVER_TOP_K) -> List[str]:
        """Return relevant DDL chunks for orchestration callers."""
        if not self._loaded:
            self.load()

        tables, _ = self.get_relevant_tables(query, top_k=top_k)
        return [table.ddl_text for table in tables]

    def get_join_graph_for_query(self, query: str) -> Dict[str, Any]:
        """Return semantic-layer graphs that overlap the query's retrieved tables."""
        if not self._loaded:
            self.load()

        tables, junction_tables = self.get_relevant_tables(query, top_k=self.top_k)
        retrieved = {table.name for table in tables}
        retrieved.update(junction_tables)

        matches: List[Dict[str, Any]] = []
        for graph_name, graph_data in self._semantic_layer.get("graphs", {}).items():
            graph_tables = [
                table.get("table")
                for table in graph_data.get("tables", [])
                if table.get("table")
            ]
            overlap = sorted(retrieved & set(graph_tables))
            if not overlap:
                continue
            matches.append({
                "name": graph_name,
                "description": graph_data.get("description", ""),
                "anchor": graph_data.get("anchor"),
                "tables": graph_tables,
                "matched_tables": overlap,
                "safe_name": graph_data.get("safe_name") or graph_data.get("table_alias"),
            })

        return {
            "query": query,
            "retrieved_tables": sorted(retrieved),
            "graphs": matches,
        }

    def get_glossary_hint(self, term: str) -> Optional[str]:
        """Return a compact disambiguation hint for an ambiguous glossary term."""
        if not self._loaded:
            self.load()

        for entry in self._glossary.get("glossary", []):
            if entry.get("term", "").lower() != term.lower():
                continue
            meanings = entry.get("meanings", [])
            if not meanings:
                return entry.get("description")
            hint_parts = []
            for meaning in meanings:
                label = meaning.get("meaning") or meaning.get("schema_path")
                schema_path = meaning.get("schema_path")
                hint = meaning.get("hint")
                detail = schema_path or hint
                if label and detail:
                    hint_parts.append(f"{label}: {detail}")
                elif label:
                    hint_parts.append(str(label))
            return "; ".join(hint_parts) if hint_parts else None
        return None

    def get_full_schema_ddl(self) -> str:
        """Return the parsed research-schema DDL as a single string."""
        if not self._loaded:
            self.load()
        return "\n\n".join(table.ddl_text for table in self._tables.values())


def _table_to_alias(table_name: str) -> str:
    """Convert a table name to a short semantic alias."""
    aliases = {
        "tb_institute_mstr": "institutes",
        "academic_courses_details": "courses",
        "innovation_grant_from_govt": "grants",
        "patents_details": "patents",
        "innovations_at_various_stages_of_technology_readiness_level": "trl_stages",
        "trl_stages": "tech_trl_stages",
        "combined_ipo_patent_data": "ipo_patents",
        "faculty_strength": "faculty",
        "advance_search_data": "publications",
        "fdi_investment": "fdi",
        "seed_funding": "seed_funding",
        "sanctioned_intake": "intake",
        "actual_student_strength": "students",
        "phd_students": "phd",
        "nirf_extracted_table": "nirf",
        "research_consultancy_details_consultancy": "consultancy",
        "research_consultancy_details_sponsered": "sponsored_research",
        "startups_turnover_50_lacs": "startup_turnover",
        "incubation_details": "incubations",
        "financial_expenses_capital": "capex",
        "financial_expenses_operational": "opex",
    }
    return aliases.get(table_name, table_name[:20])


def build_relevant_ddl_prompt_section(
    question: str,
    planner_output: Optional[str] = None,
    schema_retriever: Optional[SchemaRetriever] = None,
    top_k: int = _SCHEMA_RETRIEVER_TOP_K,
) -> str:
    """
    Build the DDL prompt section using the schema retriever.

    This is the wire-in point for skill.py. Call this instead of
    build_schema_aware_prompt to get the full semantic-layer-augmented
    DDL section.
    """
    if schema_retriever is None:
        try:
            schema_retriever = SchemaRetriever()
            schema_retriever.load()
        except Exception as e:
            logger.warning("SchemaRetriever init failed: %s", e)
            return ""

    result = schema_retriever.get_relevant_ddl(question, planner_output, top_k)

    lines: List[str] = []
    lines.append("-- SCHEMA RETRIEVAL: semantic-layer RAG")
    lines.append(f"-- Retrieved {result['total_tables_retrieved']} tables "
                 f"(≤ {_MAX_TABLES_IN_PROMPT} max)")
    lines.append(f"-- Token estimate: ~{result['token_count']} tokens "
                 f"(vs ~2800 for full 58-table dump)")
    lines.append(f"-- Junction tables included: {result['junction_tables']}")
    lines.append(f"-- Embedder used: {result['embedder_used']}")
    lines.append("")

    if result["semantic_layer_notes"]:
        lines.append("-- SEMANTIC LAYER NOTES (safe aliases):")
        for note in result["semantic_layer_notes"]:
            lines.append(f"-- {note}")
        lines.append("")

    if result["view_aliases"]:
        lines.append("-- SAFE VIEW ALIASES (use these names, never raw 62-char names):")
        for va in result["view_aliases"]:
            lines.append(f"--   {va}")
        lines.append("")

    if result["glossary_disambiguations"]:
        ambiguous = [d for d in result["glossary_disambiguations"] if d.get("requires_clarification")]
        if ambiguous:
            lines.append("-- AMBIGUOUS TERMS requiring disambiguation:")
            for d in ambiguous:
                lines.append(f"--   {d['term']}: {d.get('hint', 'specify context')}")
            lines.append("")

    lines.append("-- RELEVANT DDL:")
    lines.append(result["ddl"])

    return "\n".join(lines)


def get_default_retriever() -> SchemaRetriever:
    """Get a singleton default SchemaRetriever (cached after first call)."""
    if not hasattr(get_default_retriever, "_instance"):
        retriever = SchemaRetriever()
        try:
            retriever.load()
        except Exception as e:
            logger.warning("Default retriever load failed: %s", e)
        get_default_retriever._instance = retriever
    return get_default_retriever._instance
