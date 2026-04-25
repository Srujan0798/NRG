"""Process-level file locking for audit chain using fcntl.flock.

ADR-006: https://docs/adr/ADR-006-audit-chain-file-locking.md
"""

import fcntl
import contextlib
import os
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditLockTimeout(Exception):
    """Raised when lock cannot be acquired within timeout."""
    pass


class AuditChainLock:
    """Cross-process file lock using fcntl.flock with timeout."""

    def __init__(self, lock_path: str | Path, timeout: float = 5.0):
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self._fd = None

    def acquire(self) -> bool:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = open(self.lock_path, "w")
        start = time.monotonic()
        while True:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except BlockingIOError:
                if time.monotonic() - start >= self.timeout:
                    self._fd.close()
                    self._fd = None
                    raise AuditLockTimeout(
                        f"Could not acquire audit lock within {self.timeout}s "
                        f"(path={self.lock_path})"
                    )
                time.sleep(0.01)

    def release(self) -> None:
        if self._fd is not None:
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            self._fd.close()
            self._fd = None

    @contextlib.contextmanager
    def hold(self):
        """Context manager: acquire on enter, release on exit."""
        self.acquire()
        try:
            yield
        finally:
            self.release()
