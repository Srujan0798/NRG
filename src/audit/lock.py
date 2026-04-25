"""Process-level file locking for audit chain using fcntl.flock.

ADR-006: https://docs/adr/ADR-006-audit-chain-file-locking.md

Key invariant: the lock fd must remain open for the lifetime of the process.
Closing the fd releases the OS-level lock even if other threads/processes
are trying to acquire it. So we keep ONE fd open and reuse it.
"""

import fcntl
import contextlib
import os
import time
import atexit
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditLockTimeout(Exception):
    """Raised when lock cannot be acquired within timeout."""
    pass


class AuditChainLock:
    """Cross-process file lock using fcntl.flock with timeout.

    The lock file fd is opened once in __init__ and kept open for the
    process lifetime. fcntl.LOCK_UN releases the lock without closing
    the fd; the fd is only closed when the lock object is garbage
    collected or when close() is explicitly called.
    """

    _all_locks: list["AuditChainLock"] = []

    def __init__(self, lock_path: str | Path, timeout: float = 5.0):
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self._fd = None
        self._open_fd()

    def _open_fd(self) -> None:
        """Open lock file fd once, keep open for process lifetime."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = open(self.lock_path, "w", encoding="utf-8")
        AuditChainLock._all_locks.append(self)

    def acquire(self) -> bool:
        """Acquire exclusive lock with timeout. Returns True on success."""
        start = time.monotonic()
        while True:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except BlockingIOError:
                if time.monotonic() - start >= self.timeout:
                    raise AuditLockTimeout(
                        f"Could not acquire audit lock within {self.timeout}s "
                        f"(path={self.lock_path})"
                    )
                time.sleep(0.01)

    def release(self) -> None:
        """Release exclusive lock. Does NOT close the fd — fd stays open."""
        if self._fd is not None:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            except (OSError, IOError):
                pass

    def close(self) -> None:
        """Permanently close the lock fd. Call on process shutdown."""
        if self._fd is not None:
            try:
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
                self._fd.close()
            except (OSError, IOError):
                pass
            finally:
                self._fd = None
                if self in AuditChainLock._all_locks:
                    AuditChainLock._all_locks.remove(self)

    @contextlib.contextmanager
    def hold(self):
        """Context manager: acquire on enter, release on exit."""
        self.acquire()
        try:
            yield
        finally:
            self.release()

    def __del__(self):
        self.close()


def close_all_locks():
    """Close all audit locks on process exit."""
    for lock in AuditChainLock._all_locks[:]:
        lock.close()


atexit.register(close_all_locks)
