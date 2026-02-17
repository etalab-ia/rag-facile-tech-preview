"""Upgrade RAG Facile CLI to the latest version."""

import subprocess

import typer
from importlib.metadata import version as get_version
from rich.console import Console


console = Console()

# The git URL used by both install.sh and install.ps1
INSTALL_URL = (
    "git+https://github.com/etalab-ia/rag-facile.git@{branch}#subdirectory=apps/cli"
)


def run(
    branch: str = typer.Option(
        "main", "--branch", "-b", help="Git branch to install from"
    ),
) -> None:
    """Upgrade to the latest version of the RAG Facile CLI."""
    # Get current version
    try:
        old_version = get_version("rag-facile-cli")
    except Exception:
        old_version = "unknown"

    console.print("\n[bold]Upgrading RAG Facile CLI...[/bold]")
    console.print(f"  Current version: [cyan]v{old_version}[/cyan]")
    console.print(f"  Branch: [dim]{branch}[/dim]\n")

    url = INSTALL_URL.format(branch=branch)
    try:
        result = subprocess.run(
            ["uv", "tool", "install", "rag-facile-cli", "--force", "--from", url],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        console.print("[red]Error: uv is not installed. Re-run the installer:[/red]")
        console.print(
            "[dim]curl -fsSL https://raw.githubusercontent.com/etalab-ia/rag-facile/main/install.sh | bash[/dim]"
        )
        raise typer.Exit(code=1)
    except subprocess.TimeoutExpired:
        console.print(
            "[red]Error: upgrade timed out. Check your network connection.[/red]"
        )
        raise typer.Exit(code=1)

    if result.returncode != 0:
        console.print("[red]Error: upgrade failed.[/red]")
        if result.stderr:
            console.print(f"[dim]{result.stderr.strip()}[/dim]")
        raise typer.Exit(code=1)

    # Get new version — need to re-read from the freshly installed package
    try:
        check = subprocess.run(
            ["rag-facile", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Output format: "rag-facile v0.13.0" (with ANSI codes from Rich)
        new_version = check.stdout.strip()
    except Exception:
        new_version = "unknown"

    console.print("[bold green]Upgraded successfully![/bold green]")
    if new_version and new_version != "unknown":
        console.print(f"  {new_version}\n")
    else:
        console.print()
