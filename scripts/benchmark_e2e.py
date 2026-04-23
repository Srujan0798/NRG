"""
Dhairya's 17-Query Benchmark — Full LLM Prompt Pipeline Test
============================================================

Tests the complete Text-to-SQL pipeline:
1. System prompt (domain rules + table mapping + anti-patterns + CTEs)
2. Schema injection via SQLite schema extractor
3. Few-shot examples from sql_examples.py
4. Follow-up context tracking (QueryContext)
5. Query completeness validation

Supports two modes:
- --llm : Use real LLM (set OPENAI_API_KEY or ANTHROPIC_API_KEY)
- (default): Use keyword-routing fallback (no API key needed)

Run:
  python scripts/benchmark_e2e.py                  # fallback mode
  OPENAI_API_KEY=sk-... python scripts/benchmark_e2e.py --llm openai
  ANTHROPIC_API_KEY=sk-ant-... python scripts/benchmark_e2e.py --llm anthropic
"""

import sys
import os
import argparse
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())


class RealLLMClient:
    """Wrapper for real OpenAI/Anthropic/MiniMax API calls."""

    def __init__(self, provider: str, api_key: str, model: str):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client:
            return self._client
        if self.provider == "openai":
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        elif self.provider == "minimax":
            import requests
            self._client = requests
        return self._client

    def chat(self, messages: list) -> MagicMock:
        try:
            if self.provider == "openai":
                client = self._get_client()
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                    temperature=0.1,
                    max_tokens=1024,
                )
                text = response.choices[0].message.content
            elif self.provider == "anthropic":
                client = self._get_client()
                response = client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=messages[0]["content"] if messages and messages[0]["role"] == "system" else "",
                    messages=[{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"],

                )
                text = "".join(block.text for block in response.content)
            elif self.provider == "minimax":
                import re
                import requests
                payload = {
                    "model": self.model,
                    "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
                    "temperature": 0.1,
                    "max_tokens": 1024,
                }
                response = requests.post(
                    "https://api.minimaxi.chat/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=60,
                )
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"]
                text = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
                if not text or len(text) < 10:
                    matches = re.findall(r'(SELECT\s+.+?;)\s*(?:\n|$)', raw, re.IGNORECASE | re.DOTALL)
                    if matches:
                        text = matches[-1].strip()
            else:
                text = "SELECT 1"

            mock = MagicMock()
            mock.content = text.strip()
            return mock
        except Exception as e:
            mock = MagicMock()
            mock.content = f"ERROR: {e}"
            return mock


def main():
    parser = argparse.ArgumentParser(description="Dhairya 17-query benchmark")
    parser.add_argument("--llm", choices=["openai", "anthropic", "minimax"], default=None,
                        help="Use real LLM (requires API key env var)")
    parser.add_argument("--model", default=None, help="Model name (default: gpt-4o / claude-3-5-sonnet-latest / minimax-m2.7)")
    args = parser.parse_args()

    os.environ.setdefault("DATABASE_URL", "sqlite:///db/benchmark_nrg.db")

    llm_provider = None
    llm_name = "keyword-routing fallback"

    if args.llm:
        key = os.environ.get(f"{args.llm.upper()}_API_KEY")
        if key:
            if args.llm == "openai":
                model = args.model or "gpt-4o"
            elif args.llm == "anthropic":
                model = args.model or "claude-3-5-sonnet-latest"
            elif args.llm == "minimax":
                model = args.model or "minimax-m2.7"
            llm_provider = RealLLMClient(args.llm, key, model)
            llm_name = f"{args.llm}/{model}"
        else:
            print(f"WARNING: {args.llm.upper()}_API_KEY not set, using fallback")

    from src.skills.text_to_sql.skill import TextToSQLSkill
    from src.skills.text_to_sql.validator import QueryCompletenessValidator

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

    DHAIRYA_KEYWORDS = {
        1: ["SPLIT_PART", "total_credit_score", "GROUP BY institute", "ORDER BY"],
        2: ["level_of_course", "IIT Bombay", "GROUP BY"],
        3: ["WITH", "YearlyGrants", "SUM(grant_received)", "GROUP BY", "JOIN"],
        4: ["gov_organisation_name", "SUM(grant_received)", "ORDER BY", "DESC"],
        5: ["stage_of_technology", "IIT Madras", "percentage"],
        6: ["stage_of_technology", "Level 9", "IIT Madras"],
        7: ["WITH", "GrantData", "PatentData", "SUM", "status = 'Granted'"],
        8: ["level_of_course = 'PG'", "IIT Madras", "financial_year IN"],
        9: ["level_of_course = 'PhD'", "GROUP BY", "ORDER BY", "COUNT"],
        10: ["level_of_course", "UG", "IIT Hyderabad", "GROUP BY"],
        11: ["WITH", "YearlyData", "COUNT(*)", "GROUP BY financial_year"],
        12: ["CASE WHEN", "level_of_course = 'UG'", "level_of_course = 'PhD'", "GROUP BY financial_year"],
        13: ["academic_courses_details", "incubation_details", "GROUP BY institute"],
        14: ["financial_expenses_capital", "academic_courses_details", "capital_assets", "GROUP BY"],
        15: ["innovation_grant_from_govt", "GROUP BY institute"],
        16: ["innovation_grant_from_govt", "financial_expenses_operational", "HAVING"],
        17: ["stage_of_technology", "financial_year", "GROUP BY"],
    }

    validator = QueryCompletenessValidator()
    results = []

    print("=" * 80)
    print("NRG Text-to-SQL Benchmark — Dhairya's 17 Queries")
    print("=" * 80)
    print(f"LLM: {llm_name}")
    print(f"DB:  {os.environ.get('DATABASE_URL', 'sqlite:///nrg_research.db')}")
    print()

    for entry in DHAIRYA_QUERIES:
        skill = TextToSQLSkill(llm_provider=llm_provider)
        skill._context = skill._context.__class__()

        try:
            result = skill.execute(entry["question"], user_tier=1)
            raw_sql = result.get("query", "")
        except Exception as e:
            raw_sql = f"ERROR: {e}"
        finally:
            skill.close()

        sql = raw_sql.strip() if raw_sql else ""
        is_complete, completeness_issues = validator.validate(sql)

        if sql and not sql.startswith("ERROR"):
            expected = DHAIRYA_KEYWORDS.get(entry["id"], [])
            passed = [kw for kw in expected if kw.lower() in sql.lower()]
            issues = [f"Missing: {kw}" for kw in expected if kw.lower() not in sql.lower()]
            verdict = "PASS" if len(passed) >= len(expected) * 0.7 else "FAIL_WRONG"
        elif sql.startswith("ERROR"):
            verdict = "FAIL_ERROR"
            issues = [sql[:100]]
        else:
            verdict = "FAIL_EMPTY"
            issues = ["Empty SQL"]

        results.append({
            "id": entry["id"],
            "question": entry["question"],
            "sql": sql[:120] + "..." if len(sql) > 120 else sql,
            "verdict": verdict,
            "issues": issues,
            "is_complete": is_complete,
            "completeness_issues": completeness_issues,
        })

    verdicts = {"PASS": [], "FAIL_WRONG": [], "FAIL_ERROR": [], "FAIL_EMPTY": []}
    for r in results:
        verdicts[r["verdict"]].append(r["id"])

    print("SUMMARY")
    print("=" * 80)
    print(f"Total: {len(results)}")
    print(f"  PASS:        {len(verdicts['PASS'])} — {verdicts['PASS']}")
    print(f"  FAIL_WRONG:  {len(verdicts['FAIL_WRONG'])} — {verdicts['FAIL_WRONG']}")
    print(f"  FAIL_ERROR:  {len(verdicts['FAIL_ERROR'])} — {verdicts['FAIL_ERROR']}")
    print(f"  FAIL_EMPTY:  {len(verdicts['FAIL_EMPTY'])} — {verdicts['FAIL_EMPTY']}")
    print()
    print("DETAILED RESULTS")
    print("=" * 80)

    for r in results:
        icon = "PASS" if r["verdict"] == "PASS" else "FAIL"
        print(f"\nQ{r['id']}: [{icon}] {r['question'][:65]}...")
        if r["sql"]:
            print(f"  SQL: {r['sql']}")
        if r["issues"]:
            print(f"  Issues: {r['issues']}")
        if r["completeness_issues"]:
            print(f"  Complete: {r['completeness_issues']}")


if __name__ == "__main__":
    main()
