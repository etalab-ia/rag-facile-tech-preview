"""Tests for collections CLI commands."""

from unittest.mock import patch

import respx
from typer.testing import CliRunner

from cli.main import app as main_app

runner = CliRunner()


class TestListCollections:
    """Tests for 'ragtime collections list' command."""

    @patch.dict("os.environ", {"ALBERT_API_KEY": "test-key"})
    @respx.mock
    def test_list_collections_success(self, respx_mock):
        """List collections displays table with collection info."""
        # Mock the list_collections API response
        mock_response = {
            "data": [
                {
                    "id": 123,
                    "name": "Test Collection",
                    "description": "A test collection",
                    "documents": 42,
                    "visibility": "public",
                },
                {
                    "id": 456,
                    "name": "Private Collection",
                    "description": "Private docs",
                    "documents": 10,
                    "visibility": "private",
                },
            ],
            "total": 2,
        }
        respx_mock.get("https://albert.api.etalab.gouv.fr/v1/collections").respond(
            json=mock_response
        )

        result = runner.invoke(main_app, ["collections", "list"])

        assert result.exit_code == 0
        assert "Test Collection" in result.output
        assert "123" in result.output
        assert "42" in result.output
        assert "public" in result.output

    @patch.dict("os.environ", {"ALBERT_API_KEY": "test-key"})
    @respx.mock
    def test_list_collections_empty(self, respx_mock):
        """List collections with no results shows helpful message."""
        mock_response = {"data": [], "total": 0}
        respx_mock.get("https://albert.api.etalab.gouv.fr/v1/collections").respond(
            json=mock_response
        )

        result = runner.invoke(main_app, ["collections", "list"])

        assert result.exit_code == 0
        assert "No collections found" in result.output

    def test_list_collections_no_api_key(self):
        """List collections without API key shows error."""
        # Clear both possible env var names
        import os

        env = os.environ.copy()
        env.pop("ALBERT_API_KEY", None)
        env.pop("OPENAI_API_KEY", None)

        with patch.dict("os.environ", env, clear=True):
            result = runner.invoke(main_app, ["collections", "list"])

        assert result.exit_code == 1
        assert "ALBERT_API_KEY" in result.output or "OPENAI_API_KEY" in result.output


class TestEnableDisable:
    """Tests for 'ragtime collections enable/disable' commands."""

    def test_enable_collection(self, tmp_path):
        """Enable collection adds to config."""
        config_file = tmp_path / "ragtime.toml"
        config_file.write_text("[storage]\ncollections = [123]\n")

        result = runner.invoke(
            main_app,
            ["collections", "enable", "456", "--config", str(config_file)],
        )

        assert result.exit_code == 0
        assert "Enabled collection" in result.output
        assert "456" in result.output

        # Verify config was updated
        content = config_file.read_text()
        assert "456" in content

    def test_enable_collection_already_enabled(self, tmp_path):
        """Enable collection that's already in config shows message."""
        config_file = tmp_path / "ragtime.toml"
        config_file.write_text("[storage]\ncollections = [123, 456]\n")

        result = runner.invoke(
            main_app,
            ["collections", "enable", "456", "--config", str(config_file)],
        )

        assert result.exit_code == 0
        assert "already enabled" in result.output

    def test_disable_collection(self, tmp_path):
        """Disable collection removes from config."""
        config_file = tmp_path / "ragtime.toml"
        config_file.write_text("[storage]\ncollections = [123, 456]\n")

        result = runner.invoke(
            main_app,
            ["collections", "disable", "456", "--config", str(config_file)],
        )

        assert result.exit_code == 0
        assert "Disabled collection" in result.output
        assert "456" in result.output

    def test_disable_collection_not_in_config(self, tmp_path):
        """Disable collection that's not in config shows message."""
        config_file = tmp_path / "ragtime.toml"
        config_file.write_text("[storage]\ncollections = [123]\n")

        result = runner.invoke(
            main_app,
            ["collections", "disable", "999", "--config", str(config_file)],
        )

        assert result.exit_code == 0
        assert "not in config" in result.output


class TestUploadDocuments:
    """Tests for 'ragtime collections upload' command."""

    def test_expand_paths_filters_by_extension(self, tmp_path):
        """Test that _expand_paths only returns supported file types."""
        from cli.commands.collections import _expand_paths

        # Create test files
        (tmp_path / "doc.pdf").write_text("pdf")
        (tmp_path / "doc.md").write_text("md")
        (tmp_path / "doc.html").write_text("html")
        (tmp_path / "doc.txt").write_text("txt")  # Not supported
        (tmp_path / "doc.docx").write_text("docx")  # Not supported

        files = _expand_paths([tmp_path])

        file_names = [f.name for f in files]
        assert "doc.pdf" in file_names
        assert "doc.md" in file_names
        assert "doc.html" in file_names
        assert "doc.txt" not in file_names
        assert "doc.docx" not in file_names

    def test_expand_paths_with_pattern(self, tmp_path):
        """Test that _expand_paths respects glob pattern."""
        from cli.commands.collections import _expand_paths

        # Create test files
        (tmp_path / "report.pdf").write_text("report")
        (tmp_path / "notes.md").write_text("notes")

        files = _expand_paths([tmp_path], pattern="report")

        file_names = [f.name for f in files]
        assert "report.pdf" in file_names
        assert "notes.md" not in file_names


class TestCreateCollection:
    """Tests for 'ragtime collections create' command."""

    @patch.dict("os.environ", {"ALBERT_API_KEY": "test-key"})
    @respx.mock
    def test_create_collection_success(self, respx_mock, tmp_path):
        """Create collection with default settings."""
        mock_create_response = {
            "id": 789,
            "name": "New Collection",
            "visibility": "private",
            "documents": 0,
        }
        respx_mock.post("https://albert.api.etalab.gouv.fr/v1/collections").respond(
            json=mock_create_response
        )

        config_file = tmp_path / "ragtime.toml"
        config_file.write_text("[storage]\ncollections = []\n")

        result = runner.invoke(
            main_app,
            ["collections", "create", "New Collection", "--config", str(config_file)],
        )

        assert result.exit_code == 0
        assert "Created collection" in result.output
        assert "789" in result.output

    @patch.dict("os.environ", {"ALBERT_API_KEY": "test-key"})
    @respx.mock
    def test_create_collection_public_visibility(self, respx_mock, tmp_path):
        """Create collection with public visibility."""
        mock_create_response = {
            "id": 790,
            "name": "Public Collection",
            "visibility": "public",
            "documents": 0,
        }
        respx_mock.post("https://albert.api.etalab.gouv.fr/v1/collections").respond(
            json=mock_create_response
        )

        config_file = tmp_path / "ragtime.toml"
        config_file.write_text("[storage]\ncollections = []\n")

        result = runner.invoke(
            main_app,
            [
                "collections",
                "create",
                "Public Collection",
                "--visibility",
                "public",
                "--config",
                str(config_file),
            ],
        )

        assert result.exit_code == 0
        assert "public" in result.output


class TestShowCollection:
    """Tests for 'ragtime collections show' command."""

    @patch.dict("os.environ", {"ALBERT_API_KEY": "test-key"})
    @respx.mock
    def test_show_collection_success(self, respx_mock):
        """Show collection displays details."""
        mock_list_response = {
            "data": [
                {
                    "id": 123,
                    "name": "Test Collection",
                    "description": "A test collection",
                    "documents": 42,
                    "visibility": "public",
                }
            ],
            "total": 1,
        }
        respx_mock.get("https://albert.api.etalab.gouv.fr/v1/collections").respond(
            json=mock_list_response
        )

        result = runner.invoke(main_app, ["collections", "show", "123"])

        assert result.exit_code == 0
        assert "Test Collection" in result.output
        assert "42" in result.output

    @patch.dict("os.environ", {"ALBERT_API_KEY": "test-key"})
    @respx.mock
    def test_show_collection_with_docs(self, respx_mock):
        """Show collection with --docs flag lists documents."""
        mock_list_response = {
            "data": [
                {
                    "id": 123,
                    "name": "Test Collection",
                    "description": "A test collection",
                    "documents": 2,
                    "visibility": "public",
                }
            ],
            "total": 1,
        }
        mock_docs_response = {
            "data": [
                {
                    "id": 1,
                    "name": "doc1.pdf",
                    "status": "completed",
                    "collection_id": 123,
                    "created": 1704067200,
                },
                {
                    "id": 2,
                    "name": "doc2.pdf",
                    "status": "completed",
                    "collection_id": 123,
                    "created": 1704067200,
                },
            ],
            "total": 2,
        }
        respx_mock.get("https://albert.api.etalab.gouv.fr/v1/collections").respond(
            json=mock_list_response
        )
        respx_mock.get("https://albert.api.etalab.gouv.fr/v1/documents").respond(
            json=mock_docs_response
        )

        result = runner.invoke(main_app, ["collections", "show", "123", "--docs"])

        assert result.exit_code == 0
        assert "doc1.pdf" in result.output
        assert "doc2.pdf" in result.output


class TestDeleteCollection:
    """Tests for 'ragtime collections delete' command."""

    @patch.dict("os.environ", {"ALBERT_API_KEY": "test-key"})
    @respx.mock
    def test_delete_collection_with_force(self, respx_mock, tmp_path):
        """Delete collection with --force flag skips confirmation."""
        mock_list_response = {
            "data": [
                {
                    "id": 123,
                    "name": "Test Collection",
                    "documents": 5,
                    "visibility": "private",
                }
            ],
            "total": 1,
        }
        respx_mock.get("https://albert.api.etalab.gouv.fr/v1/collections").respond(
            json=mock_list_response
        )
        respx_mock.delete(
            "https://albert.api.etalab.gouv.fr/v1/collections/123"
        ).respond(204)

        config_file = tmp_path / "ragtime.toml"
        config_file.write_text("[storage]\ncollections = [123]\n")

        result = runner.invoke(
            main_app,
            ["collections", "delete", "123", "--force", "--config", str(config_file)],
        )

        assert result.exit_code == 0
        assert "Deleted collection" in result.output
