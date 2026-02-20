"""Tests for list_collections and run_generate_dataset tools."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from cli.commands.chat.tools import (
    list_collections,
    run_generate_dataset,
    set_workspace_root,
)


@pytest.fixture(autouse=True)
def reset_workspace():
    set_workspace_root(None)
    yield
    set_workspace_root(None)


@pytest.fixture()
def workspace(tmp_path):
    set_workspace_root(tmp_path)
    return tmp_path


@pytest.fixture()
def docs_dir(tmp_path):
    d = tmp_path / "docs"
    d.mkdir()
    (d / "guide.md").write_text("# Guide\nSome content.", encoding="utf-8")
    return d


# ── list_collections ──────────────────────────────────────────────────────────


class TestListCollections:
    def _mock_collection(self, id_, name, visibility="public", documents=100):
        col = MagicMock()
        col.id = id_
        col.name = name
        col.visibility = visibility
        col.documents = documents
        col.description = None
        return col

    def test_returns_table_with_collections(self):
        col1 = self._mock_collection(1, "Service Public")
        col2 = self._mock_collection(2, "My Private", visibility="private")
        mock_result = MagicMock()
        mock_result.data = [col1, col2]

        with patch("albert.AlbertClient") as MockClient:
            MockClient.return_value.list_collections.return_value = mock_result
            result = list_collections()

        assert "Service Public" in result
        assert "My Private" in result
        assert "1" in result

    def test_shows_public_ids_hint(self):
        col = self._mock_collection(42, "Légifrance", visibility="public")
        mock_result = MagicMock()
        mock_result.data = [col]

        with patch("albert.AlbertClient") as MockClient:
            MockClient.return_value.list_collections.return_value = mock_result
            result = list_collections()

        assert "42" in result
        assert "storage.collections" in result

    def test_returns_hint_when_no_collections(self):
        mock_result = MagicMock()
        mock_result.data = []

        with patch("albert.AlbertClient") as MockClient:
            MockClient.return_value.list_collections.return_value = mock_result
            result = list_collections()

        assert "No collections found" in result

    def test_handles_missing_api_key(self):
        with patch("albert.AlbertClient", side_effect=ValueError("No API key")):
            result = list_collections()
        assert "not configured" in result

    def test_handles_http_error(self):
        import httpx

        with patch("albert.AlbertClient") as MockClient:
            MockClient.return_value.list_collections.side_effect = (
                httpx.HTTPStatusError("403", request=MagicMock(), response=MagicMock())
            )
            result = list_collections()
        assert "Failed" in result


# ── run_generate_dataset ──────────────────────────────────────────────────────


class TestRunGenerateDataset:
    def test_returns_hint_when_no_workspace(self, docs_dir):
        result = run_generate_dataset(str(docs_dir), "out.jsonl")
        assert "No workspace detected" in result

    def test_returns_error_when_docs_path_missing(self, workspace):
        result = run_generate_dataset("/nonexistent/path", "out.jsonl")
        assert "does not exist" in result

    def test_returns_error_when_docs_path_is_file(self, workspace, tmp_path):
        f = tmp_path / "file.md"
        f.write_text("x")
        result = run_generate_dataset(str(f), "out.jsonl")
        assert "not a directory" in result

    def test_success(self, workspace, docs_dir):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Generated 20 Q&A pairs."
        with patch("cli.commands.chat.tools.subprocess.run", return_value=mock_result):
            result = run_generate_dataset(str(docs_dir), "out.jsonl", num_questions=20)
        assert "✓" in result
        assert "out.jsonl" in result

    def test_failure_returns_stderr(self, workspace, docs_dir):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "API key invalid"
        mock_result.stdout = ""
        with patch("cli.commands.chat.tools.subprocess.run", return_value=mock_result):
            result = run_generate_dataset(str(docs_dir), "out.jsonl")
        assert "API key invalid" in result

    def test_timeout(self, workspace, docs_dir):
        with patch(
            "cli.commands.chat.tools.subprocess.run",
            side_effect=subprocess.TimeoutExpired("rag-facile", 600),
        ):
            result = run_generate_dataset(str(docs_dir), "out.jsonl")
        assert "timed out" in result.lower()

    def test_missing_cli(self, workspace, docs_dir):
        with patch(
            "cli.commands.chat.tools.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = run_generate_dataset(str(docs_dir), "out.jsonl")
        assert "not found" in result.lower()

    def test_clamps_num_questions(self, workspace, docs_dir):
        """num_questions is clamped to [1, 100]."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        with patch(
            "cli.commands.chat.tools.subprocess.run", return_value=mock_result
        ) as mock_run:
            run_generate_dataset(str(docs_dir), "out.jsonl", num_questions=999)
        cmd = mock_run.call_args[0][0]
        assert "--num-questions" in cmd
        assert "100" in cmd

    def test_uses_albert_provider(self, workspace, docs_dir):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        with patch(
            "cli.commands.chat.tools.subprocess.run", return_value=mock_result
        ) as mock_run:
            run_generate_dataset(str(docs_dir), "out.jsonl")
        cmd = mock_run.call_args[0][0]
        assert "--provider" in cmd
        assert "albert" in cmd
