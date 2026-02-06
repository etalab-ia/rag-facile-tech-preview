# RAG Facile development tasks

# Use PowerShell on Windows, sh on Unix
set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Display available commands
default:
    @just --list

# Sync dependencies and install pre-commit hooks
sync:
    uv sync
    uv run pre-commit install

# Format code (write changes)
format:
    moon run tools:format
    
# Check formatting without writing
format-check:
    moon run tools:format-check

# Run linter
lint:
    moon run tools:lint

# Run linter with auto-fix
lint-fix:
    moon run tools:lint-fix

# Run type checker
type-check:
    moon run tools:type-check

# Run all checks (format-check, lint, type-check)
check: format-check lint type-check
