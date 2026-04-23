"""
Dhairya 17-Query Prompt Analysis Benchmark
==========================================

Tests whether the improved pipeline's prompts would produce the correct SQL
by analyzing prompt composition and comparing against expected patterns.

Run: python scripts/benchmark_dhairya_prompts.py
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.skills.text_to_sql.skill import TextToSQLSkill, QueryContext
from src.skills.text_to_sql.schema_extractor import _load_schema_hints, _load_value_synonyms


DHAIRYA_QUERIES = [
    {"id": 1, "question": "Which institute offers the most intensive innovation curriculum in FY 2022-23 based on total credits, not just course count?"},
    {"id": 2, "question": "Show me the ratio of PhD level innovation courses to Undergraduate ones for IIT Bombay."},
    {"id": 3, "question": "Flag any institute where grant funding has dropped by more than 50% year-over-year between 2020-21 to 2021-22."},
    {"id": 4, "question": "Who are the top 5 unique funding agencies providing grants to us?"},
    {"id": 5, "question": "Identify bottlenecks: What percentage of IIT Madras innovations are stuck at 'Lab Validation' (Level 4)?"},
    {"id": 6, "question": "List all technologies that are 'Market Ready' (TRL 9) for commercialization in IIT Madras"},
    {"id": 7, "question": "Calculate the 'Cost of Innovation': How much government grant money do we spend for every 1 Patent granted?"},
    {"id": 8, "question": "Show me all PG innovation courses at IIT Madras for the last 3 years starting from FY 2021-22."},
    {"id": 9, "question": "Which institute has the most PhD courses?"},
    {"id": 10, "question": "How does that compare to their UG numbers?"},
    {"id": 11, "question": "Identify growth trends: Calculate Year-Over-Year growth for PG courses in IIT Madras."},
    {"id": 12, "question": "Detect Strategy Shift: Institute stops UG but spikes in PhD in IIT Madras."},
    {"id": 13, "question": "Correlation: Innovation Courses vs. Startups Incubated (Cross-Module)."},
    {"id": 14, "question": "Gap Analysis: High Capital Expenses but Low Innovation Courses in FY 2023-24"},
    {"id": 15, "question": "Rising Stars: Institutes growing funding while the average declines."},
    {"id": 16, "question": "Utilization Audit: High Grants vs Low Expenditure."},
    {"id": 17, "question": "Pipeline Progression: Are we moving from Low TRL to High TRL?"},
]


class PromptAnalyzer:
    """
    Analyzes what the TextToSQL pipeline sends to the LLM for each query.
    Validates that the prompt contains the right guidance for each of Dhairya's 17 queries.
    """

    QUERY_GUIDANCE = {
        1: {
            "must_have": ["SPLIT_PART", "total_credit_score", "3:1", "credits format", "split"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": ["CAST(total_credit_score AS INTEGER)"],
        },
        2: {
            "must_have": ["level_of_course", "PG", "PhD", "UG", "course level"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": [],
        },
        3: {
            "must_have": ["year-over-year", "YoY", "CTE", "GROUP BY", "SUM", "yearly aggregates"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": ["row-level grant comparison", "ig1.grant_received"],
        },
        4: {
            "must_have": ["ORDER BY", "SUM", "GROUP BY", "ranked", "top"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": ["DISTINCT.*ORDER BY", "alphabetical"],
        },
        5: {
            "must_have": ["stage_of_technology", "Lab Validation", "Level 4", "percentage", "TRL"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": [],
        },
        6: {
            "must_have": ["TRL 9", "Level 9", "Market Ready", "TRL9", "synonym"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": [],
        },
        7: {
            "must_have": ["CTE", "GrantData", "PatentData", "status", "Granted", "cost per patent"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": ["JOIN applicants"],
        },
        8: {
            "must_have": ["PG", "level_of_course", "IIT Madras", "financial_year", "last 3 years"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": [],
        },
        9: {
            "must_have": ["PhD", "level_of_course", "GROUP BY", "ORDER BY", "COUNT", "most"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": [],
        },
        10: {
            "must_have": ["follow-up", "same table", "academic_courses", "student_strength"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": [],
        },
        11: {
            "must_have": ["year-over-year", "YoY", "COUNT", "GROUP BY financial_year", "course_count"],
            "anti_patterns_regex": ["LAG", "credit.*growth"],
            "anti_patterns_plain": [],
        },
        12: {
            "must_have": ["follow-up", "same table", "CASE WHEN", "UG", "PhD", "academic_courses"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": ["phd_students", "sanctioned_intake"],
        },
        13: {
            "must_have": ["cross-module", "incubation_details", "academic_courses_details", "institute", "correlation"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": [],
        },
        14: {
            "must_have": ["gap analysis", "HAVING", "capital_assets", "GROUP BY", "high capex low"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": ["COUNT(acd.\"id\") = 0", "zero course"],
        },
        15: {
            "must_have": ["rising stars", "funding growth", "average", "innovation_grant", "compared to average"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": [],
        },
        16: {
            "must_have": ["utilization", "HAVING", "operational", "expenditure", "grant expenditure"],
            "anti_patterns_regex": [],
            "anti_patterns_plain": ["INCOMPLETE", "truncated"],
        },
        17: {
            "must_have": ["TRL", "stage_of_technology", "financial_year", "GROUP BY.*financial_year", "progression"],
            "anti_patterns_regex": ["only.*stage", "without.*year", "lost.*time"],
            "anti_patterns_plain": [],
        },
    }

    def __init__(self):
        self.skill = TextToSQLSkill(llm_provider=None)
        self.results = []

    def analyze_query(self, query_entry: dict) -> dict:
        """Analyze what the pipeline would send to LLM for this query."""
        query = query_entry["question"]
        qid = query_entry["id"]

        relevant_tables = self.skill.extractor.get_relevant_tables(query)
        schema = self.skill.extractor.get_schema_metadata(relevant_tables)
        schema_prompt = self.skill.extractor.generate_llm_prompt(schema)

        system_prompt = self.skill._get_dialect_system_prompt()
        context = self.skill._context.get_followup_context()

        user_content = f"{schema_prompt}\n\nUser Query: {query}"
        if context:
            user_content += f"\n\n{context}"
        user_content += "\n\nGenerate SQL:"

        full_prompt = system_prompt + "\n" + user_content
        full_prompt_lower = full_prompt.lower()

        guidance = self.QUERY_GUIDANCE.get(qid, {})
        must_have = guidance.get("must_have", [])
        anti_regex = guidance.get("anti_patterns_regex", [])
        anti_plain = guidance.get("anti_patterns_plain", [])

        passed = []
        failed = []
        for kw in must_have:
            if kw.lower() in full_prompt_lower:
                passed.append(kw)
            else:
                failed.append(f"MISSING: {kw}")

        for ap in anti_regex:
            if re.search(ap, full_prompt, re.IGNORECASE):
                failed.append(f"ANTI-PATTERN: {ap}")

        for ap in anti_plain:
            if ap.lower() in full_prompt_lower:
                failed.append(f"ANTI-PATTERN: {ap}")

        hints = _load_schema_hints()
        synonyms = _load_value_synonyms()
        has_hints = bool(hints and len(hints) > 100)
        has_synonyms = bool(synonyms and len(synonyms) > 100)

        coverage = len(passed) / max(len(must_have), 1) if must_have else 1.0

        verdict = "PASS" if coverage >= 0.7 and not failed else "FAIL"

        return {
            "id": qid,
            "question": query,
            "passed": passed,
            "failed": failed,
            "coverage": coverage,
            "verdict": verdict,
            "prompt_length": len(full_prompt),
            "has_hints": has_hints,
            "has_synonyms": has_synonyms,
            "schema_tables": relevant_tables,
        }

    def run_all(self):
        print("=" * 90)
        print("NRG PROMPT ANALYSIS — Dhairya's 17 Queries")
        print("=" * 90)
        print()

        for entry in DHAIRYA_QUERIES:
            result = self.analyze_query(entry)
            self.results.append(result)

        self._print_summary()
        self._print_detail()
        self.skill.close()
        return self.results

    def _print_summary(self):
        verdicts = {"PASS": [], "FAIL": []}
        coverages = []

        for r in self.results:
            verdicts[r["verdict"]].append(r["id"])
            coverages.append(r["coverage"])

        avg_cov = sum(coverages) / len(coverages) if coverages else 0

        print("=" * 90)
        print("SUMMARY")
        print("=" * 90)
        print(f"Total queries analyzed:  {len(self.results)}")
        print(f"  ✅ PASS (coverage ≥70%): {len(verdicts['PASS'])} — {verdicts['PASS']}")
        print(f"  ❌ FAIL (coverage <70%): {len(verdicts['FAIL'])} — {verdicts['FAIL']}")
        print(f"Average keyword coverage: {avg_cov:.0%}")
        print()

    def _print_detail(self):
        print("=" * 90)
        print("DETAILED ANALYSIS")
        print("=" * 90)

        for r in self.results:
            icon = "✅" if r["verdict"] == "PASS" else "❌"
            print(f"\nQ{r['id']}: {icon} [coverage: {r['coverage']:.0%}] {r['question'][:60]}...")
            print(f"  Tables: {r['schema_tables']}")
            print(f"  Hints: {'✅' if r['has_hints'] else '❌'} | Synonyms: {'✅' if r['has_synonyms'] else '❌'}")
            if r["passed"]:
                print(f"  ✅ Passed: {r['passed']}")
            if r["failed"]:
                print(f"  ❌ Failed: {r['failed']}")


if __name__ == "__main__":
    analyzer = PromptAnalyzer()
    analyzer.run_all()
