"""Process-level concurrency lock using a PID file.

Ensures only one backfill/resume process runs at a time.
"""

from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path

_LOCK_DIR = Path(os.environ.get("TUSHARE_DB_LOCK_DIR", Path.home() / ".tushare_db"))
_LOCK_FILE = _LOCK_DIR / "process.lock"


class ConcurrencyLock:
    """File-based concurrency lock that stores the current PID."""

    def __init__(self, lock_file: Path = _LOCK_FILE):
        self._lock_file = lock_file
        self._acquired = False

    def acquire(self) -> None:
        """Acquire the lock or exit if another process holds it."""
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)

        if self._lock_file.exists():
            pid = self._read_pid()
            if pid and self._is_running(pid):
                print(
                    f"ERROR: Another tushare-db process is already running (PID {pid}).\n"
                    f"  Lock file: {self._lock_file}\n"
                    f"  If the process has crashed, delete the lock file and retry.",
                    file=sys.stderr,
                )
                sys.exit(1)
            # Stale lock — clean up
            self._lock_file.unlink(missing_ok=True)

        self._lock_file.write_text(str(os.getpid()))
        self._acquired = True
        atexit.register(self.release)

    def release(self) -> None:
        """Release the lock."""
        if self._acquired and self._lock_file.exists():
            self._lock_file.unlink(missing_ok=True)
            self._acquired = False

    def _read_pid(self) -> int | None:
        try:
            return int(self._lock_file.read_text().strip())
        except (ValueError, OSError):
            return None

    @staticmethod
    def _is_running(pid: int) -> bool:
        """Check if a process with the given PID is alive."""
        if sys.platform == "win32":
            import ctypes
            try:
                handle = ctypes.windll.kernel32.OpenProcess(0x0400, False, pid)
                if handle:
                    ctypes.windll.kernel32.CloseHandle(handle)
                    return True
                return False
            except OSError:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
