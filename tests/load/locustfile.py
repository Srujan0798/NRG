"""Load testing for NRG using Locust."""

from locust import HttpUser, task, between
import random


class ResearcherUser(HttpUser):
    """Simulates a researcher persona."""
    wait_time = between(1, 5)
    weight = 3
    
    def on_start(self):
        """Login and get token."""
        response = self.client.post("/login", json={
            "username": "researcher_user",
            "password": "researcher-pass"
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(5)
    def query_researchers(self):
        """Query for researchers."""
        queries = [
            "find robotics researchers in Gujarat",
            "AI researchers in Karnataka",
            "publications on machine learning",
            "labs working on renewable energy",
            "funding for IIT Bombay projects"
        ]
        self.client.post("/query", 
            headers=self.headers,
            json={"query": random.choice(queries), "session_id": "load-test"}
        )
    
    @task(2)
    def get_stats(self):
        """Get dashboard stats."""
        self.client.get("/stats", headers=self.headers)
    
    @task(1)
    def get_graph_data(self):
        """Get graph visualization."""
        self.client.get("/query/graph?topic=machine%20learning", 
            headers=self.headers)


class GovernmentUser(HttpUser):
    """Simulates a government persona."""
    wait_time = between(2, 10)
    weight = 1
    
    def on_start(self):
        response = self.client.post("/login", json={
            "username": "gov_user",
            "password": "gov-pass"
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def aggregate_query(self):
        """Aggregate research statistics."""
        queries = [
            "total researchers by state",
            "funding trends by year",
            "publication counts by institution"
        ]
        self.client.post("/query",
            headers=self.headers,
            json={"query": random.choice(queries), "session_id": "load-test"}
        )


class IndustryUser(HttpUser):
    """Simulates an industry persona."""
    wait_time = between(3, 15)
    weight = 1
    
    def on_start(self):
        response = self.client.post("/login", json={
            "username": "industry_user",
            "password": "industry-pass"
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(2)
    def partnership_query(self):
        """Search for partnership opportunities."""
        queries = [
            "labs with industry partnerships",
            "patent opportunities in AI",
            "technology transfer candidates"
        ]
        self.client.post("/query",
            headers=self.headers,
            json={"query": random.choice(queries), "session_id": "load-test"}
        )
