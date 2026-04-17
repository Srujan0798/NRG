#!/usr/bin/env python3
"""
Connection management utilities for databases
"""

import logging
from typing import Dict, Any, Optional, ContextManager
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage database connections for ETL pipeline"""

    def __init__(self):
        self.connections = {}

    def get_postgres_connection(self, connection_string: str):
        """Get PostgreSQL connection"""
        try:
            import psycopg2

            conn = psycopg2.connect(connection_string)
            logger.info("Created PostgreSQL connection")
            return conn
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection: {e}")
            raise

    def get_neo4j_connection(self, uri: str, username: str, password: str):
        """Get Neo4j connection"""
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(uri, auth=(username, password))
            logger.info("Created Neo4j connection")
            return driver
        except Exception as e:
            logger.error(f"Failed to create Neo4j connection: {e}")
            raise

    def get_qdrant_connection(self, host: str, port: int):
        """Get Qdrant connection"""
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(host=host, port=port)
            logger.info("Created Qdrant connection")
            return client
        except Exception as e:
            logger.error(f"Failed to create Qdrant connection: {e}")
            raise

    def get_redis_connection(self, host: str, port: int, db: int = 0):
        """Get Redis connection"""
        try:
            import redis

            client = redis.Redis(host=host, port=port, db=db)
            logger.info("Created Redis connection")
            return client
        except Exception as e:
            logger.error(f"Failed to create Redis connection: {e}")
            raise

    @contextmanager
    def managed_postgres_connection(self, connection_string: str):
        """Context manager for PostgreSQL connection"""
        conn = None
        try:
            conn = self.get_postgres_connection(connection_string)
            yield conn
        finally:
            if conn:
                conn.close()
                logger.info("Closed PostgreSQL connection")


if __name__ == "__main__":
    manager = ConnectionManager()
    logger.info("Connection manager initialized")
