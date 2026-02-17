"""Tests for the upgrade command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cli.commands.upgrade import INSTALL_URL
from cli.main import app as main_app


runner = CliRunner()


class TestInstallUrl:
    """Tests for the install URL template."""

    def test_url_contains_branch_placeholder(self):
        """URL template should have a branch placeholder."""
        assert "{branch}" in INSTALL_URL

    def test_url_formats_with_main(self):
        """Should format correctly with main branch."""
        url = INSTALL_URL.format(branch="main")
        assert "main" in url
        assert "{branch}" not in url

    def test_url_formats_with_custom_branch(self):
        """Should format correctly with a custom branch."""
        url = INSTALL_URL.format(branch="feat/test")
        assert "feat/test" in url


class TestUpgradeCommand:
    """Tests for the CLI upgrade command."""

    def test_help_text(self):
        """Should show help text."""
        result = runner.invoke(main_app, ["upgrade", "--help"])
        assert result.exit_code == 0
        assert "latest version" in result.output

    def test_successful_upgrade(self):
        """Should report success when uv tool install succeeds."""
        mock_install = MagicMock(returncode=0, stdout="", stderr="")
        mock_version = MagicMock(returncode=0, stdout="rag-facile v0.14.0\n", stderr="")

        with patch("subprocess.run", side_effect=[mock_install, mock_version]):
            result = runner.invoke(main_app, ["upgrade"])
            assert result.exit_code == 0
            assert "Upgraded successfully" in result.output

    def test_failed_upgrade(self):
        """Should report error when uv tool install fails."""
        mock_result = MagicMock(returncode=1, stdout="", stderr="network error")

        with patch("subprocess.run", return_value=mock_result):
            result = runner.invoke(main_app, ["upgrade"])
            assert result.exit_code == 1
            assert "failed" in result.output

    def test_uv_not_installed(self):
        """Should report error when uv is not available."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = runner.invoke(main_app, ["upgrade"])
            assert result.exit_code == 1
            assert "uv is not installed" in result.output

    def test_custom_branch(self):
        """Should pass custom branch to uv tool install."""
        mock_install = MagicMock(returncode=0, stdout="", stderr="")
        mock_version = MagicMock(returncode=0, stdout="rag-facile v0.14.0\n", stderr="")

        with patch(
            "subprocess.run", side_effect=[mock_install, mock_version]
        ) as mock_run:
            result = runner.invoke(main_app, ["upgrade", "--branch", "develop"])
            assert result.exit_code == 0
            # Verify the branch was used in the install URL
            call_args = mock_run.call_args_list[0]
            cmd = call_args[0][0]
            assert any("develop" in str(arg) for arg in cmd)

    def test_timeout(self):
        """Should report error on timeout."""
        import subprocess

        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="uv", timeout=120),
        ):
            result = runner.invoke(main_app, ["upgrade"])
            assert result.exit_code == 1
            assert "timed out" in result.output
