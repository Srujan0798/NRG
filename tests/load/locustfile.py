"""Load testing for NRG — C4: P99<500ms @ 1000 concurrent users.

Usage:
    locust -f tests/load/locustfile.py --headless \\
        -u 1000 -r 100 --run-time 5m \\
        --host http://localhost:8000 \\
        --html .cache/locust_report.html --csv evidence/02_load_stats

P99 assertion (run after):
    python -c "from tests.load.slo_validator import validate; validate()"
"""

from locust import HttpUser, task, between, events
import os
import random
import time

P99_THRESHOLD_MS = 500
SUCCESS_RATE_THRESHOLD = 0.95
_query_durations_ms: list[float] = []


class AuthenticatedNRGUser(HttpUser):
    abstract = True
    username_env = ""
    password_env = ""
    token_env = ""
    default_username = ""
    default_password = ""

    def on_start(self):
        preissued_token = os.environ.get(self.token_env) if self.token_env else None
        if preissued_token:
            self.token = preissued_token
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.client.headers.update(self.headers)
            return

        username = os.environ.get(self.username_env, self.default_username)
        password = os.environ.get(self.password_env, self.default_password)
        response = self.client.post("/login", json={
            "username": username,
            "password": password,
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token") or data.get("token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.client.headers.update(self.headers)
        else:
            self.headers = {}
            if self.environment.runner:
                self.environment.runner.quit()

    def _do_query(self, query_text: str):
        started_at = time.perf_counter()
        with self.client.post(
            "/query",
            headers=self.headers,
            json={"query": query_text, "question": query_text, "session_id": "load-test"},
            catch_response=True,
            name="/query",
        ) as resp:
            response_time_ms = (time.perf_counter() - started_at) * 1000
            if response_time_ms > 0:
                _query_durations_ms.append(float(response_time_ms))
            if resp.status_code in (200, 429):
                resp.success()
            else:
                resp.failure(f"Status {resp.status_code}")


class ResearcherUser(AuthenticatedNRGUser):
    """Tier 1 — Researcher persona. Full access, institution details."""
    wait_time = between(1, 4)
    weight = 6
    username_env = "LOAD_TEST_RESEARCHER_USER"
    password_env = "LOAD_TEST_RESEARCHER_PASS"
    token_env = "LOAD_TEST_RESEARCHER_TOKEN"
    default_username = "researcher_user"
    default_password = "researcher-pass"

    @task(10)
    def query_researchers(self):
        """Tier 1 query — simple researcher lookup."""
        queries = [
            "find robotics researchers in Gujarat",
            "AI researchers in Karnataka",
            "publications on machine learning",
            "labs working on renewable energy",
            "funding for IIT Bombay projects",
            "researchers working on quantum computing",
            "publications from IIT Delhi in 2024",
            "top researchers in cybersecurity",
        ]
        self._do_query(random.choice(queries))

    @task(4)
    def query_publications(self):
        """Tier 1 query — publications."""
        queries = [
            "publication counts by institution for 2024",
            "top AI venues in 2024",
            "research output of IITs",
        ]
        self._do_query(random.choice(queries))

    @task(2)
    def query_funding(self):
        """Tier 1 query — funding."""
        queries = [
            "total funding by ministry",
            "DST grants in 2024",
            "research funding by state",
        ]
        self._do_query(random.choice(queries))

    @task(1)
    def health_check(self):
        """Health endpoint."""
        self.client.get("/health/all", headers=self.headers, name="/health/all")


class GovernmentUser(AuthenticatedNRGUser):
    """Tier 2 — Government persona. Aggregated stats, policy view."""
    wait_time = between(2, 8)
    weight = 2
    username_env = "LOAD_TEST_GOV_USER"
    password_env = "LOAD_TEST_GOV_PASS"
    token_env = "LOAD_TEST_GOV_TOKEN"
    default_username = "gov_user"
    default_password = "government-pass"

    @task(8)
    def aggregate_stats(self):
        """Tier 2 aggregate query."""
        queries = [
            "total researchers by state",
            "funding trends by year",
            "publication counts by institution",
            "state-wise research output",
            "ministry-wise funding distribution",
        ]
        self._do_query(random.choice(queries))

    @task(3)
    def policy_view(self):
        """Tier 2 policy-oriented query."""
        queries = [
            "research areas with most funding",
            "collaboration patterns between institutions",
            "patent trends by sector",
        ]
        self._do_query(random.choice(queries))

    @task(1)
    def health_check(self):
        self.client.get("/health/all", headers=self.headers, name="/health/all")


class IndustryUser(AuthenticatedNRGUser):
    """Tier 3 — Industry persona. Limited, anonymized data."""
    wait_time = between(3, 12)
    weight = 1
    username_env = "LOAD_TEST_INDUSTRY_USER"
    password_env = "LOAD_TEST_INDUSTRY_PASS"
    token_env = "LOAD_TEST_INDUSTRY_TOKEN"
    default_username = "industry_user"
    default_password = "industry-pass"

    @task(6)
    def partnership_query(self):
        """Tier 3 partnership/opportunity query."""
        queries = [
            "labs with industry partnerships",
            "patent opportunities in AI",
            "technology transfer candidates",
            "collaboration opportunities with IITs",
        ]
        self._do_query(random.choice(queries))

    @task(2)
    def anonymized_stats(self):
        """Tier 3 anonymized aggregate."""
        queries = [
            "anonymized researcher counts by domain",
            "aggregate funding statistics",
        ]
        self._do_query(random.choice(queries))

    @task(1)
    def health_check(self):
        self.client.get("/health/all", headers=self.headers, name="/health/all")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Validate P99 after load test completes."""
    if not _query_durations_ms:
        print("\n⚠️  No query durations recorded")
        return

    durations = sorted(_query_durations_ms)
    p50 = durations[int(len(durations) * 0.50)]
    p95 = durations[int(len(durations) * 0.95)]
    p99 = durations[int(len(durations) * 0.99)]
    p999 = durations[int(len(durations) * 0.999)] if len(durations) >= 1000 else durations[-1]

    print(f"\n{'='*60}")
    print(f"C4 LOAD TEST RESULTS — P99 < {P99_THRESHOLD_MS}ms @ 1000 concurrent")
    print(f"{'='*60}")
    print(f"  Total queries:    {len(durations)}")
    print(f"  P50 (median):     {p50:.1f}ms")
    print(f"  P95:              {p95:.1f}ms")
    print(f"  P99:              {p99:.1f}ms  ← TARGET: <{P99_THRESHOLD_MS}ms")
    print(f"  P99.9:            {p999:.1f}ms")
    print(f"  Max:              {max(durations):.1f}ms")

    status = "✅ PASS" if p99 < P99_THRESHOLD_MS else "❌ FAIL"
    print(f"  Result:           {status}")

    if p99 >= P99_THRESHOLD_MS:
        print(f"\n  ⚠️  P99 ({p99:.1f}ms) exceeds threshold ({P99_THRESHOLD_MS}ms)")
        print(f"  Suggestions:")
        print(f"    - Enable Redis caching (rate limiting reduces DB load)")
        print(f"    - Scale API replicas: kubectl scale deploy/api --replicas=3")
        print(f"    - Enable query result caching in CostGuard")
        print(f"    - Check Qdrant latency at :6333/dashboard")

    print(f"{'='*60}\n")
