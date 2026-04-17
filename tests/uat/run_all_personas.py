#!/usr/bin/env python3
"""
Combined User Acceptance Testing (UAT) Runner.
Runs UAT tests for all 3 personas and generates comprehensive report.
"""

import json
import sys
import os
from datetime import UTC, datetime
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.uat.researcher_scenarios import ResearcherUAT
from tests.uat.government_scenarios import GovernmentUAT
from tests.uat.industry_scenarios import IndustryUAT


def run_all_persona_uat(
    evaluate_with_llm: bool = False, success_threshold: float = 0.90
) -> Dict:
    """
    Run UAT tests for all 3 personas.

    Args:
        evaluate_with_llm: Whether to use LLM for response evaluation
        success_threshold: Minimum success rate to pass (default 0.90 = 90%)

    Returns:
        Comprehensive UAT results dictionary
    """
    print("=" * 60)
    print("USER ACCEPTANCE TESTING - ALL PERSONAS")
    print("=" * 60)

    results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "evaluate_with_llm": evaluate_with_llm,
        "success_threshold": success_threshold,
        "personas": {},
        "overall": {},
    }

    # Run researcher UAT
    print("\n[1/3] Running Researcher Persona UAT...")
    researcher_tester = ResearcherUAT()
    researcher_results = researcher_tester.run_all_scenarios()
    results["personas"]["researcher"] = researcher_results

    # Run government UAT
    print("\n[2/3] Running Government Persona UAT...")
    government_tester = GovernmentUAT()
    government_results = government_tester.run_all_scenarios()
    results["personas"]["government"] = government_results

    # Run industry UAT
    print("\n[3/3] Running Industry Persona UAT...")
    industry_tester = IndustryUAT()
    industry_results = industry_tester.run_all_scenarios()
    results["personas"]["industry"] = industry_results

    # Calculate overall metrics
    total_scenarios = (
        researcher_results["total_scenarios"]
        + government_results["total_scenarios"]
        + industry_results["total_scenarios"]
    )
    total_successful = (
        researcher_results["successful"]
        + government_results["successful"]
        + industry_results["successful"]
    )
    overall_success_rate = total_successful / total_scenarios
    avg_response_time = (
        researcher_results["avg_response_time"]
        + government_results["avg_response_time"]
        + industry_results["avg_response_time"]
    ) / 3

    results["overall"] = {
        "total_scenarios": total_scenarios,
        "total_successful": total_successful,
        "success_rate": overall_success_rate,
        "avg_response_time": avg_response_time,
        "passed": overall_success_rate >= success_threshold,
    }

    # Print summary
    print("\n" + "=" * 60)
    print("UAT SUMMARY")
    print("=" * 60)
    print(
        f"\nResearcher: {researcher_results['successful']}/{researcher_results['total_scenarios']} "
        f"({researcher_results['success_rate'] * 100:.1f}%)"
    )
    print(
        f"Government: {government_results['successful']}/{government_results['total_scenarios']} "
        f"({government_results['success_rate'] * 100:.1f}%)"
    )
    print(
        f"Industry: {industry_results['successful']}/{industry_results['total_scenarios']} "
        f"({industry_results['success_rate'] * 100:.1f}%)"
    )
    print(
        f"\nOverall: {total_successful}/{total_scenarios} ({overall_success_rate * 100:.1f}%)"
    )
    print(f"Avg Response Time: {avg_response_time:.2f}s")

    if overall_success_rate >= success_threshold:
        print(f"\n✅ PASSED: ≥{success_threshold * 100:.0f}% success rate achieved!")
    else:
        print(f"\n❌ FAILED: Below {success_threshold * 100:.0f}% success rate")

    return results


def main():
    """Main UAT runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Run UAT for all personas")
    parser.add_argument(
        "--evaluate-with-llm",
        action="store_true",
        help="Use LLM for response evaluation",
    )
    parser.add_argument(
        "--success-threshold",
        type=float,
        default=0.90,
        help="Minimum success rate to pass (default 0.90)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/uat/uat_report_phase3.md",
        help="Output file for UAT report",
    )

    args = parser.parse_args()

    # Run UAT
    results = run_all_persona_uat(
        evaluate_with_llm=args.evaluate_with_llm,
        success_threshold=args.success_threshold,
    )

    # Save results to file
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save JSON results
    json_output = args.output.replace(".md", ".json")
    with open(json_output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nUAT results saved to {json_output}")

    if results["overall"]["passed"]:
        print("✅ UAT PASSED")
        return 0
    else:
        print("❌ UAT FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
