"""Tests for the bootstrap context loader."""

from ragtime.memory.context import bootstrap_context
from ragtime.memory.stores import EpisodicLog, SemanticStore


class TestBootstrapContext:
    def test_returns_empty_when_no_files(self, tmp_path):
        assert bootstrap_context(tmp_path) == ""

    def test_includes_semantic_store(self, tmp_path):
        SemanticStore.create(tmp_path)
        result = bootstrap_context(tmp_path)
        assert "Semantic Store" in result
        assert "User Identity" in result

    def test_includes_profile(self, tmp_path):
        agent_dir = tmp_path / ".agent"
        agent_dir.mkdir(parents=True)
        (agent_dir / "profile.md").write_text(
            "# Profile\n- Language: fr\n", encoding="utf-8"
        )
        result = bootstrap_context(tmp_path)
        assert "Profile" in result
        assert "Language: fr" in result

    def test_includes_recent_logs(self, tmp_path):
        EpisodicLog.append_turn(tmp_path, "user", "Hello memory")
        result = bootstrap_context(tmp_path)
        assert "Recent Conversations" in result
        assert "Hello memory" in result

    def test_combines_all_sections(self, tmp_path):
        SemanticStore.create(tmp_path)
        agent_dir = tmp_path / ".agent"
        (agent_dir / "profile.md").write_text(
            "# Profile\n- Language: en\n", encoding="utf-8"
        )
        EpisodicLog.append_turn(tmp_path, "user", "Test turn")

        result = bootstrap_context(tmp_path)
        assert "Semantic Store" in result
        assert "Profile" in result
        assert "Recent Conversations" in result
        # Sections separated by dividers
        assert "---" in result

    def test_respects_log_days(self, tmp_path):
        logs_dir = tmp_path / ".agent" / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "2020-01-01.md").write_text("# Old\nOld entry")
        (logs_dir / "2099-12-31.md").write_text("# Future\nFuture entry")

        result = bootstrap_context(tmp_path, log_days=1)
        assert "Future entry" in result
        assert "Old entry" not in result


class TestBootstrapContextBudget:
    def test_truncates_logs_when_over_budget(self, tmp_path):
        SemanticStore.create(tmp_path)
        # Create a large episodic log
        large_log = "Important content. " * 500  # ~9500 chars
        EpisodicLog.append_turn(tmp_path, "user", large_log)

        result = bootstrap_context(tmp_path, max_chars=2000)
        assert len(result) <= 2200  # allow some slack for headers
        assert "Semantic Store" in result  # highest priority kept
        assert "truncated" in result  # logs were truncated

    def test_drops_profile_when_no_room(self, tmp_path):
        # Create a large semantic store that fills the budget
        SemanticStore.create(tmp_path)
        for i in range(50):
            SemanticStore.add_entry(
                tmp_path, "Key Facts", f"Important fact number {i} with extra detail"
            )

        agent_dir = tmp_path / ".agent"
        (agent_dir / "profile.md").write_text(
            "# Profile\n" + "- Detail\n" * 100, encoding="utf-8"
        )

        result = bootstrap_context(tmp_path, max_chars=1500)
        assert "Semantic Store" in result

    def test_respects_large_budget(self, tmp_path):
        SemanticStore.create(tmp_path)
        EpisodicLog.append_turn(tmp_path, "user", "Short message")
        agent_dir = tmp_path / ".agent"
        (agent_dir / "profile.md").write_text(
            "# Profile\n- Language: en\n", encoding="utf-8"
        )

        result = bootstrap_context(tmp_path, max_chars=50000)
        assert "Semantic Store" in result
        assert "Profile" in result
        assert "Recent Conversations" in result
        assert "truncated" not in result  # nothing needs truncating

    def test_skips_logs_when_remaining_too_small(self, tmp_path):
        # Fill most of the budget with semantic store
        SemanticStore.create(tmp_path)
        for i in range(30):
            SemanticStore.add_entry(tmp_path, "Key Facts", f"Fact {i} data")
        EpisodicLog.append_turn(tmp_path, "user", "Test turn")

        # Very tight budget — logs section requires >100 chars remaining
        result = bootstrap_context(tmp_path, max_chars=800)
        assert "Semantic Store" in result
