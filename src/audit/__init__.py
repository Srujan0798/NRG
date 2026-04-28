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
import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from src.audit.lock import AuditChainLock, AuditLockTimeout

logger = logging.getLogger(__name__)

CHAIN_KEY = os.environ.get("AUDIT_CHAIN_KEY")
if not CHAIN_KEY and os.environ.get("NRG_ENV", "dev") != "dev":
    raise RuntimeError("AUDIT_CHAIN_KEY must be set outside dev")

AUDIT_CHAIN_VERSION = 1
AUDIT_ALERT_WEBHOOK = os.environ.get("AUDIT_ALERT_WEBHOOK")
AUDIT_LOCK_TIMEOUT = float(os.environ.get("AUDIT_LOCK_TIMEOUT", "5.0"))
_chain_key_cache: bytes | None = None
_chain_key_lock = threading.Lock()
_cosign_executor: ThreadPoolExecutor | None = None
_cosign_executor_lock = threading.Lock()
_cosign_metrics_lock = threading.Lock()
_cosign_metrics = {
    "submitted": 0,
    "succeeded": 0,
    "failed": 0,
    "queue_depth": 0,
    "max_queue_depth": 0,
    "success_rate": 1.0,
    "last_latency_ms": None,
    "last_error": None,
    "last_completed_at": None,
}


def _configured_chain_key_text() -> str:
    return os.environ.get("AUDIT_CHAIN_KEY") or CHAIN_KEY or "nrg-audit-chain-dev-key"


def get_chain_key() -> bytes:
    """Return the active audit chain key bytes."""
    global _chain_key_cache
    configured = _configured_chain_key_text().encode()
    with _chain_key_lock:
        if _chain_key_cache != configured:
            _chain_key_cache = configured
        return _chain_key_cache


def reset_chain_key_cache() -> None:
    """Clear cached chain-key bytes after environment changes in tests."""
    global _chain_key_cache
    with _chain_key_lock:
        _chain_key_cache = None


def chain_key_hash() -> str:
    return hashlib.sha256(get_chain_key()).hexdigest()[:16]


def _is_postgres_database_url(database_url: str | None) -> bool:
    return bool(database_url and database_url.startswith(("postgresql://", "postgres://")))


def should_db_cosign() -> bool:
    """Return True when DB co-signing is configured for a PostgreSQL target."""
    return _is_postgres_database_url(os.environ.get("DATABASE_URL")) and bool(
        os.environ.get("AUDIT_DB_COSIGN_KEY")
    )


def _get_cosign_executor() -> ThreadPoolExecutor:
    """Return the bounded DB co-sign executor.

    Audit-chain append must stay on the request path, but DB co-signing can be
    written asynchronously. A bounded worker count prevents one thread per
    request during bursts.
    """
    global _cosign_executor
    with _cosign_executor_lock:
        if _cosign_executor is None:
            workers = max(1, int(os.environ.get("AUDIT_DB_COSIGN_WORKERS", "1")))
            _cosign_executor = ThreadPoolExecutor(
                max_workers=workers,
                thread_name_prefix="audit-db-cosign",
            )
        return _cosign_executor


def _executor_queue_depth(executor: object) -> int:
    """Return pending DB co-sign work when the executor exposes a queue."""
    work_queue = getattr(executor, "_work_queue", None)
    if work_queue is None:
        return 0
    try:
        return int(work_queue.qsize())
    except Exception:
        return 0


def _publish_db_cosign_metrics(snapshot: dict) -> None:
    try:
        from src.observability.metrics import set_audit_db_cosign_metrics

        set_audit_db_cosign_metrics(snapshot)
    except Exception:
        pass


def _db_cosign_metrics_snapshot() -> dict:
    submitted = int(_cosign_metrics["submitted"])
    succeeded = int(_cosign_metrics["succeeded"])
    failed = int(_cosign_metrics["failed"])
    completed = succeeded + failed
    success_rate = succeeded / completed if completed else 1.0
    snapshot = dict(_cosign_metrics)
    snapshot["submitted"] = submitted
    snapshot["succeeded"] = succeeded
    snapshot["failed"] = failed
    snapshot["success_rate"] = success_rate
    return snapshot


def _record_db_cosign_submitted(queue_depth: int) -> None:
    with _cosign_metrics_lock:
        _cosign_metrics["submitted"] = int(_cosign_metrics["submitted"]) + 1
        _cosign_metrics["queue_depth"] = queue_depth
        _cosign_metrics["max_queue_depth"] = max(
            int(_cosign_metrics["max_queue_depth"]),
            queue_depth,
        )
        snapshot = _db_cosign_metrics_snapshot()
    _publish_db_cosign_metrics(snapshot)


def _record_db_cosign_completed(
    *,
    success: bool,
    latency_ms: float,
    queue_depth: int,
    error: str | None = None,
) -> None:
    with _cosign_metrics_lock:
        if success:
            _cosign_metrics["succeeded"] = int(_cosign_metrics["succeeded"]) + 1
            _cosign_metrics["last_error"] = None
        else:
            _cosign_metrics["failed"] = int(_cosign_metrics["failed"]) + 1
            _cosign_metrics["last_error"] = error
        _cosign_metrics["last_latency_ms"] = round(latency_ms, 3)
        _cosign_metrics["last_completed_at"] = datetime.now(UTC).isoformat()
        _cosign_metrics["queue_depth"] = queue_depth
        _cosign_metrics["max_queue_depth"] = max(
            int(_cosign_metrics["max_queue_depth"]),
            queue_depth,
        )
        snapshot = _db_cosign_metrics_snapshot()
    _publish_db_cosign_metrics(snapshot)


def get_db_cosign_metrics() -> dict:
    """Return DB co-sign worker metrics for health and CI checks."""
    with _cosign_metrics_lock:
        return _db_cosign_metrics_snapshot()


def reset_db_cosign_metrics() -> None:
    """Reset DB co-sign worker metrics. Intended for tests."""
    with _cosign_metrics_lock:
        _cosign_metrics.update(
            {
                "submitted": 0,
                "succeeded": 0,
                "failed": 0,
                "queue_depth": 0,
                "max_queue_depth": 0,
                "success_rate": 1.0,
                "last_latency_ms": None,
                "last_error": None,
                "last_completed_at": None,
            }
        )
        snapshot = _db_cosign_metrics_snapshot()
    _publish_db_cosign_metrics(snapshot)


def _schedule_db_cosign(cosign_args: tuple[str, str, str, str, str]) -> None:
    """Submit DB co-sign work and record failures from the background Future."""
    event_id = cosign_args[0]
    executor = _get_cosign_executor()
    submitted_at = time.perf_counter()

    def _cosign_fire_and_forget():
        from src.audit.db_cosign import cosign_event as _cosign

        signature = _cosign(*cosign_args)
        if signature is None:
            raise RuntimeError(f"DB co-sign returned no signature for event {event_id}")
        return signature

    def _cosign_done(future) -> None:
        latency_ms = (time.perf_counter() - submitted_at) * 1000
        try:
            exc = future.exception()
        except Exception as callback_exc:
            exc = callback_exc
        queue_depth = _executor_queue_depth(executor)
        if exc is not None:
            logger.warning("DB co-sign background task failed for event %s: %s", event_id, exc)
            _record_db_cosign_completed(
                success=False,
                latency_ms=latency_ms,
                queue_depth=queue_depth,
                error=str(exc),
            )
            return
        _record_db_cosign_completed(
            success=True,
            latency_ms=latency_ms,
            queue_depth=queue_depth,
        )

    try:
        future = executor.submit(_cosign_fire_and_forget)
        _record_db_cosign_submitted(_executor_queue_depth(executor))
        future.add_done_callback(_cosign_done)
    except Exception as exc:
        latency_ms = (time.perf_counter() - submitted_at) * 1000
        logger.warning("DB co-sign background submit failed for event %s: %s", event_id, exc)
        _record_db_cosign_completed(
            success=False,
            latency_ms=latency_ms,
            queue_depth=_executor_queue_depth(executor),
            error=str(exc),
        )


def verify_chain_continuity(stored_key_hash: str) -> bool:
    """Verify that the process is using the same chain key family."""
    return stored_key_hash == chain_key_hash()


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
        jwt_kid: Optional[str] = None,
        request_fingerprint: Optional[str] = None,
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
        self.jwt_kid = jwt_kid
        self.request_fingerprint = request_fingerprint

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

    CHAIN_KEY = _configured_chain_key_text()
    _instance: Optional["ImmutableAuditLog"] = None
    _lock = threading.Lock()

    @classmethod
    def _reset(cls) -> None:
        """Reset singleton instance. For testing only."""
        with cls._lock:
            cls._instance = None
        global _chain_health_cache
        _chain_health_cache = None
        globals().pop("_audit_log_instance", None)

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, storage_path: str = ".audit"):
        configured_path = storage_path
        if storage_path == ".audit":
            configured_path = os.environ.get("NRG_AUDIT_DIR", storage_path)
        new_path = Path(configured_path)
        if "_initialized" in self.__dict__ and self.__dict__.get("_initialized") is True and self.__dict__.get("storage_path") == new_path:
            return
        self.__dict__["_initialized"] = True
        self.CHAIN_KEY = _configured_chain_key_text()
        self.storage_path = new_path
        self.storage_path.mkdir(exist_ok=True)
        self.chain_file = self.storage_path / "chain.jsonl"
        self.merkle_file = self.storage_path / "merkle_root.json"
        self.merkle_roots_file = self.storage_path / "merkle_roots.jsonl"
        self.last_hash_file = self.storage_path / ".last_hash"
        self.genesis_pin_file = self.storage_path / "genesis_hash.pin"
        self.integrity_alerts_file = self.storage_path / "integrity_alerts.jsonl"
        self.witness_file = self.storage_path / "witness_replicas.jsonl"
        self.revocation_file = self.storage_path / "revoked_tokens.jsonl"
        self._key_history: list[dict] = []
        self._user_key_cache: dict[str, str] = {}
        self.last_hash = self._load_last_hash()
        self.event_count = self._count_events()
        self._persist_merkle_root()

        from src.audit.per_user_keys import get_per_user_key_manager
        self._per_user_key_manager = get_per_user_key_manager(self.CHAIN_KEY)
        self._file_lock = AuditChainLock(
            self.storage_path / ".chain.lock",
            timeout=AUDIT_LOCK_TIMEOUT,
        )

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

    def _read_last_chain_hash(self) -> str:
        """Read the hash on the actual last chain line, bypassing stale process state."""
        if not self.chain_file.exists():
            return self._genesis_hash()

        last_line = ""
        with open(self.chain_file) as f:
            for line in f:
                if line.strip():
                    last_line = line

        if not last_line:
            return self._genesis_hash()

        return json.loads(last_line).get("hash") or self._genesis_hash()

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

    def _event_from_chain_data(self, event_data: dict) -> AuditEvent:
        event_kwargs = {
            k: v
            for k, v in event_data.items()
            if k not in ("hash", "per_user_binding", "user_key_hash")
        }
        if "_v" not in event_data:
            event_kwargs["_v"] = None
        return AuditEvent(**event_kwargs)

    def _chain_file_sha256(self) -> str:
        digest = hashlib.sha256()
        if not self.chain_file.exists():
            return digest.hexdigest()
        with open(self.chain_file, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _write_rehashed_event(
        self,
        f,
        prev_hash: str,
        event: AuditEvent,
        include_binding: bool = True,
    ) -> str:
        if event.user_id is None:
            event.user_id = "system"

        new_hash = self._compute_hash(prev_hash, event)
        event_data = event.to_dict()
        event_data["hash"] = new_hash

        if include_binding:
            user_key = self._derive_user_key(event.user_id)
            per_user_hash = self._compute_per_user_hash(user_key, new_hash, event)
            if event.jwt_kid is not None or event.request_fingerprint is not None:
                try:
                    per_user_hash = self._per_user_key_manager.compute_binding(
                        user_id=event.user_id,
                        jwt_kid=event.jwt_kid,
                        request_fingerprint=event.request_fingerprint,
                        chain_hash=new_hash,
                        event_serialized=event.serialize(),
                    )
                except Exception:
                    pass
            event_data["per_user_binding"] = per_user_hash[:16]

        f.write(json.dumps(event_data, sort_keys=True, default=str) + "\n")
        return new_hash

    def repair_line1_hash_mismatch(self, reason: str = "line1_hash_mismatch") -> dict:
        """Archive and reseed an unanchored chain, preserving every readable event."""
        if not self.chain_file.exists():
            return {"action": "noop", "reason": "chain_missing"}

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        backup_path = self.storage_path / f"chain_line1_hash_mismatch_backup_{timestamp}.jsonl"
        temp_path = self.storage_path / f"chain_reseed_{timestamp}.jsonl"

        with self._file_lock.hold():
            source_sha256 = self._chain_file_sha256()
            source_lines = self.chain_file.read_text().splitlines()
            source_events = [json.loads(line) for line in source_lines if line.strip()]
            shutil.copy2(self.chain_file, backup_path)

            first_source = source_events[0] if source_events else {}
            genesis_event = AuditEvent(
                event_id="genesis",
                event_type="chain_genesis",
                user_id="system",
                result={
                    "origin": "audit_chain_reseed",
                    "reason": reason,
                    "source_backup": str(backup_path),
                    "source_sha256": source_sha256,
                    "preserved_event_count": len(source_events),
                    "source_line1_event_id": first_source.get("event_id"),
                    "source_line1_timestamp": first_source.get("timestamp"),
                    "source_line1_recorded_hash": first_source.get("hash"),
                },
            )

            prev_hash = self._genesis_hash()
            with open(temp_path, "w") as f:
                prev_hash = self._write_rehashed_event(f, prev_hash, genesis_event)
                for event_data in source_events:
                    prev_hash = self._write_rehashed_event(
                        f,
                        prev_hash,
                        self._event_from_chain_data(event_data),
                    )

            temp_path.replace(self.chain_file)
            self.last_hash = prev_hash
            self.last_hash_file.write_text(prev_hash)
            self.event_count = self._count_events()

        global _chain_health_cache
        _chain_health_cache = None

        self.log_tamper_alert(
            f"Line 1 hash mismatch repaired by reseeding {len(source_events)} events "
            f"from {backup_path.name}"
        )
        logger.critical(
            "Audit chain line 1 hash mismatch repaired: backup=%s preserved_events=%s",
            backup_path,
            len(source_events),
        )
        return {
            "action": "reseeded_with_genesis",
            "reason": reason,
            "backup_path": str(backup_path),
            "source_sha256": source_sha256,
            "preserved_event_count": len(source_events),
            "chain_length": self.event_count,
            "last_hash": self.last_hash,
        }

    def _first_chain_event(self) -> dict | None:
        if not self.chain_file.exists():
            return None
        with open(self.chain_file) as f:
            for line in f:
                if line.strip():
                    return json.loads(line)
        return None

    def _read_genesis_pin(self) -> str | None:
        if not self.genesis_pin_file.exists():
            return None
        value = self.genesis_pin_file.read_text().strip()
        return value or None

    def _pin_genesis_hash(self, genesis_hash: str | None) -> str | None:
        if not genesis_hash:
            return self._read_genesis_pin()
        pinned_hash = self._read_genesis_pin()
        if pinned_hash:
            return pinned_hash
        self.genesis_pin_file.write_text(f"{genesis_hash}\n")
        return genesis_hash

    def _lineage_break_metadata(
        self,
        *,
        valid: bool,
        errors: list[str],
        repair: dict | None,
    ) -> dict:
        first_event = self._first_chain_event()
        first_result = first_event.get("result", {}) if isinstance(first_event, dict) else {}
        repair_required = bool(
            not valid and errors and errors[0].startswith("Line 1: hash mismatch")
        )
        backups = sorted(self.storage_path.glob("chain_line1_hash_mismatch_backup_*.jsonl"))
        active_genesis_hash = first_event.get("hash") if first_event else None
        pinned_genesis_hash = self._pin_genesis_hash(active_genesis_hash)
        genesis_pin_matches = bool(
            active_genesis_hash is None
            or pinned_genesis_hash is None
            or active_genesis_hash == pinned_genesis_hash
        )
        traceable_reseed = bool(
            first_event
            and first_event.get("event_type") == "chain_genesis"
            and first_result.get("origin") == "audit_chain_reseed"
        )
        active_chain_traceable = bool(
            first_event is None or genesis_pin_matches or traceable_reseed
        )

        reseeding_events = []
        if first_event and first_event.get("event_type") == "chain_genesis":
            reseeding_events.append(
                {
                    "timestamp": first_event.get("timestamp"),
                    "reason": first_result.get("reason"),
                    "source_backup": first_result.get("source_backup"),
                    "source_sha256": first_result.get("source_sha256"),
                    "preserved_event_count": first_result.get("preserved_event_count"),
                }
            )

        return {
            "lineage_intact": bool(
                valid
                and active_chain_traceable
                and not repair_required
                and genesis_pin_matches
            ),
            "active_chain_traceable": bool(active_chain_traceable),
            "repair_required": repair_required,
            "auto_repair_triggered": repair is not None,
            "backup_count": len(backups),
            "backup_files": [path.name for path in backups],
            "reseeding_events": reseeding_events,
            "original_event_count": first_result.get("preserved_event_count"),
            "active_genesis_hash": (active_genesis_hash[:16] if active_genesis_hash else None),
            "pinned_genesis_hash": (
                pinned_genesis_hash[:16] if pinned_genesis_hash else None
            ),
            "genesis_pin_matches": genesis_pin_matches,
            "genesis_pin_path": str(self.genesis_pin_file),
            "active_genesis_event_id": first_event.get("event_id") if first_event else None,
        }

    def append(self, event: AuditEvent) -> str:
        """Append event to log with per-user non-repudiation binding. Thread-safe, process-safe."""
        if event.user_id is None:
            event.user_id = "system"

        user_key = self._derive_user_key(event.user_id)
        event.user_key_hash = event.compute_user_key_hash(user_key)

        try:
            with self._file_lock.hold():
                with self._lock:
                    self.last_hash = self._read_last_chain_hash()
                    self.event_count = self._count_events()
                    new_hash = self._compute_hash(self.last_hash, event)

                    per_user_hash = self._compute_per_user_hash(user_key, new_hash, event)

                    if event.jwt_kid is not None or event.request_fingerprint is not None:
                        try:
                            pk_binding = self._per_user_key_manager.compute_binding(
                                user_id=event.user_id,
                                jwt_kid=event.jwt_kid,
                                request_fingerprint=event.request_fingerprint,
                                chain_hash=new_hash,
                                event_serialized=event.serialize(),
                            )
                            per_user_hash = pk_binding
                        except Exception:
                            pass

                    event_data = event.to_dict()
                    event_data["hash"] = new_hash
                    event_data["per_user_binding"] = per_user_hash[:16]

                    with open(self.chain_file, "a") as f:
                        f.write(json.dumps(event_data, default=str) + "\n")

                    self.last_hash = new_hash
                    self.last_hash_file.write_text(new_hash)
                    self.event_count += 1
                    if self.event_count == 1:
                        self._pin_genesis_hash(new_hash)

                    cosign_args = (event.event_id, new_hash, per_user_hash, event.user_id, event.event_type)

        except AuditLockTimeout:
            logger.error("Audit lock timeout exceeded — could not append event %s", event.event_id)
            raise

        if should_db_cosign():
            _schedule_db_cosign(cosign_args)

        logger.debug(
            "Audit event %s appended, chain=%s..., user_bind=%s...",
            event.event_id,
            new_hash[:16],
            per_user_hash[:8],
        )
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

    def verify_chain(self, key: Optional[str] = None, verify_per_user: bool = True) -> tuple[bool, list[str], int]:
        """Verify chain integrity and optionally per-user bindings. Returns (valid, errors, valid_event_count)."""
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
                    stored_binding = event_data.get("per_user_binding")

                    computed_hash = self._compute_hash_with_key(
                        chain_key, prev_hash,
                        self._event_from_chain_data(event_data)
                    )

                    if computed_hash != recorded_hash:
                        errors.append(f"Line {line_num}: hash mismatch")
                        if line_num == 1:
                            logger.critical(
                                "Audit chain line 1 hash mismatch: chain is unanchored "
                                "and must be repaired before audit-dependent gates run"
                            )
                        valid_count = line_num - 1
                        break
                    else:
                        valid_count = line_num

                    prev_hash = recorded_hash

                    if verify_per_user and stored_binding and event_data.get("user_id") != "system":
                        jwt_kid = event_data.get("jwt_kid")
                        fp = event_data.get("request_fingerprint")
                        if jwt_kid is None and fp is None:
                            pass
                        else:
                            user_id = event_data.get("user_id", "system")
                            ev_kwargs = {k: v for k, v in event_data.items()
                                         if k not in ("hash", "per_user_binding")}
                            ev = AuditEvent(**ev_kwargs)
                            valid, err = self._per_user_key_manager.verify_binding(
                                user_id=user_id,
                                jwt_kid=jwt_kid,
                                request_fingerprint=fp,
                                chain_hash=recorded_hash,
                                event_serialized=ev.serialize(),
                                stored_binding=stored_binding,
                            )
                            if not valid:
                                errors.append(f"Line {line_num}: per-user binding failure for {user_id}: {err}")
                                self.log_tamper_alert(f"Per-user binding broken at line {line_num}: {err}")

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

    def get_chain_health(self, auto_repair: bool | None = None) -> dict:
        """Get chain health status for monitoring, including explicit verifier errors."""
        if auto_repair is None:
            auto_repair = os.environ.get("AUDIT_AUTO_REPAIR_LINE1", "0").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }

        valid, errors, valid_count = self.verify_chain()
        repair = None
        if (
            auto_repair
            and not valid
            and errors
            and errors[0].startswith("Line 1: hash mismatch")
        ):
            logger.warning(
                "Audit chain Line 1 hash mismatch auto-repair triggered; "
                "operator review and ADR lineage documentation are required"
            )
            repair = self.repair_line1_hash_mismatch()
            valid, errors, valid_count = self.verify_chain()

        chain_length = self._count_events()
        self.event_count = chain_length
        if valid and self.chain_file.exists():
            self.last_hash = self._load_last_hash()
        lineage_break = self._lineage_break_metadata(
            valid=valid,
            errors=errors,
            repair=repair,
        )
        lineage_intact = bool(lineage_break.get("lineage_intact"))
        status = "healthy"
        if not valid or (not lineage_intact and not auto_repair):
            status = "CRITICAL"

        return {
            "status": status,
            "chain_valid": valid,
            "chain_length": chain_length,
            "valid_events": valid_count,
            "valid_event_count": valid_count,
            "error_count": len(errors),
            "errors": errors,
            "repair": repair,
            "lineage_intact": lineage_intact,
            "auto_repair_enabled": bool(auto_repair),
            "reseeding_events": lineage_break.get("reseeding_events", []),
            "lineage_break": lineage_break,
            "db_cosign": get_db_cosign_metrics(),
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

    def log_query(self, user_id: str, query: str, jwt_kid: Optional[str] = None, request_fingerprint: Optional[str] = None) -> str:
        return self.append(AuditEvent(event_type="query", user_id=user_id, query=query, jwt_kid=jwt_kid, request_fingerprint=request_fingerprint))

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


def get_audit_log() -> ImmutableAuditLog:
    return ImmutableAuditLog()


def log_query(user_id: str, query: str, jwt_kid: Optional[str] = None, request_fingerprint: Optional[str] = None) -> str:
    return get_audit_log().log_query(user_id, query, jwt_kid=jwt_kid, request_fingerprint=request_fingerprint)


def log_plan(user_id: str, query: str, plan: dict) -> str:
    return get_audit_log().log_plan(user_id, query, plan)


def log_sql(user_id: str, sql: str, result: Optional[dict] = None) -> str:
    return get_audit_log().log_sql(user_id, sql, result)


def log_llm_call(user_id: str, prompt: str, response: dict, model: str) -> str:
    return get_audit_log().log_llm_call(user_id, prompt, response, model)


def log_anomaly(user_id: str, anomaly_type: str, details: dict, identifier: Optional[str] = None) -> str:
    return get_audit_log().log_anomaly(user_id, anomaly_type, details, identifier)


def verify_chain(verify_per_user: bool = True) -> tuple[bool, list[str], int]:
    """Verify chain integrity and optionally per-user bindings. Returns (valid, errors, valid_event_count)."""
    return get_audit_log().verify_chain(verify_per_user=verify_per_user)


_chain_health_cache: tuple[float, bool | None, dict] | None = None


def get_chain_health(auto_repair: bool | None = None) -> dict:
    """Get chain health status for monitoring. Cached for 5s to avoid repeated full-chain scans."""
    global _chain_health_cache
    now = time.time()
    if _chain_health_cache is not None:
        cached_at, cached_auto_repair, cached_result = _chain_health_cache
        if cached_auto_repair == auto_repair and now - cached_at < 5.0:
            return cached_result
    result = get_audit_log().get_chain_health(auto_repair=auto_repair)
    _chain_health_cache = (now, auto_repair, result)
    return result


def log_cost_decision(
    query_id: str,
    provider: str,
    tokens_in: int,
    tokens_out: int,
    cost_inr: float,
    persona: str,
    complexity: str,
    route_decision: str,
) -> str:
    """Log a CostGuard cost decision to the audit chain."""
    return get_audit_log().append(
        AuditEvent(
            event_type="llm_cost",
            query=query_id,
            llm_call={
                "provider": provider,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_inr": round(cost_inr, 4),
                "persona": persona,
                "complexity": complexity,
                "route_decision": route_decision,
            },
        )
    )
