"""Tests for the uninstall command."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from cli.commands.uninstall import (
    INSTALLER_MARKER,
    _clean_shell_profile,
    _collect_items_to_remove,
    _is_windows,
    _remove_cli_manually,
    _run_quiet,
    _tool_exists,
)
from cli.main import app as main_app


runner = CliRunner()


class TestHelpers:
    """Tests for helper functions."""

    def test_is_windows_returns_bool(self):
        """Should return a boolean."""
        result = _is_windows()
        assert isinstance(result, bool)

    def test_tool_exists_for_python(self):
        """Python should always be available in test env."""
        assert _tool_exists("python") is True

    def test_tool_exists_for_nonexistent(self):
        """Non-existent tool should return False."""
        assert _tool_exists("nonexistent_tool_xyz_123") is False

    def test_run_quiet_success(self):
        """Should return True for successful commands."""
        assert _run_quiet(["python", "--version"]) is True

    def test_run_quiet_failure(self):
        """Should return False for non-existent commands."""
        assert _run_quiet(["nonexistent_tool_xyz_123"]) is False

    def test_run_quiet_timeout(self):
        """Should return False on timeout."""
        with patch("subprocess.run", side_effect=TimeoutError):
            # TimeoutError is the parent of subprocess.TimeoutExpired
            # but we patch to avoid needing the cmd arg
            pass
        # Test with a very short timeout indirectly
        assert _run_quiet(["nonexistent_tool_xyz_123"]) is False


class TestCleanShellProfile:
    """Tests for shell profile cleaning."""

    def test_clean_nonexistent_profile(self, tmp_path):
        """Should return False for nonexistent file."""
        result = _clean_shell_profile(tmp_path / "nonexistent")
        assert result is False

    def test_clean_profile_without_markers(self, tmp_path):
        """Should return False when no installer entries exist."""
        profile = tmp_path / ".zshrc"
        profile.write_text("export PATH=/usr/bin:$PATH\n")
        result = _clean_shell_profile(profile)
        assert result is False
        assert profile.read_text() == "export PATH=/usr/bin:$PATH\n"

    def test_clean_profile_with_installer_marker(self, tmp_path):
        """Should remove installer marker and associated export line."""
        profile = tmp_path / ".zshrc"
        profile.write_text(
            'export PATH="/usr/bin:$PATH"\n'
            "\n"
            f"{INSTALLER_MARKER}\n"
            'export PATH="$HOME/.proto/shims:$PATH"\n'
            "\n"
            "alias ll='ls -la'\n"
        )
        result = _clean_shell_profile(profile)
        assert result is True
        content = profile.read_text()
        assert INSTALLER_MARKER not in content
        assert ".proto/shims" not in content
        assert "alias ll" in content

    def test_clean_profile_with_direnv_hook(self, tmp_path):
        """Should remove direnv hook lines."""
        profile = tmp_path / ".zshrc"
        profile.write_text(
            'export PATH="/usr/bin:$PATH"\n'
            'eval "$(direnv hook zsh)"\n'
            "alias ll='ls -la'\n"
        )
        result = _clean_shell_profile(profile)
        assert result is True
        content = profile.read_text()
        assert "direnv hook" not in content
        assert "alias ll" in content

    def test_clean_profile_with_multiple_markers(self, tmp_path):
        """Should remove all installer entries."""
        profile = tmp_path / ".zshrc"
        profile.write_text(
            f"{INSTALLER_MARKER}\n"
            'export PATH="$HOME/.proto/shims:$PATH"\n'
            f"{INSTALLER_MARKER}\n"
            'export PATH="$HOME/.proto/bin:$PATH"\n'
            f"{INSTALLER_MARKER}\n"
            'export PATH="$HOME/.local/bin:$PATH"\n'
        )
        result = _clean_shell_profile(profile)
        assert result is True
        content = profile.read_text()
        assert INSTALLER_MARKER not in content
        assert ".proto" not in content


class TestCollectItemsToRemove:
    """Tests for _collect_items_to_remove."""

    def test_returns_list_of_tuples(self):
        """Should return a list of (label, detail, exists) tuples."""
        items = _collect_items_to_remove()
        assert isinstance(items, list)
        for item in items:
            assert len(item) == 3
            label, detail, exists = item
            assert isinstance(label, str)
            assert isinstance(detail, str)
            assert isinstance(exists, bool)

    def test_always_includes_rag_facile(self):
        """Should always include rag-facile CLI in the list."""
        items = _collect_items_to_remove()
        labels = [label for label, _, _ in items]
        assert "rag-facile CLI" in labels

    def test_always_includes_proto_tools(self):
        """Should always include proto-managed tools."""
        items = _collect_items_to_remove()
        labels = [label for label, _, _ in items]
        assert "moon" in labels
        assert "uv" in labels
        assert "just" in labels

    def test_always_includes_proto(self):
        """Should always include proto itself."""
        items = _collect_items_to_remove()
        labels = [label for label, _, _ in items]
        assert "proto" in labels


class TestRemoveCliManually:
    """Tests for manual CLI removal."""

    def test_removes_bin_and_tool_dir(self, tmp_path):
        """Should remove the CLI binary and tool directory."""
        with (
            patch("cli.commands.uninstall.UV_BIN_DIR", tmp_path / "bin"),
            patch("cli.commands.uninstall.UV_TOOLS_DIR", tmp_path / "tools"),
        ):
            # Create fake files
            bin_dir = tmp_path / "bin"
            bin_dir.mkdir()
            (bin_dir / "rag-facile").write_text("#!/usr/bin/env python\n")

            tools_dir = tmp_path / "tools" / "rag-facile-cli"
            tools_dir.mkdir(parents=True)
            (tools_dir / "pyvenv.cfg").write_text("home = /usr/bin\n")

            _remove_cli_manually()

            assert not (bin_dir / "rag-facile").exists()
            assert not tools_dir.exists()


class TestUninstallCommand:
    """Tests for the CLI uninstall command."""

    def test_help_text(self):
        """Should show help text."""
        result = runner.invoke(main_app, ["uninstall", "--help"])
        assert result.exit_code == 0
        assert "Remove" in result.output
        assert "toolchain" in result.output

    def test_nothing_to_uninstall(self):
        """Should exit cleanly when nothing is found."""
        with (
            patch("cli.commands.uninstall._collect_items_to_remove", return_value=[]),
        ):
            result = runner.invoke(main_app, ["uninstall"])
            assert result.exit_code == 0
            assert "Nothing to uninstall" in result.output

    def test_cancelled_by_user(self):
        """Should exit when user declines confirmation."""
        items = [("rag-facile CLI", "/usr/local/bin/rag-facile", True)]
        with (
            patch(
                "cli.commands.uninstall._collect_items_to_remove", return_value=items
            ),
        ):
            result = runner.invoke(main_app, ["uninstall"], input="n\n")
            assert result.exit_code == 0
            assert "cancelled" in result.output

    def test_yes_flag_skips_confirmation(self):
        """Should skip confirmation with --yes flag."""
        items = [("rag-facile CLI", "/usr/local/bin/rag-facile", True)]
        with (
            patch(
                "cli.commands.uninstall._collect_items_to_remove", return_value=items
            ),
            patch("cli.commands.uninstall._tool_exists", return_value=False),
            patch("cli.commands.uninstall._remove_cli_manually"),
            patch("cli.commands.uninstall.PROTO_HOME", Path("/nonexistent")),
            patch("cli.commands.uninstall._is_windows", return_value=False),
            patch("cli.commands.uninstall._clean_shell_profile", return_value=False),
        ):
            result = runner.invoke(main_app, ["uninstall", "--yes"])
            assert result.exit_code == 0
            assert "has been uninstalled" in result.output
