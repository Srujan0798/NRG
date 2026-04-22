"""Query performance analysis - generate EXPLAIN plans for common queries.

This script analyzes the top 20 most common query patterns and generates
optimization recommendations based on EXPLAIN output.
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.database_v2 import NRGDatabase


TOP_COMMON_QUERIES = [
    {
        "name": "researchers_by_state",
        "query": "SELECT * FROM researchers WHERE state = 'Gujarat' AND research_area LIKE '%Robotics%' LIMIT 50",
        "frequency": "high",
    },
    {
        "name": "researchers_by_area",
        "query": "SELECT * FROM researchers WHERE research_area = 'Artificial Intelligence' LIMIT 100",
        "frequency": "high",
    },
    {
        "name": "publications_by_year",
        "query": "SELECT * FROM publications WHERE year = 2024 ORDER BY citations DESC LIMIT 20",
        "frequency": "high",
    },
    {
        "name": "publications_search",
        "query": "SELECT * FROM publications WHERE title LIKE '%machine learning%' AND abstract LIKE '%neural%' LIMIT 20",
        "frequency": "high",
    },
    {
        "name": "funding_by_researcher",
        "query": "SELECT * FROM funding_records WHERE researcher_id = ? LIMIT 50",
        "frequency": "high",
    },
    {
        "name": "labs_by_institution",
        "query": "SELECT * FROM labs WHERE institution_id = 'inst-123' LIMIT 50",
        "frequency": "medium",
    },
    {
        "name": "researcher_publications",
        "query": "SELECT p.* FROM publications p JOIN researcher_publications rp ON p.publication_id = rp.publication_id WHERE rp.researcher_id = ?",
        "frequency": "high",
    },
    {
        "name": "researcher_count_by_state",
        "query": "SELECT state, COUNT(*) FROM researchers GROUP BY state ORDER BY COUNT(*) DESC",
        "frequency": "medium",
    },
    {
        "name": "publication_count_by_year",
        "query": "SELECT year, COUNT(*) FROM publications GROUP BY year ORDER BY year DESC",
        "frequency": "medium",
    },
    {
        "name": "top_researchers_by_hindex",
        "query": "SELECT * FROM researchers WHERE h_index >= 30 ORDER BY h_index DESC LIMIT 50",
        "frequency": "high",
    },
    {
        "name": "institution_researchers",
        "query": "SELECT r.* FROM researchers r WHERE r.institution_id = ? ORDER BY r.h_index DESC",
        "frequency": "medium",
    },
    {
        "name": "recent_publications",
        "query": "SELECT * FROM publications WHERE year >= 2022 ORDER BY created_at DESC LIMIT 50",
        "frequency": "high",
    },
    {
        "name": "collaborations_by_country",
        "query": "SELECT * FROM collaborations WHERE partner_country = 'USA' LIMIT 50",
        "frequency": "low",
    },
    {
        "name": "projects_by_status",
        "query": "SELECT * FROM projects WHERE status = 'Active' LIMIT 50",
        "frequency": "medium",
    },
    {
        "name": "patents_by_inventor",
        "query": "SELECT * FROM patents WHERE inventor_ids LIKE '%researcher-123%' LIMIT 50",
        "frequency": "low",
    },
    {
        "name": "funding_by_agency",
        "query": "SELECT agency, SUM(amount) as total FROM funding_records GROUP BY agency ORDER BY total DESC",
        "frequency": "low",
    },
    {
        "name": "area_distribution",
        "query": "SELECT research_area, COUNT(*) FROM researchers GROUP BY research_area ORDER BY COUNT(*) DESC LIMIT 20",
        "frequency": "medium",
    },
    {
        "name": "researcher_labs",
        "query": "SELECT l.* FROM labs l JOIN researcher_labs rl ON l.lab_id = rl.lab_id WHERE rl.researcher_id = ?",
        "frequency": "medium",
    },
    {
        "name": "publication_citations",
        "query": "SELECT * FROM publications WHERE citations > 100 ORDER BY citations DESC LIMIT 100",
        "frequency": "medium",
    },
    {
        "name": "keyword_search",
        "query": "SELECT p.* FROM publications p JOIN publication_keywords pk ON p.publication_id = pk.publication_id WHERE pk.keyword_id = ?",
        "frequency": "low",
    },
]


def analyze_query(db: NRGDatabase, query_info: Dict) -> Dict[str, Any]:
    """Analyze a single query and return EXPLAIN results."""
    query = query_info["query"]

    try:
        explain_result = db.explain_query(query)
        plan = explain_result.get("plan", [])

        plan_text = " ".join([str(row) for row in plan]).lower()

        issues = []
        recommendations = []

        if "scan" in plan_text and "index" not in plan_text:
            issues.append("Full table scan detected")
            recommendations.append("Consider adding an index for this query pattern")

        if "1000" in plan_text or "10000" in plan_text:
            issues.append("Large number of rows processed")

        if "filesort" in plan_text or "sort" in plan_text:
            issues.append("External sort required")
            recommendations.append("Consider adding an index to avoid sorting")

        if "temp" in plan_text:
            issues.append("Temporary data structure used")
            recommendations.append("Query may benefit from materialized view")

        return {
            "name": query_info["name"],
            "query": query,
            "frequency": query_info["frequency"],
            "plan": plan,
            "issues": issues,
            "recommendations": recommendations,
            "status": "analyzed",
        }
    except Exception as e:
        return {
            "name": query_info["name"],
            "query": query,
            "frequency": query_info["frequency"],
            "plan": [],
            "issues": [f"Error analyzing query: {str(e)}"],
            "recommendations": [],
            "status": "error",
        }


def generate_optimization_report() -> Dict[str, Any]:
    """Generate comprehensive query optimization report."""
    db = NRGDatabase()

    report = {
        "generated_at": "2025-01-15",
        "database_dialect": db.dialect,
        "queries_analyzed": 0,
        "queries_with_issues": 0,
        "total_recommendations": 0,
        "query_analysis": [],
        "index_recommendations": set(),
        "materialized_view_recommendations": set(),
    }

    for query_info in TOP_COMMON_QUERIES:
        analysis = analyze_query(db, query_info)
        report["queries_analyzed"] += 1

        if analysis["issues"]:
            report["queries_with_issues"] += 1

        report["total_recommendations"] += len(analysis["recommendations"])

        for rec in analysis["recommendations"]:
            if "index" in rec.lower():
                report["index_recommendations"].add(rec)
            if "materialized" in rec.lower():
                report["materialized_view_recommendations"].add(rec)

        report["query_analysis"].append(analysis)

    report["index_recommendations"] = list(report["index_recommendations"])
    report["materialized_view_recommendations"] = list(report["materialized_view_recommendations"])

    return report


def print_report(report: Dict) -> None:
    """Print a formatted optimization report."""
    print("=" * 80)
    print("NRG DATABASE QUERY PERFORMANCE ANALYSIS REPORT")
    print("=" * 80)
    print(f"\nGenerated: {report['generated_at']}")
    print(f"Database Dialect: {report['database_dialect']}")
    print(f"\nQueries Analyzed: {report['queries_analyzed']}")
    print(f"Queries with Issues: {report['queries_with_issues']}")
    print(f"Total Recommendations: {report['total_recommendations']}")

    print("\n" + "-" * 80)
    print("QUERIES REQUIRING ATTENTION")
    print("-" * 80)

    for qa in report["query_analysis"]:
        if qa["issues"]:
            print(f"\n[{qa['status'].upper()}] {qa['name']} ({qa['frequency']} frequency)")
            print(f"  Query: {qa['query'][:100]}...")
            print("  Issues:")
            for issue in qa["issues"]:
                print(f"    - {issue}")
            if qa["recommendations"]:
                print("  Recommendations:")
                for rec in qa["recommendations"]:
                    print(f"    - {rec}")

    if report["index_recommendations"]:
        print("\n" + "-" * 80)
        print("NEW INDEX RECOMMENDATIONS")
        print("-" * 80)
        for rec in report["index_recommendations"]:
            print(f"  - {rec}")

    if report["materialized_view_recommendations"]:
        print("\n" + "-" * 80)
        print("MATERIALIZED VIEW RECOMMENDATIONS")
        print("-" * 80)
        for rec in report["materialized_view_recommendations"]:
            print(f"  - {rec}")


if __name__ == "__main__":
    report = generate_optimization_report()
    print_report(report)

    output_path = Path(__file__).resolve().parents[1] / "docs" / "query_optimization_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n\nReport saved to: {output_path}")