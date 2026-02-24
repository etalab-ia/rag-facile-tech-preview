"""CLI commands for RAG evaluation using Inspect AI.

Provides ``rag-facile eval`` subcommands:
- ``run`` — execute an evaluation on a dataset
- ``view`` — open the Inspect AI log viewer
- ``list`` — list past evaluation runs
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from rag_facile.core.loader import load_config_or_default


console = Console()


def _resolve_log_dir() -> Path:
    """Resolve the Inspect log directory from config."""
    try:
        config = load_config_or_default()
        return Path(config.eval.inspect_log_dir)
    except (FileNotFoundError, AttributeError):
        return Path("data/evals/logs")


def run(
    dataset: Optional[str] = typer.Argument(
        None,
        help="Path to JSONL dataset. Defaults to latest in data/datasets/.",
    ),
    model: str = typer.Option(
        "openai/openweight-medium",
        "--model",
        "-m",
        help="Model for generation and faithfulness scoring.",
    ),
    log_dir: Optional[str] = typer.Option(
        None,
        "--log-dir",
        help="Override Inspect log directory.",
    ),
) -> None:
    """Run a RAG evaluation on a dataset."""
    # Resolve dataset path
    if dataset is None:
        data_dir = Path("data/datasets")
        if not data_dir.exists():
            console.print(
                "[red]No data/datasets/ directory found. "
                "Run `rag-facile generate-dataset` first.[/red]"
            )
            raise typer.Exit(code=1)
        jsonl_files = sorted(data_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        if not jsonl_files:
            console.print(
                "[red]No .jsonl files in data/datasets/. "
                "Run `rag-facile generate-dataset` first.[/red]"
            )
            raise typer.Exit(code=1)
        dataset = str(jsonl_files[-1])
        console.print(f"[cyan]Using latest dataset:[/cyan] {dataset}")

    dataset_path = Path(dataset).resolve()
    if not dataset_path.exists():
        console.print(f"[red]Dataset not found:[/red] {dataset}")
        raise typer.Exit(code=1)

    # Resolve log directory
    effective_log_dir = (
        Path(log_dir).resolve() if log_dir else _resolve_log_dir().resolve()
    )
    effective_log_dir.mkdir(parents=True, exist_ok=True)

    console.print("[cyan]Running evaluation...[/cyan]")
    console.print(f"  Dataset: {dataset_path}")
    console.print(f"  Model: {model}")
    console.print(f"  Logs: {effective_log_dir}\n")

    # Verify the evaluation package is installed
    try:
        from rag_facile.evaluation._tasks import rag_eval  # ty: ignore[unresolved-import]
    except ImportError:
        console.print(
            "[red]evaluation package not installed. "
            "Run `uv sync` in the workspace root.[/red]"
        )
        raise typer.Exit(code=1)

    # Run evaluation via the Inspect AI Python API (not subprocess CLI).
    # The CLI path-based task discovery fails on Python 3.13 because
    # pathlib.glob() rejects absolute paths. The Python API takes the
    # @task function object directly — no path resolution needed.
    try:
        from inspect_ai import eval as inspect_eval

        results = inspect_eval(
            rag_eval(
                dataset_path=str(dataset_path),
                grader_model=model,
            ),
            model=model,
            log_dir=str(effective_log_dir),
        )

        failed = [r for r in results if r.status == "error"]
        if failed:
            console.print(f"\n[red]Evaluation failed: {failed[0].error}[/red]")
            raise typer.Exit(code=1)

    except ImportError:
        console.print(
            "[red]inspect-ai not found. Install with: uv add inspect-ai[/red]"
        )
        raise typer.Exit(code=1)

    console.print("\n[green]Evaluation complete![/green]")
    console.print("View results: [cyan]rag-facile eval view[/cyan]")


def view(
    log_dir: Optional[str] = typer.Option(
        None,
        "--log-dir",
        help="Override Inspect log directory.",
    ),
) -> None:
    """Open the Inspect AI log viewer in the browser."""
    effective_log_dir = Path(log_dir) if log_dir else _resolve_log_dir()

    if not effective_log_dir.exists():
        console.print(f"[red]Log directory not found:[/red] {effective_log_dir}")
        console.print("Run an evaluation first: [cyan]rag-facile eval run[/cyan]")
        raise typer.Exit(code=1)

    cmd = [
        sys.executable,
        "-m",
        "inspect_ai._cli.main",
        "view",
        "--log-dir",
        str(effective_log_dir),
    ]

    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        console.print(
            "[red]inspect-ai not found. Install with: uv add inspect-ai[/red]"
        )
        raise typer.Exit(code=1)


def list_runs(
    log_dir: Optional[str] = typer.Option(
        None,
        "--log-dir",
        help="Override Inspect log directory.",
    ),
) -> None:
    """List past evaluation runs."""
    effective_log_dir = Path(log_dir) if log_dir else _resolve_log_dir()

    if not effective_log_dir.exists():
        console.print(
            f"[yellow]No evaluations yet.[/yellow] Log dir: {effective_log_dir}"
        )
        return

    log_files = sorted(
        [*effective_log_dir.glob("*.eval"), *effective_log_dir.glob("*.json")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not log_files:
        console.print("[yellow]No evaluation logs found.[/yellow]")
        return

    table = Table(title="Evaluation Runs", expand=True)
    table.add_column("File", no_wrap=True)
    table.add_column("Size", justify="right")
    table.add_column("Modified", no_wrap=True)

    for f in log_files[:20]:  # Show latest 20
        stat = f.stat()
        size_kb = stat.st_size / 1024
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        table.add_row(
            f.name,
            f"{size_kb:.1f} KB",
            mtime.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)
    console.print(f"\nTotal: {len(log_files)} log(s) in {effective_log_dir}")
