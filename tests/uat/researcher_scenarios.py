#!/usr/bin/env python3
"""User Acceptance Testing (UAT) for persona query flows."""

import json
import time
from datetime import UTC, datetime
from typing import Dict, Tuple

import requests

from tests.uat.client import UATClient


class ResearcherUAT:
    """UAT test suite for researcher persona."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.tier = "tier1"
        self.persona_name = "researcher"
        self.client = UATClient(base_url=base_url)
        self.test_scenarios = [
            {"query": "Find researchers in machine learning at IIT Delhi", "expected_contains": ["machine learning", "iit delhi"], "category": "researcher_discovery"},
            {"query": "List publications by Dr. Amit Sharma in quantum computing", "expected_contains": ["quantum"], "category": "publication_discovery"},
            {"query": "Find collaborators for natural language processing research", "expected_contains": ["research"], "category": "collaboration"},
            {"query": "What research labs work on computer vision in India?", "expected_contains": ["computer vision", "india"], "category": "lab_discovery"},
            {"query": "Find funding opportunities for AI research in 2025", "expected_contains": ["ai", "2025"], "category": "funding_analysis"},
            {"query": "Who are the top researchers in deep learning?", "expected_contains": ["deep learning"], "category": "expertise_discovery"},
            {"query": "Find research papers on blockchain technology from IITs", "expected_contains": ["blockchain", "iit"], "category": "publication_discovery"},
            {"query": "What is the collaboration network between IIT Bombay and IIT Madras?", "expected_contains": ["iit bombay", "iit madras"], "category": "network_analysis"},
            {"query": "Find researchers working on quantum computing at Indian institutions", "expected_contains": ["quantum", "indian"], "category": "researcher_discovery"},
            {"query": "What are the recent publications in cybersecurity from Indian labs?", "expected_contains": ["cybersecurity", "recent"], "category": "publication_discovery"},
            {"query": "Find cross-institution research projects in data science", "expected_contains": ["data science"], "category": "project_discovery"},
            {"query": "Who are the leading researchers in neural networks?", "expected_contains": ["neural networks"], "category": "expertise_discovery"},
            {"query": "Find research groups working on robotics at IISc", "expected_contains": ["robotics", "iisc"], "category": "lab_discovery"},
            {"query": "What is the research output of NIT Trichy in the last 5 years?", "expected_contains": ["nit trichy"], "category": "metrics_analysis"},
            {"query": "Find collaborations between industry and academia in AI", "expected_contains": ["industry", "ai"], "category": "partnership_discovery"},
            {"query": "Who published papers on reinforcement learning in 2024?", "expected_contains": ["reinforcement learning", "2024"], "category": "publication_discovery"},
            {"query": "Find researcher profiles with expertise in computer graphics", "expected_contains": ["computer graphics"], "category": "expertise_discovery"},
            {"query": "What research areas are growing at IIT Kharagpur?", "expected_contains": ["research areas", "iit kharagpur"], "category": "trends_analysis"},
            {"query": "Find international collaborations in biotechnology research", "expected_contains": ["international", "biotechnology"], "category": "network_analysis"},
            {"query": "What patents have been filed by IIT researchers in AI?", "expected_contains": ["patents", "ai"], "category": "ip_discovery"},
        ]

    def run_scenario(self, scenario: Dict) -> Tuple[bool, str, float]:
        start_time = time.time()
        try:
            response = self.client.query_for_tier(scenario["query"], self.tier)
            response_time = time.time() - start_time
            if response.status_code != 200:
                return False, f"Error: {response.status_code} {response.text}", response_time
            response_text = json.dumps(response.json()).lower()
            success = all(term in response_text for term in scenario["expected_contains"])
            return success, response_text, response_time
        except requests.exceptions.RequestException as exc:
            return False, f"Runtime error: {exc}", 0

    def run_all_scenarios(self) -> Dict:
        print(f"Running {self.persona_name.title()} UAT scenarios...")
        results = []
        success_count = 0
        total_time = 0.0
        for i, scenario in enumerate(self.test_scenarios):
            print(f"  Testing scenario {i + 1}/20: {scenario['category']}")
            success, response_text, response_time = self.run_scenario(scenario)
            total_time += response_time
            if success:
                success_count += 1
            results.append({"query": scenario["query"], "category": scenario["category"], "success": success, "response_time": response_time})
        return {
            "persona": self.persona_name,
            "total_scenarios": len(self.test_scenarios),
            "successful": success_count,
            "success_rate": success_count / len(self.test_scenarios),
            "avg_response_time": total_time / len(self.test_scenarios),
            "results": results,
        }


def run_researcher_uat():
    tester = ResearcherUAT()
    results = tester.run_all_scenarios()
    print(f"\nResearcher UAT Results:\n  Total scenarios: {results['total_scenarios']}\n  Successful: {results['successful']}/{results['total_scenarios']}\n  Success rate: {results['success_rate'] * 100:.1f}%\n  Avg response time: {results['avg_response_time']:.2f}s")
    return results["success_rate"] >= 0.50


if __name__ == "__main__":
    raise SystemExit(0 if run_researcher_uat() else 1)
