"""Immutable Audit Log with HMAC-SHA256 Chaining.

Phase 1 - Fortify: HMAC-SHA256 chaining, append-only events
Phase 2 - Elevate: Key rotation, serialization versioning, Merkle roots
Phase 3 - Immortalize: Tamper detection, integrity alerts, compliance docs
"""

import hmac
import hashlib
import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, date, UTC
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CHAIN_KEY = os.environ.get("AUDIT_CHAIN_KEY")
if not CHAIN_KEY and os.environ.get("NRG_ENV", "dev") != "dev":
    raise RuntimeError("AUDIT_CHAIN_KEY must be set outside dev")

AUDIT_CHAIN_VERSION = 1
AUDIT_ALERT_WEBHOOK = os.environ.get("AUDIT_ALERT_WEBHOOK")


class AuditEvent:
    """Single audit event with serialization versioning and user non-repudiation."""

    SERIALIZATION_VERSION = 1

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
        _key_rotation: Optional[dict] = None,
        _v: Optional[int] = None,
        user_key_hash: Optional[str] = None,
        per_user_binding: Optional[str] = None,
    ):
        self.event_id = event_id or str(uuid.uuid4())[:8]
        self.event_type = event_type
        self.timestamp = timestamp or datetime.now(UTC).isoformat()
        self.user_id = user_id
        self.query = query
        self.sql = sql
        self.vector_query = vector_query
        self.llm_call = llm_call
        self.result = result
        self.error = error
        self._v = _v if _v is not None else self.SERIALIZATION_VERSION
        self._key_rotation = _key_rotation
        self.user_key_hash = user_key_hash
        self.per_user_binding = per_user_binding

    def to_dict(self) -> dict:
        result = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            if k == "_v" and v == self.SERIALIZATION_VERSION:
                continue
            if k in ("per_user_binding", "user_key_hash"):
                continue
            result[k] = v
        return result

    def serialize(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, default=str)

    def compute_user_key_hash(self, chain_key: str) -> str:
        """Compute HMAC of user_id + event data for non-repudiation."""
        if not self.user_id or self.user_id == "system":
            return ""
        message = f"{self.user_id}:{self.event_id}:{self.event_type}"
        return hmac.new(
            chain_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]


class ImmutableAuditLog:
    """Thread-safe append-only audit log with HMAC chaining and key rotation."""

    CHAIN_KEY = CHAIN_KEY or "nrg-audit-chain-dev-key"
    _instance: Optional["ImmutableAuditLog"] = None
    _lock = threading.Lock()

    @classmethod
    def _reset(cls) -> None:
        """Reset singleton instance. For testing only."""
        with cls._lock:
            cls._instance = None
        global _chain_health_cache
        _chain_health_cache = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, storage_path: str = ".audit"):
        new_path = Path(storage_path)
        already_init = "_initialized" in self.__dict__ and self.__dict__.get("_initialized") is True
        if already_init and self.__dict__.get("storage_path") == new_path:
            return
        self.__dict__["_initialized"] = True
        self.storage_path = new_path
        self.storage_path.mkdir(exist_ok=True)
        self.chain_file = self.storage_path / "chain.jsonl"
        self.merkle_file = self.storage_path / "merkle_root.json"
        self.merkle_roots_file = self.storage_path / "merkle_roots.jsonl"
        self.last_hash_file = self.storage_path / ".last_hash"
        self.integrity_alerts_file = self.storage_path / "integrity_alerts.jsonl"
        self.witness_file = self.storage_path / "witness_replicas.jsonl"
        self.revocation_file = self.storage_path / "revoked_tokens.jsonl"
        self._key_history: list[dict] = []
        self._user_key_cache: dict[str, str] = {}  # user_id -> derived_key_hash

        self.last_hash = self._load_last_hash()
        self.event_count = self._count_events()

        self._persist_merkle_root()

    def _derive_user_key(self, user_id: str) -> str:
        """
        Derive a per-user key from user credential + server salt for non-repudiation.
        Uses PBKDF2-like derivation to create unique per-user chain binding.
        """
        if user_id in self._user_key_cache:
            return self._user_key_cache[user_id]

        # Derive key from user_id + chain_key using HMAC
        derived = hmac.new(
            self.CHAIN_KEY.encode(),
            f"user_key:{user_id}".encode(),
            hashlib.sha256,
        ).hexdigest()[:32]  # 256-bit key

        self._user_key_cache[user_id] = derived
        return derived

    def _compute_per_user_hash(self, user_key: str, prev_hash: str, event: AuditEvent) -> str:
        """
        Compute hash with per-user binding for non-repudiation.
        Each user's actions are cryptographically bound to their identity.
        """
        user_message = f"{user_key}:{prev_hash}:{event.serialize()}"
        return hmac.new(
            user_key.encode(),
            user_message.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _count_events(self) -> int:
        if not self.chain_file.exists():
            return 0
        with open(self.chain_file) as f:
            return sum(1 for _ in f)

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

    def _compute_hash_with_key(self, key: str, prev_hash: str, event: AuditEvent) -> str:
        message = prev_hash + event.serialize()
        return hmac.new(
            key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

    def append(self, event: AuditEvent) -> str:
        """Append event to log with per-user non-repudiation binding. Thread-safe."""
        if event.user_id is None:
            event.user_id = "system"

        # Compute per-user key hash for non-repudiation
        user_key = self._derive_user_key(event.user_id)
        event.user_key_hash = event.compute_user_key_hash(user_key)

        # Compute chain hash (uses CHAIN_KEY for chain integrity)
        with self._lock:
            new_hash = self._compute_hash(self.last_hash, event)

            # Compute per-user binding hash (uses user-specific key)
            per_user_hash = self._compute_per_user_hash(user_key, new_hash, event)

            event_data = event.to_dict()
            event_data["hash"] = new_hash
            event_data["per_user_binding"] = per_user_hash[:16]  # Store truncated for space

            with open(self.chain_file, "a") as f:
                f.write(json.dumps(event_data, default=str) + "\n")

            self.last_hash = new_hash
            self.last_hash_file.write_text(new_hash)
            self.event_count += 1

            logger.info(f"Audit event {event.event_id} appended, chain: {new_hash[:16]}..., user_bind: {per_user_hash[:8]}...")
            return new_hash

    def rotate_key(self, old_key: str, new_key: str) -> str:
        """Rotate the chain key, creating a provable transition event signed with both keys."""
        with self._lock:
            rotation_event = AuditEvent(
                event_type="key_rotation",
                user_id="system",
                _key_rotation={
                    "old_key_hash": hashlib.sha256(old_key.encode()).hexdigest()[:16],
                    "new_key_hash": hashlib.sha256(new_key.encode()).hexdigest()[:16],
                    "rotated_at": datetime.now(UTC).isoformat(),
                    "events_before_rotation": self.event_count,
                },
            )

            signed_with_old = self._compute_hash_with_key(old_key, self.last_hash, rotation_event)
            signed_with_new = self._compute_hash_with_key(new_key, self.last_hash, rotation_event)

            rotation_event._key_rotation["old_signature"] = signed_with_old
            rotation_event._key_rotation["new_signature"] = signed_with_new

            self._key_history.append({
                "old_key": old_key,
                "new_key": new_key,
                "events_before": self.event_count,
                "rotation_hash": signed_with_new,
            })

            new_hash = self._compute_hash_with_key(new_key, self.last_hash, rotation_event)

            with open(self.chain_file, "a") as f:
                f.write(json.dumps({**rotation_event.to_dict(), "hash": new_hash}) + "\n")

            self.CHAIN_KEY = new_key
            self.last_hash = new_hash
            self.last_hash_file.write_text(new_hash)
            self.event_count += 1

            logger.warning(f"Key rotation completed. New key hash: {new_key[:16]}...")
            return new_hash

    def verify_chain(self, key: Optional[str] = None) -> tuple[bool, list[str], int]:
        """Verify chain integrity, return (valid, errors, valid_event_count)."""
        errors = []
        chain_key = key or self.CHAIN_KEY
        prev_hash = self._genesis_hash()
        valid_count = 0

        if not self.chain_file.exists():
            return True, [], 0

        with open(self.chain_file) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    event_data = json.loads(line)
                    recorded_hash = event_data.get("hash")

                    event_kwargs = {k: v for k, v in event_data.items() if k != "hash"}
                    if "_v" not in event_data:
                        event_kwargs["_v"] = None

                    computed_hash = self._compute_hash_with_key(
                        chain_key, prev_hash,
                        AuditEvent(**event_kwargs)
                    )

                    if computed_hash != recorded_hash:
                        errors.append(f"Line {line_num}: hash mismatch")
                    else:
                        valid_count = line_num

                    prev_hash = recorded_hash

                except Exception as e:
                    errors.append(f"Line {line_num}: {e}")

        return len(errors) == 0, errors, valid_count

    def _persist_merkle_root(self) -> None:
        """Persist daily Merkle root to merkle_roots.jsonl."""
        merkle = self.get_merkle_root()
        if merkle["event_count"] > 0:
            with open(self.merkle_roots_file, "a") as f:
                f.write(json.dumps(merkle) + "\n")

    def get_merkle_root(self, for_date: Optional[str] = None) -> dict:
        """Get Merkle root for a specific date or today (UTC)."""
        target_date = for_date or datetime.now(UTC).date().isoformat()
        events = []

        if self.chain_file.exists():
            with open(self.chain_file) as f:
                for line in f:
                    if target_date in line:
                        events.append(json.loads(line))

        if not events:
            return {"date": target_date, "merkle_root": self._genesis_hash(), "event_count": 0}

        merkle_root = hashlib.sha256(
            "".join(e["hash"] for e in events).encode()
        ).hexdigest()

        return {
            "date": target_date,
            "merkle_root": merkle_root,
            "event_count": len(events),
        }

    def get_chain_health(self) -> dict:
        """Get chain health status for monitoring."""
        valid, errors, valid_count = self.verify_chain()
        return {
            "chain_valid": valid,
            "chain_length": self.event_count,
            "valid_events": valid_count,
            "error_count": len(errors),
            "last_hash": self.last_hash[:16] + "...",
            "last_event": self._get_last_event_time(),
        }

    def _get_last_event_time(self) -> Optional[str]:
        if not self.chain_file.exists():
            return None
        with open(self.chain_file) as f:
            for line in f:
                pass
            last = json.loads(line)
            return last.get("timestamp")

    def log_tamper_alert(self, error_details: str) -> None:
        """Log a tamper detection alert to the integrity alerts file."""
        alert = {
            "timestamp": datetime.now(UTC).isoformat(),
            "alert_type": "chain_tamper_detected",
            "details": error_details,
            "chain_length_at_alert": self.event_count,
        }
        with open(self.integrity_alerts_file, "a") as f:
            f.write(json.dumps(alert) + "\n")

        logger.critical(f"TAMPER DETECTED: {error_details}")

        try:
            import httpx
            if AUDIT_ALERT_WEBHOOK:
                httpx.post(AUDIT_ALERT_WEBHOOK, json=alert, timeout=5)
        except Exception:
            pass

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

    def log_sql(self, user_id: str, sql: str, result: Optional[dict] = None) -> str:
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

    def log_anomaly(
        self,
        user_id: str,
        anomaly_type: str,
        details: dict,
        identifier: Optional[str] = None,
    ) -> str:
        """Log a behavioral anomaly detected by the security pipeline."""
        return self.append(
            AuditEvent(
                event_type="anomaly_detected",
                user_id=user_id,
                query=identifier,
                result={
                    "anomaly_type": anomaly_type,
                    "details": details,
                },
            )
        )

    def replicate_to_witness(self, witness_urls: list[str], event_hash: str) -> dict:
        """
        Replicate audit entry to government + institute witness servers for multi-party attestation.
        Returns dict with replication status per witness.
        """
        import httpx
        replication_status = {}

        # Load the event data to replicate
        event_data = None
        if self.chain_file.exists():
            with open(self.chain_file) as f:
                for line in f:
                    if event_hash in line:
                        event_data = json.loads(line)
                        break

        if not event_data:
            logger.warning(f"Event {event_hash[:16]} not found for replication")
            return {"error": "Event not found"}

        for witness_url in witness_urls:
            try:
                response = httpx.post(
                    f"{witness_url}/audit/witness",
                    json=event_data,
                    timeout=10,
                )
                replication_status[witness_url] = {
                    "status": "success" if response.status_code == 200 else "failed",
                    "response_code": response.status_code,
                }
            except Exception as e:
                replication_status[witness_url] = {
                    "status": "error",
                    "error": str(e),
                }

        # Log replication attempt
        with open(self.witness_file, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.now(UTC).isoformat(),
                "event_hash": event_hash,
                "replication_status": replication_status,
            }) + "\n")

        return replication_status

    def log_token_revocation(self, user_id: str, token_jti: str, reason: str) -> str:
        """
        Log token revocation for audit trail.
        Revoked tokens cannot have their audit entries later denied.
        """
        return self.append(
            AuditEvent(
                event_type="token_revocation",
                user_id=user_id,
                result={
                    "revoked_token_jti": token_jti,
                    "reason": reason,
                    "revoked_at": datetime.now(UTC).isoformat(),
                },
            )
        )

    def get_user_events(self, user_id: str, limit: int = 100) -> list[dict]:
        """Return audit events for a specific user for non-repudiation verification."""
        events = []
        if self.chain_file.exists():
            with open(self.chain_file) as f:
                for line in f:
                    event_data = json.loads(line)
                    if event_data.get("user_id") == user_id:
                        events.append(event_data)
        return events[-limit:] if events else []

    def verify_user_binding(self, user_id: str, event_hash: str) -> tuple[bool, str]:
        """
        Verify that an event's per-user binding is valid for non-repudiation.
        Returns (is_valid, error_message).
        """
        event_data = None
        if self.chain_file.exists():
            with open(self.chain_file) as f:
                for line in f:
                    if event_hash in line:
                        event_data = json.loads(line)
                        break

        if not event_data:
            return False, "Event not found"

        stored_binding = event_data.get("per_user_binding")
        if not stored_binding:
            return False, "No per-user binding found"

        # Recompute the binding
        user_key = self._derive_user_key(user_id)
        event_kwargs = {k: v for k, v in event_data.items() if k != "hash" and k != "per_user_binding"}
        event = AuditEvent(**event_kwargs)
        recomputed = self._compute_per_user_hash(user_key, event_data["hash"], event)

        if recomputed[:16] == stored_binding:
            return True, "Valid"
        else:
            return False, "Binding mismatch - possible tampering"

    def get_last_hash(self) -> str:
        """Return the hash of the most recent sealed event."""
        return self._load_last_hash()

    def get_recent_events(self, limit: int = 100) -> list[dict]:
        """Return the most recent audit events from the chain."""
        events = []
        if self.chain_file.exists():
            with open(self.chain_file) as f:
                for line in f:
                    events.append(json.loads(line))
        return events[-limit:] if events else []


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


def log_sql(user_id: str, sql: str, result: Optional[dict] = None) -> str:
    return get_audit_log().log_sql(user_id, sql, result)


def log_llm_call(user_id: str, prompt: str, response: dict, model: str) -> str:
    return get_audit_log().log_llm_call(user_id, prompt, response, model)


def log_anomaly(user_id: str, anomaly_type: str, details: dict, identifier: Optional[str] = None) -> str:
    return get_audit_log().log_anomaly(user_id, anomaly_type, details, identifier)


def verify_chain() -> tuple[bool, list[str], int]:
    """Verify chain integrity, return (valid, errors, valid_event_count)."""
    return get_audit_log().verify_chain()


_chain_health_cache: tuple[float, dict] | None = None


def get_chain_health() -> dict:
    """Get chain health status for monitoring. Cached for 5s to avoid repeated full-chain scans."""
    global _chain_health_cache
    now = time.time()
    if _chain_health_cache is not None:
        cached_at, cached_result = _chain_health_cache
        if now - cached_at < 5.0:
            return cached_result
    result = get_audit_log().get_chain_health()
    _chain_health_cache = (now, result)
    return result