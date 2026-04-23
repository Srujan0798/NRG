"""
Training Data Formatter — Task #22 Phase 3
Formats training pairs into fine-tuning formats:
- JSONL (instruction/input/output) for Alpaca-style
- ShareGPT (conversations) for chat model fine-tuning
- SQL-specific (question/sql/result) for Text-to-SQL fine-tuning
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.training.quality_filter import GRADE_THRESHOLDS

logger = logging.getLogger(__name__)


class DataFormatter:
    """Formats training pairs into various fine-tuning formats.

    Supports:
    - jsonl: Alpaca instruction format {instruction, input, output}
    - sharegpt: Conversation format {conversations: [{from, value}]}
    - sql: Text-to-SQL format {question, sql_query, sql_result, difficulty}
    """

    def __init__(self, include_metadata: bool = True):
        self.include_metadata = include_metadata

    def to_alpaca(self, pair: dict[str, Any]) -> dict[str, Any]:
        """Convert a training pair to Alpaca instruction format.

        Alpaca format:
        {
            "instruction": "<task description>",
            "input": "<optional context or query>",
            "output": "<the response>"
        }
        """
        route = pair.get("route", "unknown")
        query = pair.get("query", "")
        response = pair.get("response", "")

        if route == "text_to_sql":
            sql = pair.get("sql_generated") or ""
            instruction = (
                "You are an expert SQL query writer for a research database. "
                "Given the natural language question, write a SQL query to answer it."
            )
            input_text = f"Question: {query}"
            if sql:
                input_text += f"\n\nThe query should return: {sql[:200]}"

        elif route == "rag":
            instruction = (
                "You are a research assistant. Given a question and relevant "
                "document chunks, synthesize a clear, cited answer."
            )
            citations_raw = pair.get("citations", "[]")
            try:
                citations = json.loads(citations_raw) if isinstance(citations_raw, str) else citations_raw
            except Exception:
                citations = []
            chunks_info = f"Retrieved {len(citations)} citations"
            input_text = f"Question: {query}\n\n{chunks_info}"

        else:
            instruction = (
                "You are NRG, India's national research intelligence assistant. "
                "Given a research question, provide a comprehensive, cited answer."
            )
            input_text = f"Research question: {query}"

        result = {
            "instruction": instruction,
            "input": input_text,
            "output": response,
        }

        if self.include_metadata:
            result["metadata"] = {
                "quality_grade": pair.get("quality_grade", "ungraded"),
                "tier": pair.get("tier", 1),
                "route": route,
                "verifier_score": pair.get("verifier_score", 0.0),
                "timestamp": pair.get("timestamp", ""),
            }

        return result

    def to_sharegpt(self, pair: dict[str, Any]) -> dict[str, Any]:
        """Convert a training pair to ShareGPT conversation format.

        ShareGPT format:
        {
            "conversations": [
                {"from": "human", "value": "<query>"},
                {"from": "gpt", "value": "<response>"}
            ]
        }
        """
        query = pair.get("query", "")
        response = pair.get("response", "")
        route = pair.get("route", "unknown")
        citations_raw = pair.get("citations", "[]")

        try:
            citations = json.loads(citations_raw) if isinstance(citations_raw, str) else citations_raw
        except Exception:
            citations = []

        citations_str = ", ".join(str(c) for c in citations[:5]) if citations else "none"

        human_msg = f"[{'route': '{route}'}] Question: {query}"
        if citations:
            human_msg += f"\n\nRetrieved {len(citations)} citations: {citations_str}"

        gpt_msg = response
        if citations:
            gpt_msg += f"\n\n[Citations: {citations_str}]"

        conversations = [
            {"from": "human", "value": human_msg},
            {"from": "gpt", "value": gpt_msg},
        ]

        result = {"conversations": conversations}

        if self.include_metadata:
            result["metadata"] = {
                "quality_grade": pair.get("quality_grade", "ungraded"),
                "tier": pair.get("tier", 1),
                "route": route,
                "verifier_score": pair.get("verifier_score", 0.0),
            }

        return result

    def to_sql_format(self, pair: dict[str, Any]) -> dict[str, Any]:
        """Convert a training pair to Text-to-SQL fine-tuning format.

        Format:
        {
            "question": "<natural language>",
            "sql_query": "<generated SQL>",
            "sql_result": "<result rows (truncated)>",
            "difficulty": "<easy/medium/hard>",
            "table_schema": "<optional schema context>",
        }
        """
        route = pair.get("route", "")
        if route != "text_to_sql":
            return {}

        question = pair.get("query", "")
        sql = pair.get("sql_generated", "")
        result_raw = pair.get("sql_result", "")
        row_count = int(pair.get("sql_row_count", 0) or 0)

        try:
            result_data = json.loads(result_raw) if isinstance(result_raw, str) else result_raw
        except Exception:
            result_data = result_raw

        if isinstance(result_data, list):
            result_str = json.dumps(result_data[:10], default=str)
            if len(result_data) > 10:
                result_str += f"\n... and {len(result_data) - 10} more rows"
        else:
            result_str = str(result_data)

        difficulty = "medium"
        sql_lower = sql.lower() if sql else ""
        if "join" in sql_lower or "subquery" in sql_lower:
            difficulty = "hard"
        elif "where" not in sql_lower and "order" not in sql_lower:
            difficulty = "easy"

        result = {
            "question": question,
            "sql_query": sql,
            "sql_result": result_str,
            "row_count": row_count,
            "difficulty": difficulty,
        }

        if self.include_metadata:
            result["metadata"] = {
                "quality_grade": pair.get("quality_grade", "ungraded"),
                "verifier_score": pair.get("verifier_score", 0.0),
                "tier": pair.get("tier", 1),
            }

        return result

    def format_pair(self, pair: dict[str, Any], fmt: str) -> dict[str, Any] | None:
        """Format a single pair into the specified format."""
        fmt = fmt.lower()
        if fmt == "alpaca" or fmt == "jsonl":
            return self.to_alpaca(pair)
        elif fmt == "sharegpt" or fmt == "chat":
            return self.to_sharegpt(pair)
        elif fmt == "sql" or fmt == "text_to_sql":
            return self.to_sql_format(pair)
        else:
            logger.warning(f"Unknown format: {fmt}")
            return None

    def format_batch(
        self,
        pairs: list[dict[str, Any]],
        fmt: str,
    ) -> list[dict[str, Any]]:
        """Format a batch of pairs into the specified format."""
        results = []
        for pair in pairs:
            formatted = self.format_pair(pair, fmt)
            if formatted:
                results.append(formatted)
        return results


def pairs_to_jsonl(pairs: list[dict[str, Any]], output_path: Path | str) -> int:
    """Write training pairs as JSONL (one JSON object per line)."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w") as f:
        for pair in pairs:
            line = json.dumps(pair, ensure_ascii=False, default=str)
            f.write(line + "\n")
            count += 1
    logger.info(f"Wrote {count} pairs to {path}")
    return count


def read_jsonl(input_path: Path | str) -> list[dict[str, Any]]:
    """Read a JSONL file into a list of dicts."""
    path = Path(input_path)
    results = []
    with path.open("r") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results
