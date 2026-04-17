#!/usr/bin/env python3
"""
IITGN Institutional Load Test Suite
=====================================
Tests rate limiting, DDoS protection, and system stability under load.

Usage:
    python3 scripts/load_test.py --endpoint http://localhost:8000/query \
        --tokens 100 --concurrent 10 --duration 60
"""

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import aiohttp
import requests

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.auth.jwt_handler import JWTHandler


@dataclass
class LoadTestConfig:
    endpoint: str
    total_tokens: int = 100
    concurrent_requests: int = 10
    duration_seconds: int = 60
    test_type: str = "mixed"  # normal, burst, ddos, sustained


@dataclass
class TestResult:
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    rate_limited: int = 0
    dlp_blocked: int = 0
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0.0
    errors: list = field(default_factory=list)
    response_times: list = field(default_factory=list)


class IITGNLoadTester:
    """Institutional-scale load testing framework."""
    
    COLORS = {
        'GREEN': '\033[92m',
        'RED': '\033[91m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'CYAN': '\033[96m',
        'RESET': '\033[0m',
        'BOLD': '\033[1m'
    }
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.result = TestResult()
        self.tokens = []
        self._generate_tokens()
    
    def _generate_tokens(self):
        """Generate JWT tokens for testing."""
        print(f"{self.COLORS['CYAN']}Generating {self.config.total_tokens} test tokens...{self.COLORS['RESET']}")
        
        try:
            handler = JWTHandler(algorithm="RS256")
            
            roles = ["researcher", "government", "industry"]
            
            for i in range(self.config.total_tokens):
                role = roles[i % len(roles)]
                user = {
                    "user_id": f"load-test-user-{i}",
                    "username": f"{role}_user",
                    "role": role,
                    "tier": i % 3 + 1,
                    "groups": [role],
                    "scope": "test"
                }
                
                tokens = handler.issue_token_pair(user)
                self.tokens.append(tokens["access_token"])
            
            print(f"{self.COLORS['GREEN']}✓ Generated {len(self.tokens)} tokens{self.COLORS['RESET']}")
            
        except Exception as e:
            print(f"{self.COLORS['RED']}✗ Token generation failed: {e}{self.COLORS['RESET']}")
            sys.exit(1)
    
    async def _make_request(self, session: aiohttp.ClientSession, token: str, query: str) -> dict:
        """Make single request with timing."""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Request-ID": f"load-test-{time.time()}"
        }
        
        start_time = time.time()
        try:
            async with session.post(
                self.config.endpoint,
                headers=headers,
                json={"query": query},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_time = (time.time() - start_time) * 1000
                return {
                    "status": response.status,
                    "response_time": response_time,
                    "body": await response.text()
                }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "status": 0,
                "response_time": response_time,
                "error": str(e)
            }
    
    async def _run_concurrent_batch(self, batch_size: int):
        """Run concurrent batch of requests."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(batch_size):
                token = self.tokens[self.result.total_requests % len(self.tokens)]
                
                # Mix of query types
                if self.result.total_requests % 10 == 0:
                    query = "What is quantum computing research in India?"
                elif self.result.total_requests % 15 == 0:
                    query = "Show me AI research papers from IITGN"
                else:
                    query = f"Test query {self.result.total_requests}"
                
                task = self._make_request(session, token, query)
                tasks.append(task)
                self.result.total_requests += 1
            
            results = await asyncio.gather(*tasks)
            
            for res in results:
                self.result.response_times.append(res["response_time"])
                
                if res["status"] == 200:
                    self.result.successful += 1
                elif res["status"] == 429:
                    self.result.rate_limited += 1
                elif res["status"] == 400 and "DLP" in res.get("body", ""):
                    self.result.dlp_blocked += 1
                    self.result.successful += 1  # DLP blocking is expected
                elif res["status"] == 0:
                    self.result.failed += 1
                    self.result.errors.append(res.get("error", "Unknown error"))
                else:
                    self.result.failed += 1
    
    def run_load_test(self) -> TestResult:
        """Execute load test."""
        print(f"\n{self.COLORS['BOLD']}{self.COLORS['BLUE']}")
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║         IITGN INSTITUTIONAL LOAD TEST                    ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print(f"{self.COLORS['RESET']}")
        
        print(f"{self.COLORS['CYAN']}Configuration:{self.COLORS['RESET']}")
        print(f"  Endpoint: {self.config.endpoint}")
        print(f"  Duration: {self.config.duration_seconds}s")
        print(f"  Concurrent: {self.config.concurrent_requests}")
        print(f"  Total Tokens: {self.config.total_tokens}")
        print()
        
        start_time = time.time()
        batch_count = 0
        
        # Run for specified duration
        while time.time() - start_time < self.config.duration_seconds:
            batch_count += 1
            print(f"{self.COLORS['YELLOW']}Batch {batch_count}...{self.COLORS['RESET']}", end=" ", flush=True)
            
            asyncio.run(self._run_concurrent_batch(self.config.concurrent_requests))
            
            elapsed = time.time() - start_time
            print(f"{self.COLORS['GREEN']}✓{self.COLORS['RESET']} ({elapsed:.1f}s)")
            
            # Small delay between batches
            time.sleep(0.5)
        
        # Calculate statistics
        if self.result.response_times:
            self.result.avg_response_time_ms = sum(self.result.response_times) / len(self.result.response_times)
            self.result.min_response_time_ms = min(self.result.response_times)
            self.result.max_response_time_ms = max(self.result.response_times)
        
        return self.result
    
    def print_report(self):
        """Print comprehensive load test report."""
        print(f"\n{self.COLORS['BOLD']}{self.COLORS['BLUE']}")
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║              LOAD TEST RESULTS                           ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print(f"{self.COLORS['RESET']}")
        
        total = self.result.total_requests
        print(f"{self.COLORS['BOLD']}Total Requests:{self.COLORS['RESET']} {total}")
        print(f"{self.COLORS['GREEN']}✓ Successful:{self.COLORS['RESET']} {self.result.successful} ({self.result.successful/max(total,1)*100:.1f}%)")
        print(f"{self.COLORS['RED']}✗ Failed:{self.COLORS['RESET']} {self.result.failed} ({self.result.failed/max(total,1)*100:.1f}%)")
        print(f"{self.COLORS['YELLOW']}⚠ Rate Limited:{self.COLORS['RESET']} {self.result.rate_limited}")
        print(f"{self.COLORS['CYAN']}ℹ DLP Blocked:{self.COLORS['RESET']} {self.result.dlp_blocked}")
        
        print(f"\n{self.COLORS['BOLD']}Response Times:{self.COLORS['RESET']}")
        print(f"  Average: {self.result.avg_response_time_ms:.2f}ms")
        print(f"  Min: {self.result.min_response_time_ms:.2f}ms")
        print(f"  Max: {self.result.max_response_time_ms:.2f}ms")
        
        if self.result.errors:
            print(f"\n{self.COLORS['RED']}Errors (top 5):{self.COLORS['RESET']}")
            for error in self.result.errors[:5]:
                print(f"  - {error}")
        
        # Determine pass/fail
        success_rate = self.result.successful / max(total, 1) * 100
        print(f"\n{self.COLORS['BOLD']}SUCCESS RATE: {success_rate:.1f}%{self.COLORS['RESET']}")
        
        if success_rate >= 95:
            print(f"{self.COLORS['GREEN']}✅ LOAD TEST PASSED{self.COLORS['RESET']}")
        else:
            print(f"{self.COLORS['RED']}❌ LOAD TEST FAILED{self.COLORS['RESET']}")


def main():
    parser = argparse.ArgumentParser(description="IITGN Institutional Load Test")
    parser.add_argument("--endpoint", default="http://localhost:8000/query",
                       help="API endpoint to test")
    parser.add_argument("--tokens", type=int, default=100,
                       help="Number of JWT tokens to generate")
    parser.add_argument("--concurrent", type=int, default=10,
                       help="Number of concurrent requests")
    parser.add_argument("--duration", type=int, default=60,
                       help="Test duration in seconds")
    parser.add_argument("--type", default="mixed",
                       choices=["normal", "burst", "ddos", "sustained"],
                       help="Test type")
    
    args = parser.parse_args()
    
    config = LoadTestConfig(
        endpoint=args.endpoint,
        total_tokens=args.tokens,
        concurrent_requests=args.concurrent,
        duration_seconds=args.duration,
        test_type=args.type
    )
    
    tester = IITGNLoadTester(config)
    result = tester.run_load_test()
    tester.print_report()
    
    return 0 if result.successful / max(result.total_requests, 1) >= 0.95 else 1


if __name__ == "__main__":
    sys.exit(main())
