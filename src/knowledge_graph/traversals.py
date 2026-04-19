#!/usr/bin/env python3
# Phase 2: Neo4j integration — not yet connected to orchestration pipeline
"""
Knowledge Graph Traversal Queries for National Researcher Graph
Production-grade implementation of common traversal patterns

NOTE: This module is standalone and not yet integrated into the query pipeline.
Phase 2 will connect it to the LangGraph orchestration for graph-based queries.
"""

import logging
import sys
from typing import List, Dict, Any, Optional
import time

# Neo4j driver
try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import Neo4jError
except ImportError:
    print("neo4j package not available. Install with: pip install neo4j")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("knowledge_graph_traversals.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class KnowledgeGraphTraversals:
    """Production-grade knowledge graph traversal queries"""

    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.database = database

    def close(self) -> None:
        """Close database connection"""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")

    def find_collaborators(
        self, researcher_id: str, max_hops: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find direct and 2-hop collaborators for a researcher

        Args:
            researcher_id: Researcher ID to find collaborators for
            max_hops: Maximum number of hops to traverse (default: 2)

        Returns:
            List of collaborator dictionaries with relationship details
        """
        query = f"""
        MATCH (r:Researcher {{researcher_id: $researcher_id}})
        CALL apoc.path.subgraphAll(r, {{
            relationshipFilter: "COLLABORATES_WITH|AUTHORED",
            maxLevel: {max_hops}
        }})
        YIELD nodes, relationships
        UNWIND nodes AS collaborator
        WITH collaborator
        WHERE collaborator.researcher_id <> $researcher_id
        MATCH (collaborator)-[:AFFILIATED_WITH]->(i:Institution)
        RETURN 
            collaborator.researcher_id AS researcher_id,
            collaborator.name AS name,
            collaborator.research_area AS research_area,
            i.name AS institution,
            i.state AS state
        """

        with self.driver.session(database=self.database) as session:
            try:
                start_time = time.time()
                result = session.run(query, researcher_id=researcher_id)
                collaborators = [record.data() for record in result]
                elapsed_time = time.time() - start_time

                logger.info(
                    f"find_collaborators query executed in {elapsed_time * 1000:.2f}ms, "
                    f"returned {len(collaborators)} collaborators"
                )
                return collaborators
            except Exception as e:
                logger.error(f"find_collaborators query failed: {e}")
                return []

    def topic_cluster(self, topic: str) -> Dict[str, Any]:
        """
        Find all researchers and labs in a topic area

        Args:
            topic: Research topic/keyword to search for

        Returns:
            Dictionary with researchers and labs in the topic area
        """
        query = """
        MATCH (k:Keyword {keyword: $topic})<-[:INTERESTED_IN|HAS_KEYWORD]-(r:Researcher)
        OPTIONAL MATCH (r)-[:AFFILIATED_WITH]->(i:Institution)
        OPTIONAL MATCH (r)-[:MEMBER_OF]->(l:Lab)
        WITH r, i, l, k
        OPTIONAL MATCH (l)-[:SPECIALIZES_IN]->(k2:Keyword {keyword: $topic})
        RETURN 
            r.researcher_id AS researcher_id,
            r.name AS researcher_name,
            r.research_area AS research_area,
            i.name AS institution,
            l.name AS lab_name,
            collect(DISTINCT k.keyword) AS keywords
        """

        with self.driver.session(database=self.database) as session:
            try:
                start_time = time.time()
                result = session.run(query, topic=topic)
                researchers = [record.data() for record in result]
                elapsed_time = time.time() - start_time

                # Also get labs in topic
                lab_query = """
                MATCH (k:Keyword {keyword: $topic})<-[:SPECIALIZES_IN]-(l:Lab)
                OPTIONAL MATCH (l)-[:LOCATED_AT]->(i:Institution)
                RETURN 
                    l.lab_id AS lab_id,
                    l.name AS lab_name,
                    i.name AS institution,
                    l.research_area AS research_area
                """

                result = session.run(lab_query, topic=topic)
                labs = [record.data() for record in result]

                logger.info(
                    f"topic_cluster query executed in {elapsed_time * 1000:.2f}ms, "
                    f"returned {len(researchers)} researchers and {len(labs)} labs"
                )

                return {"researchers": researchers, "labs": labs, "topic": topic}
            except Exception as e:
                logger.error(f"topic_cluster query failed: {e}")
                return {"researchers": [], "labs": [], "topic": topic}

    def funding_trail(self, institution_id: str) -> List[Dict[str, Any]]:
        """
        Get funding sources, amounts, and timelines for an institution

        Args:
            institution_id: Institution ID to get funding trail for

        Returns:
            List of funding records
        """
        query = """
        MATCH (i:Institution {institution_id: $institution_id})<-[:ADMINISTERED_BY]-(f:Funding)-[:FUNDED_BY]->(r:Researcher)
        OPTIONAL MATCH (f)-[:FUNDED_BY]->(a:Agency)
        RETURN 
            f.funding_id AS funding_id,
            f.amount AS amount,
            f.start_date AS start_date,
            f.end_date AS end_date,
            f.title AS title,
            f.agency AS agency,
            r.name AS researcher_name,
            r.research_area AS research_area,
            count(f) AS project_count
        ORDER BY f.start_date DESC
        """

        with self.driver.session(database=self.database) as session:
            try:
                start_time = time.time()
                result = session.run(query, institution_id=institution_id)
                funding_records = [record.data() for record in result]
                elapsed_time = time.time() - start_time

                logger.info(
                    f"funding_trail query executed in {elapsed_time * 1000:.2f}ms, "
                    f"returned {len(funding_records)} funding records"
                )
                return funding_records
            except Exception as e:
                logger.error(f"funding_trail query failed: {e}")
                return []

    def capability_map(self, technology: str) -> List[Dict[str, Any]]:
        """
        Find institutions and researchers with relevant expertise in a technology

        Args:
            technology: Technology keyword to search for

        Returns:
            List of institutions and researchers with relevant expertise
        """
        query = """
        MATCH (k:Keyword {keyword: $technology})<-[:HAS_KEYWORD|INTERESTED_IN]-(p:Publication|Researcher)-[:AUTHORED|INTERESTED_IN]->(r:Researcher)
        OPTIONAL MATCH (r)-[:AFFILIATED_WITH]->(i:Institution)
        RETURN DISTINCT
            r.researcher_id AS researcher_id,
            r.name AS researcher_name,
            r.research_area AS research_area,
            i.name AS institution,
            i.state AS state,
            count(p) AS publication_count
        ORDER BY publication_count DESC
        """

        with self.driver.session(database=self.database) as session:
            try:
                start_time = time.time()
                result = session.run(query, technology=technology)
                capabilities = [record.data() for record in result]
                elapsed_time = time.time() - start_time

                logger.info(
                    f"capability_map query executed in {elapsed_time * 1000:.2f}ms, "
                    f"returned {len(capabilities)} capability records"
                )
                return capabilities
            except Exception as e:
                logger.error(f"capability_map query failed: {e}")
                return []

    def cross_institutional_overlap(
        self, inst_a_id: str, inst_b_id: str
    ) -> Dict[str, Any]:
        """
        Find shared topics and people between two institutions

        Args:
            inst_a_id: First institution ID
            inst_b_id: Second institution ID

        Returns:
            Dictionary with shared topics and researchers
        """
        query = """
        MATCH (ia:Institution {institution_id: $inst_a_id})<-[:AFFILIATED_WITH]-(ra:Researcher)-[:INTERESTED_IN]->(k:Keyword)
        MATCH (ib:Institution {institution_id: $inst_b_id})<-[:AFFILIATED_WITH]-(rb:Researcher)-[:INTERESTED_IN]->(k)
        WITH k, collect(DISTINCT ra) AS researchers_a, collect(DISTINCT rb) AS researchers_b
        WHERE size(researchers_a) > 0 AND size(researchers_b) > 0
        UNWIND researchers_a AS researcher_a
        UNWIND researchers_b AS researcher_b
        MATCH (researcher_a)-[:AFFILIATED_WITH]->(ia)
        MATCH (researcher_b)-[:AFFILIATED_WITH]->(ib)
        RETURN 
            k.keyword AS shared_topic,
            collect(DISTINCT researcher_a.name) AS institution_a_researchers,
            collect(DISTINCT researcher_b.name) AS institution_b_researchers,
            count(DISTINCT researcher_a) AS count_a,
            count(DISTINCT researcher_b) AS count_b
        ORDER BY count_a + count_b DESC
        """

        with self.driver.session(database=self.database) as session:
            try:
                start_time = time.time()
                result = session.run(query, inst_a_id=inst_a_id, inst_b_id=inst_b_id)
                shared_data = [record.data() for record in result]
                elapsed_time = time.time() - start_time

                logger.info(
                    f"cross_institutional_overlap query executed in {elapsed_time * 1000:.2f}ms"
                )
                return {
                    "shared_data": shared_data,
                    "institution_a_id": inst_a_id,
                    "institution_b_id": inst_b_id,
                }
            except Exception as e:
                logger.error(f"cross_institutional_overlap query failed: {e}")
                return {
                    "shared_data": [],
                    "institution_a_id": inst_a_id,
                    "institution_b_id": inst_b_id,
                }

    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all traversal pattern tests to validate performance

        Returns:
            Dictionary with test results and performance metrics
        """
        logger.info("Running all knowledge graph traversal tests...")
        results = {}

        # Test 1: find_collaborators
        start_time = time.time()
        collaborators = self.find_collaborators("test_researcher_001")
        results["find_collaborators_time"] = time.time() - start_time
        results["find_collaborators_count"] = len(collaborators)

        # Test 2: topic_cluster
        start_time = time.time()
        topic_data = self.topic_cluster("machine learning")
        results["topic_cluster_time"] = time.time() - start_time
        results["topic_cluster_researchers"] = len(topic_data.get("researchers", []))
        results["topic_cluster_labs"] = len(topic_data.get("labs", []))

        # Test 3: funding_trail
        start_time = time.time()
        funding_data = self.funding_trail("test_institution_001")
        results["funding_trail_time"] = time.time() - start_time
        results["funding_trail_count"] = len(funding_data)

        # Test 4: capability_map
        start_time = time.time()
        capability_data = self.capability_map("artificial intelligence")
        results["capability_map_time"] = time.time() - start_time
        results["capability_map_count"] = len(capability_data)

        # Test 5: cross_institutional_overlap
        start_time = time.time()
        overlap_data = self.cross_institutional_overlap("inst_a", "inst_b")
        results["cross_institutional_overlap_time"] = time.time() - start_time
        results["cross_institutional_overlap_count"] = len(
            overlap_data.get("shared_data", [])
        )

        logger.info("All traversal tests completed successfully")
        return results


def main():
    """Main function for testing traversal patterns"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Knowledge Graph Traversal Patterns"
    )
    parser.add_argument("--neo4j-uri", required=True, help="Neo4j URI")
    parser.add_argument("--neo4j-user", required=True, help="Neo4j username")
    parser.add_argument("--neo4j-password", required=True, help="Neo4j password")
    parser.add_argument("--neo4j-database", default="neo4j", help="Neo4j database name")
    parser.add_argument(
        "--test-all", action="store_true", help="Run all traversal tests"
    )
    parser.add_argument(
        "--test-collaborators", action="store_true", help="Test find_collaborators"
    )
    parser.add_argument("--test-topic", action="store_true", help="Test topic_cluster")
    parser.add_argument(
        "--test-funding", action="store_true", help="Test funding_trail"
    )
    parser.add_argument(
        "--test-capability", action="store_true", help="Test capability_map"
    )
    parser.add_argument(
        "--test-overlap", action="store_true", help="Test cross_institutional_overlap"
    )

    args = parser.parse_args()

    # Create traversal instance
    kg_traversals = KnowledgeGraphTraversals(
        args.neo4j_uri, args.neo4j_user, args.neo4j_password, args.neo4j_database
    )

    try:
        if args.test_all or args.test_collaborators:
            logger.info("Testing find_collaborators...")
            collaborators = kg_traversals.find_collaborators("test_researcher_001")
            logger.info(f"Found {len(collaborators)} collaborators")

        if args.test_all or args.test_topic:
            logger.info("Testing topic_cluster...")
            topic_data = kg_traversals.topic_cluster("machine learning")
            logger.info(
                f"Found {len(topic_data.get('researchers', []))} researchers "
                f"and {len(topic_data.get('labs', []))} labs for topic"
            )

        if args.test_all or args.test_funding:
            logger.info("Testing funding_trail...")
            funding_data = kg_traversals.funding_trail("test_institution_001")
            logger.info(f"Found {len(funding_data)} funding records")

        if args.test_all or args.test_capability:
            logger.info("Testing capability_map...")
            capability_data = kg_traversals.capability_map("artificial intelligence")
            logger.info(f"Found {len(capability_data)} capability records")

        if args.test_all or args.test_overlap:
            logger.info("Testing cross_institutional_overlap...")
            overlap_data = kg_traversals.cross_institutional_overlap("inst_a", "inst_b")
            logger.info(
                f"Found {len(overlap_data.get('shared_data', []))} shared topics"
            )

        if args.test_all:
            logger.info("Running all traversal tests...")
            test_results = kg_traversals.run_all_tests()
            logger.info(f"Test results: {test_results}")

    except Exception as e:
        logger.error(f"Error running tests: {e}")
        sys.exit(1)
    finally:
        kg_traversals.close()


if __name__ == "__main__":
    main()
