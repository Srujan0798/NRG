#!/usr/bin/env python3
"""User Acceptance Testing (UAT) for Government Persona."""

from tests.uat.researcher_scenarios import ResearcherUAT


class GovernmentUAT(ResearcherUAT):
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url=base_url)
        self.tier = "tier2"
        self.persona_name = "government"
        self.test_scenarios = [
            {"query": "What is the total research funding allocated to all IITs in 2024?", "expected_contains": ["funding", "iit", "2024"], "category": "funding_analysis"},
            {"query": "Compare research output between Gujarat and Maharashtra institutions", "expected_contains": ["gujarat", "maharashtra"], "category": "state_comparison"},
            {"query": "What are the trending research areas across Indian institutions?", "expected_contains": ["research areas", "indian"], "category": "trends_report"},
            {"query": "Show funding distribution by state for the last fiscal year", "expected_contains": ["funding", "state"], "category": "funding_analysis"},
            {"query": "What is the research productivity index of all NITs?", "expected_contains": ["research", "nits"], "category": "metrics_report"},
            {"query": "Compare patent filings between IITs over the last 5 years", "expected_contains": ["patent", "iits"], "category": "ip_analysis"},
            {"query": "What is the funding utilization rate by institution type?", "expected_contains": ["funding", "institution"], "category": "funding_analysis"},
            {"query": "Show regional distribution of research funding across India", "expected_contains": ["funding", "india"], "category": "geographic_analysis"},
            {"query": "What is the return on research investment by state?", "expected_contains": ["research", "investment"], "category": "roi_analysis"},
            {"query": "Compare research impact of centrally funded vs state institutions", "expected_contains": ["impact", "state"], "category": "comparison"},
            {"query": "What is the growth rate of research publications in India?", "expected_contains": ["publications", "india"], "category": "trends_report"},
            {"query": "Show industry-academia collaboration statistics", "expected_contains": ["industry", "collaboration"], "category": "partnership_analysis"},
            {"query": "What is the research output by domain across all institutions?", "expected_contains": ["research output", "institutions"], "category": "metrics_report"},
            {"query": "Compare funding allocation between public and private institutions", "expected_contains": ["funding", "public", "private"], "category": "comparison"},
            {"query": "Show research impact scores by institution", "expected_contains": ["impact", "institution"], "category": "metrics_report"},
        ]


def run_government_uat():
    tester = GovernmentUAT()
    results = tester.run_all_scenarios()
    print(f"\nGovernment UAT Results:\n  Total scenarios: {results['total_scenarios']}\n  Successful: {results['successful']}/{results['total_scenarios']}\n  Success rate: {results['success_rate'] * 100:.1f}%\n  Avg response time: {results['avg_response_time']:.2f}s")
    return results["success_rate"] >= 0.90


if __name__ == "__main__":
    raise SystemExit(0 if run_government_uat() else 1)
