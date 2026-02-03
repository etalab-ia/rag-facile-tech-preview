# Project Knowledge: RAG Starter Kit

## 0. Global Rules Compliance
- **CRITICAL**: You **MUST** always create a new git branch for every task. Never work directly on `main`.
- **CRITICAL**: You **MUST** run linting (`ruff format`, `ruff check`) and verification **before** every commit.
- **Rule**: Read and follow all Global User Rules defined in the system prompt without exception.

## 1. Project Architecture & Toolchain
- **Fact**: Python 3.14 monorepo managed by **moon** (repo tooling) and **uv** (package manager).
- **Rule**: Always use `uv sync` to install dependencies and update lockfiles. Never use `pip` or `poetry`.
- **Rule**: Linting and formatting are handled by `ruff` (v0.9.3+), and type checking by `ty` (Astral's type checker).

## 2. UV Workspace Configuration Pattern
- **Insight**: For development tools (like `ty` (LSP) or `mypy`) to correctly resolve imports from local workspace packages (e.g., `packages/sample`), those packages **must** be explicitly listed in the root `pyproject.toml` under `dependencies` **and** mapped in `[tool.uv.sources]`.
- **Example**:
    ```toml
    # pyproject.toml
    [project]
    dependencies = ["my-lib"]

    [tool.uv.sources]
    my-lib = { workspace = true }
    ```

## 3. CLI Development Patterns
- **Fact**: The project CLI is named `rag-facile`.
- **Fact**: CLI displays ASCII banner on every invocation (printed at module load time).

## 4. Configuration Specifics
- **Gotcha**: The `ty` pre-commit hook requires the `entry` to be explicitly set to `uv run ty check`. The default entry may fail or lack the necessary context.
