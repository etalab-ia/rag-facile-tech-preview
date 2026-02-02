# Contributing to RAG Facile

Thank you for your interest in contributing to RAG Facile! This document is for **maintainers** who want to understand the architecture and contribute to the project itself.

> **Note**: If you just want to use RAG Facile to create a new app, see the [README](README.md).

## Architecture Overview

RAG Facile uses an **Init + Patch** architecture with **Golden Master** templates:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG Facile Monorepo                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  apps/ (Golden Masters)          .moon/templates/ (Generated)       │
│  ├── chainlit-chat/ ──────────►  ├── chainlit-chat/                │
│  ├── reflex-chat/   ──────────►  ├── reflex-chat/                  │
│  └── cli/                        ├── sys-config/                    │
│                                  └── pdf-context/                   │
│  packages/                                                          │
│  └── pdf-context/   ──────────►  (copied to templates)             │
│                                                                     │
│  tools/                                                             │
│  └── generate_templates.py  ◄── Transforms apps → templates        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    User Workspace (Generated)                       │
├─────────────────────────────────────────────────────────────────────┤
│  rf generate workspace my-app                                       │
│                                                                     │
│  1. moon init          → Bootstrap workspace                        │
│  2. moon generate      → Apply sys-config (toolchain, workspace)    │
│  3. moon generate      → Generate selected app (chainlit/reflex)    │
│  4. moon generate      → Generate selected modules (pdf, etc.)      │
│  5. Create .env        → Write user's API credentials               │
│  6. uv sync            → Install dependencies                       │
│  7. moon run :dev      → Start development server                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Concepts

#### Golden Masters
The apps in `apps/` are **living, working applications** that serve as the source of truth. Maintainers develop and test features here first.

#### Template Generation
Running `moon run tools:generate-all` transforms Golden Masters into parameterized Moon templates:

1. **LibCST transformation** - Python code is parsed and string literals are parameterized
2. **Import parameterization** - Module imports are converted to use template variables
3. **File renaming** - Directories/files are renamed with Tera template syntax

#### Init + Patch
Instead of generating everything from scratch, we:
1. **Init** - Use `moon init` to bootstrap a standard Moon workspace
2. **Patch** - Apply RAG Facile-specific configuration via `sys-config` template

This leverages Moon's battle-tested scaffolding while adding our customizations.

## Development Setup

### Prerequisites

- **Python 3.13**
- **uv** (package manager)
- **moon** (monorepo manager)
- **git**

### 1. Clone the Repository

```bash
git clone https://github.com/etalab-ia/rag-facile.git
cd rag-facile
```

### 2. Install Dependencies

```bash
just setup
```

This installs all dependencies and sets up pre-commit hooks for linting/formatting.

### 3. Environment Variables

Copy the example environment file and add your Albert API credentials:

```bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and OPENAI_BASE_URL
```

## Project Structure

```
rag-facile/
├── apps/                    # Golden Master applications
│   ├── chainlit-chat/       # ChainLit chat interface
│   ├── reflex-chat/         # Reflex chat interface
│   ├── admin/               # Admin UI (Streamlit)
│   ├── ingestion/           # Data ingestion pipeline
│   └── cli/                 # The `rf` command-line tool
├── packages/                # Shared packages
│   └── pdf-context/         # PDF processing module
├── tools/                   # Development tools
│   └── generate_templates.py  # Template generator
├── .moon/
│   └── templates/           # Generated Moon templates (do not edit directly!)
├── pyproject.toml           # Root workspace configuration
└── justfile                 # Command recipes
```

## Common Tasks

### Running Golden Master Apps

```bash
# Run apps directly from the monorepo
moon run chainlit-chat:dev
moon run reflex-chat:dev
```

### Regenerating Templates

After making changes to Golden Master apps:

```bash
moon run tools:generate-all
```

This regenerates all templates in `.moon/templates/`.

### Running CLI Tests

```bash
moon run cli:test
```

### Testing the Full Generation Flow

```bash
# Generate a test workspace
rm -rf /tmp/test-app && rf generate workspace /tmp/test-app
```

## Making Changes

### Modifying an App Template

1. **Edit the Golden Master** in `apps/<app-name>/`
2. **Test locally** with `moon run <app-name>:dev`
3. **Regenerate templates** with `moon run tools:generate-all`
4. **Test generation** with `rf generate workspace /tmp/test`
5. **Commit both** the Golden Master and generated templates

### Adding a New Module

1. Create the package in `packages/<module-name>/`
2. Add template generation in `tools/generate_templates.py`
3. Register in `apps/cli/src/cli/commands/generate.py` (MODULES dict)
4. Regenerate templates

### Modifying the CLI

The CLI lives in `apps/cli/`. Key files:
- `src/cli/main.py` - Entry point and command registration
- `src/cli/commands/generate.py` - The `rf generate workspace` command

## Template Parameterization

Templates use [Tera](https://keats.github.io/tera/) syntax (similar to Jinja2):

| Pattern | Description |
|---------|-------------|
| `{{ project_name }}` | User's project name (e.g., "my-app") |
| `{{ project_name \| replace(from='-', to='_') }}` | Python-safe name (e.g., "my_app") |
| `{{ description }}` | Project description |
| `{{ openai_api_key }}` | User's API key |
| `{% if use_pdf %}...{% endif %}` | Conditional content |

### Boolean Flags

Feature flags like `use_pdf` and `use_chroma` are passed to `moon generate` as:
```bash
moon generate chainlit-chat --defaults -- --use_pdf --use_chroma
```

## Gotchas

- **Typer CLI** - Collapses if only one command exists; maintain at least 2 commands
- **macOS /tmp** - Resolves to `/private/tmp`; normalize for cleaner output
- **moon init** - Must run FROM the target directory, not with path argument
- **moon generate** - Needs `generator.templates` in workspace.yml to find templates
- **Moon boolean vars** - Pass as `-- --flag` not `-- flag=true`
- **Moon commands** - Run directly, not through venv; use `uv run` in task commands
- **.python-version** - Add to pin Python version for generated workspaces

## Pull Request Process

1. **Fork and clone** the repository
2. **Create a branch**: `git checkout -b feature/your-feature`
3. **Make changes** to Golden Masters (not templates directly!)
4. **Regenerate templates**: `moon run tools:generate-all`
5. **Run tests**: `moon run cli:test`
6. **Test generation**: `rf generate workspace /tmp/test`
7. **Commit** both source and generated changes
8. **Push** and create a pull request

## Getting Help

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues and discussions first

## License

By contributing to RAG Facile, you agree that your contributions will be licensed under the same license as the project.
