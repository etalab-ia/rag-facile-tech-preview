"""Bootstrap context loader for session start.

Assembles a formatted string from:
  1. Semantic Store (``MEMORY.md`` — capped at 200 lines)
  2. Profile (``profile.md``)
  3. Recent Episodic Logs (today + yesterday)

The result is injected into the first user turn of the session so the
model pays full attention to it (instead of burying it at the end of
smolagents' long built-in system prompt).
"""

from __future__ import annotations

from pathlib import Path

from rag_facile.memory._paths import PROFILE_FILE
from rag_facile.memory.stores import EpisodicLog, SemanticStore


# Default character budget for the injected context (~2000 tokens).
MAX_CONTEXT_CHARS = 8000

# Separator used between sections.
_SEP = "\n\n---\n\n"


def bootstrap_context(
    workspace: Path, *, log_days: int = 2, max_chars: int = MAX_CONTEXT_CHARS
) -> str:
    """Return the combined memory context for the start of a session.

    Sections are added in priority order (semantic store > profile >
    episodic logs).  If the total exceeds *max_chars*, lower-priority
    sections are truncated or dropped to fit.

    Parameters
    ----------
    workspace:
        Root directory containing ``.agent/``.
    log_days:
        Number of past days of episodic logs to include (default 2).
    max_chars:
        Maximum total characters for the combined context.

    Returns
    -------
    str
        Formatted context string (may be empty if no memory files exist).
    """
    sections: list[str] = []
    remaining = max_chars

    # 1. Semantic store (highest priority — curated facts, capped at 200 lines)
    semantic = SemanticStore.load(workspace)
    if semantic:
        section = f"[Memory — Semantic Store]\n{semantic}"
        sections.append(section)
        remaining -= len(section) + len(_SEP)

    # 2. Profile (small, almost always fits)
    profile_path = workspace / PROFILE_FILE
    if profile_path.exists():
        profile = profile_path.read_text(encoding="utf-8").strip()
        if profile:
            section = f"[Memory — Profile]\n{profile}"
            if len(section) <= remaining:
                sections.append(section)
                remaining -= len(section) + len(_SEP)

    # 3. Recent episodic logs (lowest priority — truncated to fit budget)
    if remaining > 100:  # don't bother if barely any room
        logs = EpisodicLog.read_recent(workspace, days=log_days)
        if logs:
            section = f"[Memory — Recent Conversations]\n{logs}"
            if len(section) > remaining:
                # Truncate logs to fit, keeping the beginning (newest entries)
                header = "[Memory — Recent Conversations]\n"
                truncation_marker = "\n…(truncated)"
                available = remaining - len(header) - len(truncation_marker)
                section = header + logs[:available] + truncation_marker
            sections.append(section)

    if not sections:
        return ""

    return _SEP.join(sections)
