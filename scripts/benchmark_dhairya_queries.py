"""
Dhairya's 17-Query Benchmark — NRG Text-to-SQL Pipeline
======================================================

Tests our pipeline against the exact queries Dhairya used.
Each query tests a specific failure pattern.

Run with: python scripts/benchmark_dhairya_queries.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.skills.text_to_sql.skill import TextToSQLSkill
from src.skills.text_to_sql.validator import QueryCompletenessValidator


DHAIRYA_QUERIES = [
    {
        "id": 1,
        "question": "Which institute offers the most intensive innovation curriculum in FY 2022-23 based on total credits, not just course count?",
        "expected_keywords": ["SPLIT_PART", "total_credit_score", "GROUP BY institute", "ORDER BY"],
        "forbidden_patterns": ["LIMIT 1;", "CAST(total_credit_score AS INTEGER)"],
        "tables_expected": ["academic_courses_details"],
        "status": "xxx",
        "failure_pattern": "Credits format — SPLIT_PART needed, LIMIT 1 unwanted",
    },
    {
        "id": 2,
        "question": "Show me the ratio of PhD level innovation courses to Undergraduate ones for IIT Bombay.",
        "expected_keywords": ["level_of_course", "IIT Bombay", "GROUP BY"],
        "forbidden_patterns": ["phd_to_ug_ratio"],  # ratio format acceptable but different
        "tables_expected": ["academic_courses_details"],
        "status": "yyy",
        "failure_pattern": "Format mismatch — ratio vs per-level counts",
    },
    {
        "id": 3,
        "question": "Flag any institute where grant funding has dropped by more than 50% year-over-year between 2020-21 to 2021-22.",
        "expected_keywords": ["WITH", "YearlyGrants", "SUM(grant_received)", "GROUP BY", "JOIN"],
        "forbidden_patterns": ["ig1.grant_received", "ig2.grant_received"],  # row-level
        "tables_expected": ["innovation_grant_from_govt"],
        "status": "xxx",
        "failure_pattern": "CTE + YoY aggregation — row-level comparison wrong",
    },
    {
        "id": 4,
        "question": "Who are the top 5 unique funding agencies providing grants to us?",
        "expected_keywords": ["gov_organisation_name", "SUM(grant_received)", "ORDER BY", "DESC"],
        "forbidden_patterns": ["DISTINCT", "ORDER BY gov_organisation_name"],  # alphabetical wrong
        "tables_expected": ["innovation_grant_from_govt"],
        "status": "000",
        "failure_pattern": "ORDER BY without aggregation — needs GROUP BY + SUM",
    },
    {
        "id": 5,
        "question": "Identify bottlenecks: What percentage of IIT Madras innovations are stuck at 'Lab Validation' (Level 4)?",
        "expected_keywords": ["stage_of_technology", "IIT Madras", "percentage", "GROUP BY"],
        "forbidden_patterns": [],
        "tables_expected": ["innovations_at_various_stages_of_technology_readiness_level"],
        "status": "zzz",
        "failure_pattern": "Question interpretation — breakdown all stages vs single value",
    },
    {
        "id": 6,
        "question": "List all technologies that are 'Market Ready' (TRL 9) for commercialization in IIT Madras",
        "expected_keywords": ["stage_of_technology", "Level 9", "IIT Madras"],  # NOT 'TRL 9'
        "forbidden_patterns": ["TRL 9"],  # wrong value
        "tables_expected": ["innovations_at_various_stages_of_technology_readiness_level"],
        "status": "000",
        "failure_pattern": "String mismatch — 'Level 9' is DB value, not 'TRL 9'",
    },
    {
        "id": 7,
        "question": "Calculate the 'Cost of Innovation': How much government grant money do we spend for every 1 Patent granted?",
        "expected_keywords": ["WITH", "GrantData", "PatentData", "SUM", "status = 'Granted'"],
        "forbidden_patterns": ["patents_granted", "ig JOIN pd"],  # wrong join pattern
        "tables_expected": ["innovation_grant_from_govt", "combined_ipo_patent_data"],
        "status": "zzz",
        "failure_pattern": "CTE cost-per-unit pattern — wrong table + no status filter",
    },
    {
        "id": 8,
        "question": "Show me all PG innovation courses at IIT Madras for the last 3 years starting from FY 2021-22.",
        "expected_keywords": ["level_of_course = 'PG'", "IIT Madras", "financial_year IN"],
        "forbidden_patterns": [],
        "tables_expected": ["academic_courses_details"],
        "status": "xxx",
        "failure_pattern": "Broad but correct — low severity",
    },
    {
        "id": 9,
        "question": "Which institute has the most PhD courses?",
        "expected_keywords": ["level_of_course = 'PhD'", "GROUP BY", "ORDER BY", "COUNT"],
        "forbidden_patterns": [],
        "tables_expected": ["academic_courses_details"],
        "status": "xxx",
        "failure_pattern": "None — correct",
    },
    {
        "id": 10,
        "question": "How does that compare to their UG numbers?",  # follow-up to Q9
        "expected_keywords": ["level_of_course", "UG", "IIT Hyderabad", "GROUP BY"],
        "forbidden_patterns": ["student_strength", "actual_student_strength"],  # wrong table
        "tables_expected": ["academic_courses_details"],
        "status": "zzz",
        "failure_pattern": "Follow-up lost domain — switched to student_strength",
    },
    {
        "id": 11,
        "question": "Identify growth trends: Calculate Year-Over-Year growth for PG courses in IIT Madras.",
        "expected_keywords": ["WITH", "YearlyData", "COUNT(*)", "GROUP BY financial_year"],
        "forbidden_patterns": ["LAG", "total_credit_score", "OVER (ORDER BY)"],  # credits not count
        "tables_expected": ["academic_courses_details"],
        "status": "xxx",
        "failure_pattern": "YoY on credits not counts — CTE pattern needed",
    },
    {
        "id": 12,
        "question": "Detect Strategy Shift: Institute stops UG but spikes in PhD in IIT Madras.",
        "expected_keywords": ["CASE WHEN", "level_of_course = 'UG'", "level_of_course = 'PhD'", "GROUP BY financial_year"],
        "forbidden_patterns": ["phd_students", "sanctioned_intake"],  # wrong tables
        "tables_expected": ["academic_courses_details"],
        "status": "zzz",
        "failure_pattern": "Cross-domain confusion — phd_students vs courses",
    },
    {
        "id": 13,
        "question": "Correlation: Innovation Courses vs. Startups Incubated (Cross-Module).",
        "expected_keywords": ["academic_courses_details", "incubation_details", "GROUP BY institute"],
        "forbidden_patterns": [],
        "tables_expected": ["academic_courses_details", "incubation_details"],
        "status": "xxx",
        "failure_pattern": "Over-join but functional — low severity",
    },
    {
        "id": 14,
        "question": "Gap Analysis: High Capital Expenses but Low Innovation Courses in FY 2023-24",
        "expected_keywords": ["financial_expenses_capital", "academic_courses_details", "capital_assets", "GROUP BY"],
        "forbidden_patterns": ["HAVING COUNT(acd", "= 0"],  # excludes all with courses
        "tables_expected": ["financial_expenses_capital", "academic_courses_details"],
        "status": "yyy",
        "failure_pattern": "HAVING too restrictive — should show high capex low courses",
    },
    {
        "id": 15,
        "question": "Rising Stars: Institutes growing funding while the average declines.",
        "expected_keywords": ["innovation_grant_from_govt", "GROUP BY institute"],
        "forbidden_patterns": ["Error"],
        "tables_expected": ["innovation_grant_from_govt"],
        "status": "000",
        "failure_pattern": "Complex multi-step — needs explicit scaffolding",
    },
    {
        "id": 16,
        "question": "Utilization Audit: High Grants vs Low Expenditure.",
        "expected_keywords": ["innovation_grant_from_govt", "financial_expenses_operational", "HAVING"],
        "forbidden_patterns": ["-- [INCOMPLETE]", "LEFT JOIN", "fc."],  # incomplete query
        "tables_expected": ["innovation_grant_from_govt", "financial_expenses_operational"],
        "status": "zzz",
        "failure_pattern": "Query truncated — missing HAVING clause",
    },
    {
        "id": 17,
        "question": "Pipeline Progression: Are we moving from Low TRL to High TRL?",
        "expected_keywords": ["stage_of_technology", "financial_year", "GROUP BY"],
        "forbidden_patterns": [],  # only stage grouping loses time dimension
        "tables_expected": ["innovations_at_various_stages_of_technology_readiness_level"],
        "status": "xxx",
        "failure_pattern": "Lost time dimension — needs financial_year in GROUP BY",
    },
]


class BenchmarkRunner:
    def __init__(self):
        self.validator = QueryCompletenessValidator()
        self.results = []

    def run_query(self, query_entry: dict) -> dict:
        """Run a single query through the pipeline and analyze the result."""
        skill = TextToSQLSkill(llm_provider=None)  # Will use fallback
        skill._context = skill._context.__class__()

        try:
            result = skill.execute(query_entry["question"], user_tier=1)
            raw_sql = result.get("query", "")
        except Exception as e:
            raw_sql = f"ERROR: {e}"
        finally:
            skill.close()

        sql = raw_sql.strip() if raw_sql else ""
        is_complete, completeness_issues = self.validator.validate(sql)

        analysis = self._analyze(sql, query_entry)
        return {
            "id": query_entry["id"],
            "question": query_entry["question"],
            "generated_sql": sql,
            "is_complete": is_complete,
            "completeness_issues": completeness_issues,
            "analysis": analysis,
        }

    def _analyze(self, sql: str, entry: dict) -> dict:
        """Analyze how well the generated SQL matches expectations."""
        sql_lower = sql.lower()
        issues = []
        passed = []

        for kw in entry.get("expected_keywords", []):
            if kw.lower() in sql_lower:
                passed.append(kw)
            else:
                issues.append(f"Missing expected: {kw}")

        for fp in entry.get("forbidden_patterns", []):
            if fp.lower() in sql_lower:
                issues.append(f"Contains forbidden: {fp}")

        if not sql or sql.startswith("ERROR"):
            verdict = "FAIL_ERROR"
        elif issues:
            verdict = "FAIL_WRONG"
        elif not entry.get("expected_keywords"):
            verdict = "PASS"
        elif len(passed) >= len(entry["expected_keywords"]) * 0.6:
            verdict = "PASS"
        else:
            verdict = "FAIL_MISSING"

        return {
            "passed_keywords": passed,
            "issues": issues,
            "verdict": verdict,
        }

    def run_all(self):
        print("=" * 80)
        print("NRG Text-to-SQL Benchmark — Dhairya's 17 Queries")
        print("=" * 80)
        print()

        for entry in DHAIRYA_QUERIES:
            result = self.run_query(entry)
            self.results.append(result)

        self._print_summary()
        return self.results

    def _print_summary(self):
        verdicts = {"PASS": [], "FAIL_WRONG": [], "FAIL_ERROR": [], "FAIL_MISSING": []}
        for r in self.results:
            verdicts[r["analysis"]["verdict"]].append(r["id"])

        total = len(self.results)
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total queries: {total}")
        print(f"  PASS (correct SQL): {len(verdicts['PASS'])} — {verdicts['PASS']}")
        print(f"  FAIL (wrong logic): {len(verdicts['FAIL_WRONG'])} — {verdicts['FAIL_WRONG']}")
        print(f"  FAIL (errors):     {len(verdicts['FAIL_ERROR'])} — {verdicts['FAIL_ERROR']}")
        print(f"  FAIL (missing kw): {len(verdicts['FAIL_MISSING'])} — {verdicts['FAIL_MISSING']}")
        print()

        print("=" * 80)
        print("DETAILED RESULTS")
        print("=" * 80)

        for r in self.results:
            a = r["analysis"]
            status_icon = "✅" if a["verdict"] == "PASS" else "❌"
            print(f"\nQ{r['id']}: {status_icon} {a['verdict']}")
            print(f"  Q: {r['question'][:70]}...")
            if r["generated_sql"]:
                print(f"  SQL: {r['generated_sql'][:120]}")
            else:
                print("  SQL: (none generated)")
            if a["issues"]:
                print(f"  Issues: {a['issues']}")
            if r["completeness_issues"]:
                print(f"  Completeness: {r['completeness_issues']}")


if __name__ == "__main__":
    runner = BenchmarkRunner()
    runner.run_all()
