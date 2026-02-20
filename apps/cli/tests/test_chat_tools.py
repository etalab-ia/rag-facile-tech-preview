"""Tests for the chat agent tools (get_ragfacile_config, get_agents_md, get_recent_git_activity)."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from cli.commands.chat.tools import (
    get_agents_md,
    get_ragfacile_config,
    get_recent_git_activity,
    set_workspace_root,
)


@pytest.fixture(autouse=True)
def reset_workspace():
    """Reset the module-level workspace root before and after each test."""
    set_workspace_root(None)
    yield
    set_workspace_root(None)


@pytest.fixture()
def workspace(tmp_path):
    """Workspace with ragfacile.toml, AGENTS.md, and a git repo."""
    (tmp_path / "ragfacile.toml").write_text(
        "[meta]\npreset = 'balanced'\n", encoding="utf-8"
    )
    (tmp_path / "AGENTS.md").write_text(
        "# Project Architecture\n\nThis is a rag-facile workspace.\n", encoding="utf-8"
    )
    set_workspace_root(tmp_path)
    return tmp_path


# ── get_ragfacile_config ──────────────────────────────────────────────────────


class TestGetRagfacileConfig:
    def test_returns_hint_when_no_workspace(self):
        result = get_ragfacile_config()
        assert "No workspace detected" in result

    def test_returns_config_content(self, workspace):
        result = get_ragfacile_config()
        assert "balanced" in result

    def test_returns_hint_when_no_toml(self, tmp_path):
        set_workspace_root(tmp_path)
        result = get_ragfacile_config()
        assert "No ragfacile.toml found" in result


# ── get_agents_md ─────────────────────────────────────────────────────────────


class TestGetAgentsMd:
    def test_returns_hint_when_no_workspace(self):
        result = get_agents_md()
        assert "No workspace detected" in result

    def test_returns_agents_md_content(self, workspace):
        result = get_agents_md()
        assert "Project Architecture" in result
        assert "rag-facile workspace" in result

    def test_returns_hint_when_no_agents_md(self, tmp_path):
        set_workspace_root(tmp_path)
        result = get_agents_md()
        assert "No AGENTS.md found" in result


# ── get_recent_git_activity ───────────────────────────────────────────────────


class TestGetRecentGitActivity:
    def test_returns_hint_when_no_workspace(self):
        result = get_recent_git_activity()
        assert "No workspace detected" in result

    def test_returns_log_output(self, workspace):
        mock_result = MagicMock()
        mock_result.stdout = "abc1234 feat: initial commit\n"
        with patch("cli.commands.chat.tools.subprocess.run", return_value=mock_result):
            result = get_recent_git_activity()
        assert "feat: initial commit" in result

    def test_returns_no_commits_message_on_empty_log(self, workspace):
        mock_result = MagicMock()
        mock_result.stdout = ""
        with patch("cli.commands.chat.tools.subprocess.run", return_value=mock_result):
            result = get_recent_git_activity()
        assert "No commits found" in result

    def test_returns_hint_when_git_not_installed(self, workspace):
        with patch(
            "cli.commands.chat.tools.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = get_recent_git_activity()
        assert "git is not installed" in result

    def test_returns_error_on_git_failure(self, workspace):
        with patch(
            "cli.commands.chat.tools.subprocess.run",
            side_effect=subprocess.CalledProcessError(
                128, "git", stderr="not a git repo"
            ),
        ):
            result = get_recent_git_activity()
        assert "git log failed" in result
