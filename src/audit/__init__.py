"""Immutable Audit Log with HMAC-SHA256 Chaining."""

import hmac
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)

CHAIN_KEY = os.environ.get("AUDIT_CHAIN_KEY")
if not CHAIN_KEY and os.environ.get("NRG_ENV", "dev") != "dev":
    raise RuntimeError("AUDIT_CHAIN_KEY must be set outside dev")


class AuditEvent:
    """Single audit event."""

    def __init__(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        query: Optional[str] = None,
        sql: Optional[str] = None,
        vector_query: Optional[str] = None,
        llm_call: Optional[dict] = None,
        result: Optional[dict] = None,
        error: Optional[str] = None,
        event_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ):
        self.event_id = event_id or str(uuid.uuid4())[:8]
        self.event_type = event_type
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.user_id = user_id
        self.query = query
        self.sql = sql
        self.vector_query = vector_query
        self.llm_call = llm_call
        self.result = result
        self.error = error

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def serialize(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, default=str)


class ImmutableAuditLog:
    """Append-only audit log with HMAC chaining."""

    CHAIN_KEY = CHAIN_KEY or "nrg-audit-chain-dev-key"

    def __init__(self, storage_path: str = ".audit"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.chain_file = self.storage_path / "chain.jsonl"
        self.merkle_file = self.storage_path / "merkle_root.json"
        self.last_hash_file = self.storage_path / ".last_hash"

        self.last_hash = self._load_last_hash()
        self.event_count = 0

    def _load_last_hash(self) -> str:
        if self.last_hash_file.exists():
            return self.last_hash_file.read_text().strip()
        return self._genesis_hash()

    def _genesis_hash(self) -> str:
        return "0" * 64

    def _compute_hash(self, prev_hash: str, event: AuditEvent) -> str:
        message = prev_hash + event.serialize()
        return hmac.new(
            self.CHAIN_KEY.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

    def append(self, event: AuditEvent) -> str:
        """Append event to log, return new hash."""
        if event.user_id is None:
            event.user_id = "system"

        new_hash = self._compute_hash(self.last_hash, event)

        with open(self.chain_file, "a") as f:
            f.write(json.dumps({**event.to_dict(), "hash": new_hash}) + "\n")

        self.last_hash = new_hash
        self.last_hash_file.write_text(new_hash)
        self.event_count += 1

        logger.info(f"Audit event {event.event_id} appended, chain hash: {new_hash[:16]}...")
        return new_hash

    def log_query(self, user_id: str, query: str) -> str:
        return self.append(AuditEvent(event_type="query", user_id=user_id, query=query))

    def log_plan(self, user_id: str, query: str, plan: dict) -> str:
        return self.append(
            AuditEvent(
                event_type="plan",
                user_id=user_id,
                query=query,
                llm_call=plan,
            )
        )

    def log_sql(self, user_id: str, sql: str, result: dict = None) -> str:
        return self.append(
            AuditEvent(event_type="sql", user_id=user_id, sql=sql, result=result)
        )

    def log_vector_query(self, user_id: str, query: str, vector_query: str) -> str:
        return self.append(
            AuditEvent(
                event_type="vector_query",
                user_id=user_id,
                query=query,
                vector_query=vector_query,
            )
        )

    def log_llm_call(
        self, user_id: str, prompt: str, response: dict, model: str
    ) -> str:
        return self.append(
            AuditEvent(
                event_type="llm_call",
                user_id=user_id,
                llm_call={"prompt": prompt, "model": model, "response": response},
            )
        )

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verify chain integrity, return (valid, errors)."""
        errors = []

        if not self.chain_file.exists():
            return True, []

        prev_hash = self._genesis_hash()

        with open(self.chain_file) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    event_data = json.loads(line)
                    recorded_hash = event_data.get("hash")

                    computed_hash = self._compute_hash(
                        prev_hash, AuditEvent(**{k: v for k, v in event_data.items() if k != "hash"})
                    )

                    if computed_hash != recorded_hash:
                        errors.append(f"Line {line_num}: hash mismatch")

                    prev_hash = recorded_hash

                except Exception as e:
                    errors.append(f"Line {line_num}: {e}")

        if self.last_hash != prev_hash:
            errors.append("Final hash mismatch")

        return len(errors) == 0, errors

    def get_merkle_root(self) -> dict:
        """Publish daily Merkle root."""
        today = date.today().isoformat()
        events = []

        if self.chain_file.exists():
            with open(self.chain_file) as f:
                for line in f:
                    if today in line:
                        events.append(json.loads(line))

        if not events:
            return {"date": today, "merkle_root": self._genesis_hash(), "event_count": 0}

        merkle_root = hashlib.sha256(
            "".join(e["hash"] for e in events).encode()
        ).hexdigest()

        return {
            "date": today,
            "merkle_root": merkle_root,
            "event_count": len(events),
        }


_audit_log_instance: Optional[ImmutableAuditLog] = None


def get_audit_log() -> ImmutableAuditLog:
    global _audit_log_instance
    if _audit_log_instance is None:
        _audit_log_instance = ImmutableAuditLog()
    return _audit_log_instance


def log_query(user_id: str, query: str) -> str:
    return get_audit_log().log_query(user_id, query)


def log_plan(user_id: str, query: str, plan: dict) -> str:
    return get_audit_log().log_plan(user_id, query, plan)


def log_sql(user_id: str, sql: str, result: dict = None) -> str:
    return get_audit_log().log_sql(user_id, sql, result)


def log_llm_call(user_id: str, prompt: str, response: dict, model: str) -> str:
    return get_audit_log().log_llm_call(user_id, prompt, response, model)


def verify_chain() -> tuple[bool, list[str]]:
    return get_audit_log().verify_chain()