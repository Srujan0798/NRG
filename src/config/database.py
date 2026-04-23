"""
DatabaseManager — Task #23 Phase 1
Dual-database runtime: SQLite for dev, PostgreSQL for prod.
Reads DATABASE_URL env var to determine driver.
Provides unified interface: execute(), fetch_all(), fetch_one(), transaction().
Connection pool: min=5, max=20 for PostgreSQL. Single connection for SQLite.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator, Literal, Optional

import logging
logger = logging.getLogger(__name__)

DEFAULT_POOL_MIN = 5
DEFAULT_POOL_MAX = 20
DEFAULT_POOL_TIMEOUT = 30.0


@dataclass
class PoolStats:
    """Connection pool statistics."""
    active: int = 0
    idle: int = 0
    waiting: int = 0
    max_size: int = 20
    min_size: int = 5


class DatabaseManager:
    """Unified database manager for SQLite (dev) and PostgreSQL (prod).

    Detects driver from DATABASE_URL:
    - postgresql://...  → asyncpg pool
    - sqlite:///...     → SQLite direct connection

    Interface:
    - execute(sql, params) → int (rows affected)
    - fetch_all(sql, params) → list[Row]
    - fetch_one(sql, params) → Row | None
    - transaction() → context manager
    - health_check() → dict
    - pool_stats() → PoolStats
    """

    _instance: "DatabaseManager | None" = None
    _lock = threading.Lock()

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "") or ""
        self.driver = self._detect_driver()
        self._pool: Any = None
        self._pool_lock = threading.Lock()
        self._pool_exhausted_until: float | None = None

        if self.driver == "postgresql":
            self._init_postgres_pool()
        elif self.driver == "sqlite":
            self._sqlite_path = self._resolve_sqlite_path()

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _detect_driver(self) -> Literal["postgresql", "sqlite"]:
        if self.database_url.startswith("postgresql://"):
            return "postgresql"
        return "sqlite"

    def _resolve_sqlite_path(self) -> Path:
        raw = self.database_url
        if raw.startswith("sqlite:///"):
            raw = raw[len("sqlite:///") :]
        if not raw:
            raw = "nrg_research.db"
        path = Path(raw).expanduser()
        if not path.is_absolute():
            from pathlib import Path as P
            path = P(__file__).resolve().parents[2] / path
        return path.resolve()

    def _init_postgres_pool(self) -> None:
        try:
            import asyncpg
        except ImportError:
            logger.warning("asyncpg not installed — PostgreSQL pool unavailable")
            self.driver = "sqlite"
            return

        async def _create_pool():
            try:
                self._pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=DEFAULT_POOL_MIN,
                    max_size=DEFAULT_POOL_MAX,
                    command_timeout=60.0,
                    timeout=DEFAULT_POOL_TIMEOUT,
                )
                logger.info(
                    f"PostgreSQL pool initialized: min={DEFAULT_POOL_MIN}, max={DEFAULT_POOL_MAX}"
                )
            except Exception as e:
                logger.error(f"Failed to create PostgreSQL pool: {e}")
                self.driver = "sqlite"

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _create_pool())
                    future.result(timeout=30)
            else:
                asyncio.run(_create_pool())
        except Exception as e:
            logger.warning(f"PostgreSQL pool creation deferred: {e}")

    @contextmanager
    def _sqlite_connection(self) -> Generator[sqlite3.Connection, None, None]:
        if self._pool_exhausted_until and time.time() < self._pool_exhausted_until:
            raise ConnectionError("SQLite pool exhausted, overloaded")
        conn = sqlite3.connect(self._sqlite_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def _pg_connection(self) -> Generator[Any, None, None]:
        if self._pool is None:
            raise ConnectionError("PostgreSQL pool not initialized")
        try:
            async def _get():
                return await self._pool.acquire(timeout=DEFAULT_POOL_TIMEOUT)
            import asyncio
            conn = asyncio.run(_get())
            try:
                yield conn
            finally:
                async def _release():
                    await self._pool.release(conn)
                asyncio.run(_release())
        except Exception as e:
            if "timeout" in str(e).lower() or "pool" in str(e).lower():
                self._pool_exhausted_until = time.time() + 5.0
                logger.error("PostgreSQL pool exhausted — queries will return 503")
            raise

    @contextmanager
    def connection(self) -> Generator[Any, None, None]:
        """Context manager for a raw connection (use execute/fetch_all instead)."""
        if self.driver == "postgresql":
            yield from self._pg_connection()
        else:
            yield from self._sqlite_connection()

    def execute(self, sql: str, params: tuple = ()) -> int:
        """Execute SQL and return rows affected."""
        with self.connection() as conn:
            if self.driver == "postgresql":
                cur = conn.cursor()
                cur.execute(sql, params)
                await cur.execute("COMMIT") if hasattr(conn, "execute") else None
                return cur.rowcount
            else:
                cur = conn.execute(sql, params)
                conn.commit()
                return cur.rowcount

    def fetch_all(self, sql: str, params: tuple = ()) -> list[Any]:
        """Execute SELECT and return all rows."""
        with self.connection() as conn:
            if self.driver == "postgresql":
                cur = conn.cursor()
                await cur.execute(sql, params)
                rows = await cur.fetchall()
                return [dict(row) for row in rows]
            else:
                cur = conn.execute(sql, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]

    def fetch_one(self, sql: str, params: tuple = ()) -> dict | None:
        """Execute SELECT and return first row or None."""
        rows = self.fetch_all(sql + " LIMIT 1", params)
        return rows[0] if rows else None

    @contextmanager
    def transaction(self) -> Generator:
        """Context manager for a transaction."""
        with self.connection() as conn:
            if self.driver == "postgresql":
                async def _begin():
                    await conn.execute("BEGIN")
                import asyncio
                asyncio.run(_begin())
                try:
                    yield conn
                    async def _commit():
                        await conn.execute("COMMIT")
                    asyncio.run(_commit())
                except Exception:
                    async def _rollback():
                        await conn.execute("ROLLBACK")
                    asyncio.run(_rollback())
                    raise
            else:
                try:
                    yield conn
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise

    def health_check(self) -> dict:
        """Verify connection and return health status."""
        try:
            with self.connection() as conn:
                if self.driver == "postgresql":
                    async def _check():
                        row = await conn.fetchrow("SELECT 1 as n")
                        return row["n"]
                    result = asyncio.run(_check())
                else:
                    cur = conn.execute("SELECT 1 as n")
                    result = cur.fetchone()["n"]
            return {
                "status": "healthy",
                "driver": self.driver,
                "url": self._mask_url(self.database_url) if self.database_url else "sqlite",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "driver": self.driver,
                "error": str(e),
            }

    def pool_stats(self) -> PoolStats:
        """Return current connection pool stats."""
        if self.driver != "postgresql" or self._pool is None:
            return PoolStats()
        try:
            return PoolStats(
                active=0,
                idle=0,
                waiting=0,
                max_size=DEFAULT_POOL_MAX,
                min_size=DEFAULT_POOL_MIN,
            )
        except Exception:
            return PoolStats()

    def _mask_url(self, url: str) -> str:
        """Mask password in database URL for logging."""
        if not url:
            return "not configured"
        if "@" not in url:
            return url
        parts = url.split("@")
        user_pass = parts[0].split("://")
        if len(user_pass) == 2 and ":" in user_pass[1]:
            masked = f"{user_pass[0]}://***:***"
        else:
            masked = user_pass[0] + "://***"
        return masked + "@" + "@".join(parts[1:])

    def is_overloaded(self) -> bool:
        """Return True if pool is exhausted (circuit breaker)."""
        if self._pool_exhausted_until and time.time() < self._pool_exhausted_until:
            return True
        return False

    def execute_with_retry(
        self,
        sql: str,
        params: tuple = (),
        max_retries: int = 2,
        retry_delay: float = 0.5,
    ) -> int:
        """Execute with automatic retry on transient errors."""
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                return self.execute(sql, params)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    time.sleep(retry_delay * (attempt + 1))
        raise last_error


_db_instance: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    """Get singleton database manager."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
