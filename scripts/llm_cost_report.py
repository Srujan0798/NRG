#!/usr/bin/env python3
"""Weekly LLM Cost Report Generator — NRG CostGuard Budget Governance."""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = "nrg_research.db"
OUTPUT_DIR = Path("docs/ops")
WEEK_NUMBER = datetime.now().isocalendar()[1]
YEAR = datetime.now().year


def get_cost_breakdown() -> dict:
    conn = sqlite3.connect(DB_PATH)
    breakdown = {}

    monthly_total = conn.execute(
        "SELECT SUM(cost_inr) FROM llm_cost_log WHERE timestamp >= date('now', 'start of month')"
    ).fetchone()[0] or 0.0

    persona_breakdown = {}
    for row in conn.execute(
        """
        SELECT persona, SUM(cost_inr), COUNT(*), AVG(cost_inr)
        FROM llm_cost_log
        WHERE timestamp >= date('now', 'start of month')
        GROUP BY persona
        """
    ).fetchall():
        persona_breakdown[row[0]] = {"cost": row[1], "count": row[2], "avg": row[3]}

    provider_breakdown = {}
    for row in conn.execute(
        """
        SELECT provider, SUM(cost_inr), COUNT(*), AVG(cost_inr)
        FROM llm_cost_log
        WHERE timestamp >= date('now', 'start of month')
        GROUP BY provider
        """
    ).fetchall():
        provider_breakdown[row[0]] = {"cost": row[1], "count": row[2], "avg": row[3]}

    complexity_breakdown = {}
    fallback_events = {}
    for row in conn.execute(
        """
        SELECT complexity, SUM(cost_inr), COUNT(*), SUM(CASE WHEN route_decision LIKE '%fallback%' THEN 1 ELSE 0 END)
        FROM llm_cost_log
        WHERE timestamp >= date('now', 'start of month')
        GROUP BY complexity
        """
    ).fetchall():
        complexity_breakdown[row[0]] = {"cost": row[1], "count": row[2]}
        fallback_events[row[0]] = row[3]

    conn.close()
    return {
        "monthly_total": monthly_total,
        "persona": persona_breakdown,
        "provider": provider_breakdown,
        "complexity": complexity_breakdown,
        "fallback_events": fallback_events,
    }


def format_inr(amount: float) -> str:
    return f"₹{amount:,.2f}"


def generate_report() -> str:
    breakdown = get_cost_breakdown()
    monthly_budget = 500000.0
    spent = breakdown["monthly_total"]
    pct = (spent / monthly_budget) * 100
    projected = (spent / datetime.now().day) * 30 if datetime.now().day > 0 else 0

    status = "HEALTHY"
    if pct >= 95:
        status = "HALT"
    elif pct >= 85:
        status = "CRITICAL"
    elif pct >= 70:
        status = "WARNING"

    lines = [
        f"# LLM Cost Report — Week {WEEK_NUMBER}, {YEAR}",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Status:** {status}",
        f"",
        f"## Budget Overview",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Monthly Budget | {format_inr(monthly_budget)} |",
        f"| Spent This Month | {format_inr(spent)} ({pct:.1f}%) |",
        f"| Remaining | {format_inr(monthly_budget - spent)} |",
        f"| Projected Month-End | {format_inr(projected)} ({projected / monthly_budget * 100:.1f}%) |",
        f"| Alerts | {status} |",
        f"",
    ]

    if breakdown["persona"]:
        lines += [
            f"## By Persona",
            f"",
            f"| Tier | Queries | Cost | Avg/Query | % of Budget |",
            f"|------|---------|------|-----------|-------------|",
        ]
        for persona, data in breakdown["persona"].items():
            tier_pct = (data["cost"] / monthly_budget) * 100
            lines.append(f"| {persona.title()} | {data['count']} | {format_inr(data['cost'])} | {format_inr(data['avg'])} | {tier_pct:.1f}% |")
        lines.append("")

    if breakdown["provider"]:
        lines += [
            f"## By Provider",
            f"",
            f"| Provider | Queries | Cost | Avg/Query |",
            f"|----------|---------|------|-----------|",
        ]
        for provider, data in breakdown["provider"].items():
            lines.append(f"| {provider} | {data['count']} | {format_inr(data['cost'])} | {format_inr(data['avg'])} |")
        lines.append("")

    if breakdown["complexity"]:
        lines += [
            f"## By Complexity",
            f"",
            f"| Level | Queries | Cost | Avg |",
            f"|-------|---------|------|-----|",
        ]
        for complexity, data in breakdown["complexity"].items():
            avg = data["cost"] / data["count"] if data["count"] > 0 else 0
            lines.append(f"| {complexity} | {data['count']} | {format_inr(data['cost'])} | {format_inr(avg)} |")
        lines.append("")

    if status != "HEALTHY":
        lines += [
            f"## Action Required",
            f"",
            f"- **{status}**: Monthly spend has reached {pct:.1f}% of budget",
            f"- Consider optimizing routing to lower-cost providers",
            f"- Review critical-complexity query volume",
            f"",
        ]

    lines.append(f"> **Note:** This report auto-generates weekly. Last run: {datetime.now().isoformat()}")
    return "\n".join(lines)


def main():
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    report = generate_report()
    output_file = output_dir / f"LLM_COST_REPORT_{YEAR}-W{WEEK_NUMBER:02d}.md"
    output_file.write_text(report)
    print(f"Report written to: {output_file}")
    print()
    print(report)


if __name__ == "__main__":
    main()