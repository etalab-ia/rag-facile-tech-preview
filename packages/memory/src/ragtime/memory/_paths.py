"""Path constants for the ``.agent/`` memory layout.

All paths are relative to the workspace root (the directory containing
``ragtime.toml``).  Functions accept a ``workspace: Path`` argument and
return absolute paths.
"""

from __future__ import annotations

from pathlib import Path


# ── Relative path segments ────────────────────────────────────────────────────

AGENT_DIR = Path(".agent")
MEMORY_FILE = AGENT_DIR / "MEMORY.md"
PROFILE_FILE = AGENT_DIR / "profile.md"
LOGS_DIR = AGENT_DIR / "logs"
SESSIONS_DIR = AGENT_DIR / "sessions"


# ── Resolved helpers ──────────────────────────────────────────────────────────


def ensure_dirs(workspace: Path) -> None:
    """Create all memory directories if they don't exist."""
    for d in (AGENT_DIR, LOGS_DIR, SESSIONS_DIR):
        (workspace / d).mkdir(parents=True, exist_ok=True)
