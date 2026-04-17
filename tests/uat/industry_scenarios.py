#!/usr/bin/env python3
"""User Acceptance Testing (UAT) for Industry Persona."""

from tests.uat.researcher_scenarios import ResearcherUAT


class IndustryUAT(ResearcherUAT):
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url=base_url)
        self.tier = "tier3"
        self.persona_name = "industry"
        self.test_scenarios = [
            {"query": "What AI capabilities do Indian research institutions offer?", "expected_contains": ["ai", "institutions"], "category": "capability_mapping"},
            {"query": "Find potential partnership opportunities in semiconductor research", "expected_contains": ["partnership", "semiconductor"], "category": "partnership_discovery"},
            {"query": "What is the Technology Readiness Level (TRL) of Indian quantum research?", "expected_contains": ["trl", "quantum"], "category": "trl_assessment"},
            {"query": "Find researchers working on electric vehicle technology", "expected_contains": ["electric vehicle"], "category": "talent_discovery"},
            {"query": "What are the emerging technologies from Indian labs?", "expected_contains": ["emerging", "technologies"], "category": "technology_scouting"},
            {"query": "Find industry-academia collaboration opportunities in biotech", "expected_contains": ["industry", "biotech"], "category": "partnership_discovery"},
            {"query": "What IP is available for licensing from IITs?", "expected_contains": ["ip", "iits"], "category": "ip_discovery"},
            {"query": "Find technical expertise in machine learning and AI", "expected_contains": ["machine learning", "ai"], "category": "capability_mapping"},
            {"query": "What are the research capabilities at IIT for EV technology?", "expected_contains": ["iit", "ev"], "category": "capability_mapping"},
            {"query": "Find potential R&D partners for semiconductor manufacturing", "expected_contains": ["r&d", "semiconductor"], "category": "partnership_discovery"},
            {"query": "What technologies are ready for commercial transfer?", "expected_contains": ["commercial", "transfer"], "category": "tech_transfer"},
            {"query": "Find research groups working on renewable energy", "expected_contains": ["renewable energy"], "category": "partner_discovery"},
            {"query": "What is the innovation index of Indian engineering institutions?", "expected_contains": ["innovation", "engineering"], "category": "metrics"},
            {"query": "Find expertise in advanced materials science", "expected_contains": ["materials science"], "category": "capability_mapping"},
            {"query": "What are the technology gaps in Indian research?", "expected_contains": ["technology", "india"], "category": "gap_analysis"},
        ]


def run_industry_uat():
    tester = IndustryUAT()
    results = tester.run_all_scenarios()
    print(f"\nIndustry UAT Results:\n  Total scenarios: {results['total_scenarios']}\n  Successful: {results['successful']}/{results['total_scenarios']}\n  Success rate: {results['success_rate'] * 100:.1f}%\n  Avg response time: {results['avg_response_time']:.2f}s")
    return results["success_rate"] >= 0.90


if __name__ == "__main__":
    raise SystemExit(0 if run_industry_uat() else 1)
