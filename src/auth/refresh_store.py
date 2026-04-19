"""Refresh token storage with hashing and revocation."""

import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import Optional


class RefreshTokenStore:
    """SQLite-backed refresh token store with SHA256 hashing."""

    def __init__(self, db_path: str = "nrg_research.db"):
        self.db_path = db_path
        self._init_table()

    def _init_table(self):
        """Create refresh_tokens table if not exists."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                issued_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked BOOLEAN DEFAULT FALSE,
                replaced_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user 
            ON refresh_tokens(user_id)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires 
            ON refresh_tokens(expires_at)
            """
        )
        conn.commit()
        conn.close()

    def _hash_token(self, token: str) -> str:
        """Hash token with SHA256."""
        return hashlib.sha256(token.encode()).hexdigest()

    def store(self, token: str, user_id: str, issued_at: datetime, expires_at: datetime) -> bool:
        """Store a new refresh token."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO refresh_tokens (token_hash, user_id, issued_at, expires_at, revoked)
                VALUES (?, ?, ?, ?, FALSE)
                """,
                (
                    self._hash_token(token),
                    user_id,
                    issued_at.isoformat(),
                    expires_at.isoformat(),
                ),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def validate(self, token: str) -> Optional[dict]:
        """Validate a refresh token. Returns user_id if valid, None if not."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            SELECT user_id, expires_at, revoked FROM refresh_tokens
            WHERE token_hash = ?
            """,
            (self._hash_token(token),),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        user_id, expires_at_str, revoked = row

        if revoked:
            return None

        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now(timezone.utc) > expires_at:
            return None

        return {"user_id": user_id, "expires_at": expires_at}

    def revoke(self, token: str, replaced_by: Optional[str] = None) -> bool:
        """Revoke a refresh token."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            UPDATE refresh_tokens
            SET revoked = TRUE, replaced_by = ?
            WHERE token_hash = ?
            """,
            (
                self._hash_token(replaced_by) if replaced_by else None,
                self._hash_token(token),
            ),
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def cleanup_expired(self, before: Optional[datetime] = None) -> int:
        """Delete expired tokens. Returns number deleted."""
        conn = sqlite3.connect(self.db_path)
        before = before or datetime.now(timezone.utc)
        cursor = conn.execute(
            "DELETE FROM refresh_tokens WHERE expires_at < ?",
            (before.isoformat(),),
        )
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        return deleted

    def is_revoked(self, token: str) -> bool:
        """Check if a token is revoked."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT revoked FROM refresh_tokens WHERE token_hash = ?",
            (self._hash_token(token),),
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None and row[0]
