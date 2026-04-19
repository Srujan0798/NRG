#!/usr/bin/env python3
"""Experimental Neo4j client for future knowledge graph queries.

This module is intentionally outside ``src``. Phase 1 uses SQL-backed graph
views; Neo4j remains optional future work behind ``FEATURE_KG=1``.
"""

import os
from typing import Any, Dict, List, Optional


class Neo4jClient:
    """Client for Neo4j graph database."""

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self._driver = None
        self.enabled = os.getenv("FEATURE_KG", "0") == "1"

        if self.enabled:
            try:
                from neo4j import GraphDatabase

                self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            except ImportError:
                print("Neo4j driver not installed. Run: pip install neo4j")
                self.enabled = False

    def close(self):
        """Close Neo4j connection."""
        if self._driver:
            self._driver.close()

    def is_available(self) -> bool:
        """Check if Neo4j is available."""
        if not self.enabled or not self._driver:
            return False
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    def find_coauthorship_path(
        self,
        researcher_a: str,
        researcher_b: str,
        max_depth: int = 5,
    ) -> Optional[List[Dict]]:
        """Find shortest co-authorship path between two researchers."""
        if not self.enabled:
            return None

        query = """
        MATCH path = shortestPath(
            (a:Researcher {researcher_id: $id_a})-[:COAUTHORS*1..%d]-(b:Researcher {researcher_id: $id_b})
        )
        RETURN [node in nodes(path) | {id: node.researcher_id, name: node.name}] as path_nodes,
               length(path) as distance
        """ % max_depth

        try:
            with self._driver.session() as session:
                result = session.run(query, id_a=researcher_a, id_b=researcher_b)
                record = result.single()
                if record:
                    return record["path_nodes"]
                return None
        except Exception as e:
            print(f"Neo4j query failed: {e}")
            return None

    def get_collaboration_network(self, researcher_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get collaboration network for a researcher."""
        if not self.enabled:
            return {"nodes": [], "edges": []}

        query = """
        MATCH (r:Researcher {researcher_id: $id})-[:COAUTHORS*1..%d]-(collaborator)
        RETURN r, collaborator, size((r)-[:COAUTHORS]-(collaborator)) as strength
        """ % depth

        nodes = {}
        edges = []

        try:
            with self._driver.session() as session:
                result = session.run(query, id=researcher_id)
                for record in result:
                    r = record["r"]
                    c = record["collaborator"]
                    strength = record["strength"]

                    nodes[r["researcher_id"]] = {
                        "id": r["researcher_id"],
                        "label": r.get("name", "Unknown"),
                        "type": "researcher",
                    }
                    nodes[c["researcher_id"]] = {
                        "id": c["researcher_id"],
                        "label": c.get("name", "Unknown"),
                        "type": "researcher",
                    }

                    edges.append(
                        {
                            "source": r["researcher_id"],
                            "target": c["researcher_id"],
                            "type": "coauthors",
                            "weight": strength,
                        }
                    )
        except Exception as e:
            print(f"Neo4j query failed: {e}")

        return {"nodes": list(nodes.values()), "edges": edges}

    def sync_from_postgres(self):
        """Placeholder for a future SQL-to-Neo4j sync job."""
        if not self.enabled:
            return
        print("Neo4j sync job placeholder")


def get_neo4j_client() -> Optional[Neo4jClient]:
    """Get Neo4j client if enabled."""
    if os.getenv("FEATURE_KG", "0") != "1":
        return None
    return Neo4jClient()
