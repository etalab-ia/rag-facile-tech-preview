"""Tests for the run_ragtime tool."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from cli.commands.learn.tools import run_ragtime, set_workspace_root


@pytest.fixture(autouse=True)
def reset_workspace():
    set_workspace_root(None)
    yield
    set_workspace_root(None)


@pytest.fixture()
def workspace(tmp_path):
    set_workspace_root(tmp_path)
    return tmp_path


class TestRunRagtime:
    def _success(self, stdout="ok"):
        r = MagicMock()
        r.returncode = 0
        r.stdout = stdout
        r.stderr = ""
        return r

    def test_runs_without_workspace(self):
        """Commands like 'version' and 'collections list' don't require a workspace."""
        with patch(
            "cli.commands.learn.tools.subprocess.run",
            return_value=self._success("0.17.0"),
        ):
            result = run_ragtime("version")
        assert "0.17.0" in result

    def test_runs_allowed_subcommand(self, workspace):
        with patch(
            "cli.commands.learn.tools.subprocess.run",
            return_value=self._success("v1.0"),
        ) as m:
            result = run_ragtime("version")
        cmd = m.call_args[0][0]
        assert cmd == ["ragtime", "version"]
        assert "v1.0" in result

    def test_rejects_unknown_subcommand(self, workspace):
        result = run_ragtime("rm -rf /")
        assert "not available" in result

    def test_rejects_empty_subcommand(self, workspace):
        result = run_ragtime("")
        assert "No subcommand" in result

    def test_passes_arguments_through(self, workspace):
        with patch(
            "cli.commands.learn.tools.subprocess.run", return_value=self._success()
        ) as m:
            run_ragtime("collections list --limit 5")
        cmd = m.call_args[0][0]
        assert cmd == ["ragtime", "collections", "list", "--limit", "5"]

    def test_returns_stderr_on_failure(self, workspace):
        r = MagicMock()
        r.returncode = 1
        r.stdout = ""
        r.stderr = "API key missing"
        with patch("cli.commands.learn.tools.subprocess.run", return_value=r):
            result = run_ragtime("collections list")
        assert "API key missing" in result

    def test_handles_missing_cli(self, workspace):
        with patch(
            "cli.commands.learn.tools.subprocess.run", side_effect=FileNotFoundError
        ):
            result = run_ragtime("version")
        assert "not found" in result.lower()

    def test_handles_timeout(self, workspace):
        with patch(
            "cli.commands.learn.tools.subprocess.run",
            side_effect=subprocess.TimeoutExpired("ragtime", 600),
        ):
            result = run_ragtime("generate-dataset ./docs -o out.jsonl")
        assert "timed out" in result.lower()

    def test_handles_invalid_shell_syntax(self, workspace):
        result = run_ragtime("collections list 'unclosed")
        assert "Invalid command syntax" in result

    def test_generate_dataset_is_allowed(self, workspace):
        with patch(
            "cli.commands.learn.tools.subprocess.run",
            return_value=self._success("done"),
        ) as m:
            run_ragtime("generate-dataset ./docs -o out.jsonl -n 20 --provider albert")
        cmd = m.call_args[0][0]
        assert cmd[1] == "generate-dataset"

    def test_returns_no_output_placeholder(self, workspace):
        with patch(
            "cli.commands.learn.tools.subprocess.run", return_value=self._success("")
        ):
            result = run_ragtime("version")
        assert result == "(no output)"
