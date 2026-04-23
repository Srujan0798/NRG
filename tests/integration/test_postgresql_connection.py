"""
PostgreSQL connection integration tests.
Tests DatabaseManager pool behavior, connection handling, and failover.
"""
from __future__ import annotations

import os
import pytest
import time
from unittest.mock import patch, MagicMock

from src.config.database import (
    DatabaseManager,
    get_database_manager,
    PoolStats,
    DEFAULT_POOL_MIN,
    DEFAULT_POOL_MAX,
)


pytestmark = pytest.mark.skipif(
    not os.getenv("POSTGRES_DATABASE_URL"),
    reason="Requires POSTGRES_DATABASE_URL environment variable",
)


class TestDatabaseManagerInit:
    def test_detects_postgresql_driver(self):
        url = "postgresql://user:pass@localhost:5432/nrg"
        dm = DatabaseManager(url)
        assert dm.driver == "postgresql"

    def test_detects_sqlite_driver(self):
        dm = DatabaseManager("sqlite:///test.db")
        assert dm.driver == "sqlite"

    def test_defaults_to_sqlite_when_no_url(self):
        dm = DatabaseManager("")
        assert dm.driver == "sqlite"

    def test_singleton_pattern(self):
        dm1 = DatabaseManager.get_instance()
        dm2 = DatabaseManager.get_instance()
        assert dm1 is dm2


class TestPostgresPool:
    def test_pool_initialized_with_config(self):
        url = os.getenv("POSTGRES_DATABASE_URL", "")
        dm = DatabaseManager(url)
        assert dm.driver == "postgresql"
        assert dm._pool is not None or dm.driver == "sqlite"

    def test_pool_stats_returns_valid_stats(self):
        url = os.getenv("POSTGRES_DATABASE_URL", "")
        dm = DatabaseManager(url)
        stats = dm.pool_stats()
        assert isinstance(stats, PoolStats)
        assert stats.max_size == DEFAULT_POOL_MAX
        assert stats.min_size == DEFAULT_POOL_MIN
        assert stats.active >= 0
        assert stats.idle >= 0


class TestPostgresConnection:
    def test_execute_insert_and_select(self):
        url = os.getenv("POSTGRES_DATABASE_URL", "")
        dm = DatabaseManager(url)
        if dm.driver != "postgresql":
            pytest.skip("PostgreSQL not available")

        test_key = f"pg_test_{int(time.time() * 1000)}"
        try:
            dm.execute(
                "CREATE TABLE IF NOT EXISTS pg_connection_test (key TEXT PRIMARY KEY, value TEXT)"
            )
            rows = dm.execute(
                "INSERT INTO pg_connection_test (key, value) VALUES (%s, %s)",
                (test_key, "test_value"),
            )
            assert rows >= 0

            row = dm.fetch_one(
                "SELECT * FROM pg_connection_test WHERE key = %s",
                (test_key,),
            )
            assert row is not None
            assert row["key"] == test_key
            assert row["value"] == "test_value"
        finally:
            dm.execute("DROP TABLE IF EXISTS pg_connection_test")

    def test_fetch_all_returns_list_of_dicts(self):
        url = os.getenv("POSTGRES_DATABASE_URL", "")
        dm = DatabaseManager(url)
        if dm.driver != "postgresql":
            pytest.skip("PostgreSQL not available")

        test_key = f"pg_fetch_test_{int(time.time() * 1000)}"
        try:
            dm.execute(
                "CREATE TABLE IF NOT EXISTS pg_fetch_test (key TEXT PRIMARY KEY, value TEXT)"
            )
            dm.execute(
                "INSERT INTO pg_fetch_test (key, value) VALUES (%s, %s)",
                (test_key + "_1", "val1"),
            )
            dm.execute(
                "INSERT INTO pg_fetch_test (key, value) VALUES (%s, %s)",
                (test_key + "_2", "val2"),
            )

            rows = dm.fetch_all("SELECT * FROM pg_fetch_test WHERE key LIKE %s", (test_key + "_%",))
            assert isinstance(rows, list)
            assert len(rows) == 2
            for row in rows:
                assert isinstance(row, dict)
                assert "key" in row
                assert "value" in row
        finally:
            dm.execute("DROP TABLE IF EXISTS pg_fetch_test")

    def test_fetch_one_returns_none_when_no_match(self):
        url = os.getenv("POSTGRES_DATABASE_URL", "")
        dm = DatabaseManager(url)
        if dm.driver != "postgresql":
            pytest.skip("PostgreSQL not available")

        row = dm.fetch_one(
            "SELECT * FROM pg_fetch_test WHERE key = %s",
            ("nonexistent_key_12345",),
        )
        assert row is None

    def test_transaction_commits_on_success(self):
        url = os.getenv("POSTGRES_DATABASE_URL", "")
        dm = DatabaseManager(url)
        if dm.driver != "postgresql":
            pytest.skip("PostgreSQL not available")

        test_key = f"pg_txn_{int(time.time() * 1000)}"
        try:
            dm.execute(
                "CREATE TABLE IF NOT EXISTS pg_txn_test (key TEXT PRIMARY KEY, value TEXT)"
            )
            with dm.transaction():
                dm.execute(
                    "INSERT INTO pg_txn_test (key, value) VALUES (%s, %s)",
                    (test_key, "txn_value"),
                )

            row = dm.fetch_one("SELECT * FROM pg_txn_test WHERE key = %s", (test_key,))
            assert row is not None
            assert row["value"] == "txn_value"
        finally:
            dm.execute("DROP TABLE IF EXISTS pg_txn_test")

    def test_transaction_rolls_back_on_error(self):
        url = os.getenv("POSTGRES_DATABASE_URL", "")
        dm = DatabaseManager(url)
        if dm.driver != "postgresql":
            pytest.skip("PostgreSQL not available")

        test_key = f"pg_rbk_{int(time.time() * 1000)}"
        try:
            dm.execute(
                "CREATE TABLE IF NOT EXISTS pg_rbk_test (key TEXT PRIMARY KEY, value TEXT)"
            )
            dm.execute(
                "INSERT INTO pg_rbk_test (key, value) VALUES (%s, %s)",
                (test_key + "_before", "before_txn"),
            )

            with pytest.raises(Exception):
                with dm.transaction():
                    dm.execute(
                        "INSERT INTO pg_rbk_test (key, value) VALUES (%s, %s)",
                        (test_key + "_inside", "inside_txn"),
                    )
                    raise ValueError("simulated failure")

            rows = dm.fetch_all("SELECT * FROM pg_rbk_test WHERE key LIKE %s", (test_key + "_%",))
            assert len(rows) == 1
            assert rows[0]["key"] == test_key + "_before"
        finally:
            dm.execute("DROP TABLE IF EXISTS pg_rbk_test")

    def test_execute_with_retry_succeeds(self):
        url = os.getenv("POSTGRES_DATABASE_URL", "")
        dm = DatabaseManager(url)
        if dm.driver != "postgresql":
            pytest.skip("PostgreSQL not available")

        rows = dm.execute_with_retry("SELECT 1")
        assert rows >= 0


class TestDatabaseHealthCheck:
    def test_health_check_returns_healthy_status(self):
        url = os.getenv("POSTGRES_DATABASE_URL", "")
        dm = DatabaseManager(url)
        health = dm.health_check()

        assert "status" in health
        assert "driver" in health
        if dm.driver == "postgresql":
            assert health["driver"] == "postgresql"


class TestConnectionPoolBehavior:
    def test_is_overloaded_false_under_normal_load(self):
        url = os.getenv("POSTGRES_DATABASE_URL", "")
        dm = DatabaseManager(url)
        if dm.driver != "postgresql":
            pytest.skip("PostgreSQL not available")

        assert dm.is_overloaded() is False

    def test_mask_url_hides_password(self):
        url = "postgresql://user:secret123@localhost:5432/nrg"
        dm = DatabaseManager(url)
        masked = dm._mask_url(url)
        assert "secret123" not in masked
        assert "user" in masked
        assert "localhost" in masked

    def test_mask_url_handles_empty_url(self):
        dm = DatabaseManager("")
        masked = dm._mask_url("")
        assert masked == "not configured"

    def test_mask_url_handles_url_without_password(self):
        url = "postgresql://localhost:5432/nrg"
        dm = DatabaseManager(url)
        masked = dm._mask_url(url)
        assert masked == url
