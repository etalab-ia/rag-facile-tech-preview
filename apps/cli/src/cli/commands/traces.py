"""CLI commands for inspecting and exporting conversation traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from rag_facile.tracing import get_store


console = Console()


def show(
    n: Annotated[
        int, typer.Option("--n", "-n", help="Number of traces to display")
    ] = 20,
    db: Annotated[
        Optional[Path],
        typer.Option("--db", help="Path to traces.db (default: .rag-facile/traces.db)"),
    ] = None,
) -> None:
    """Show the most recent RAG conversation traces."""
    store = _get_store(db)
    rows = store.recent(n=n)

    if not rows:
        console.print("[yellow]No traces found.[/yellow] Run a conversation first.")
        raise typer.Exit()

    table = Table(
        title=f"Last {min(n, len(rows))} traces",
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    table.add_column("Created", style="dim", min_width=20, no_wrap=True)
    table.add_column("Question", ratio=3)
    table.add_column("Model", min_width=18, no_wrap=True)
    table.add_column("Latency", min_width=8, no_wrap=True)
    table.add_column("⭐", min_width=5, no_wrap=True)
    table.add_column("Sentiment", min_width=10, no_wrap=True)

    for row in rows:
        created = (row.get("created_at") or "")[:19].replace("T", " ")
        question = (row.get("question") or "")[:80]
        model = row.get("model_resolved") or row.get("model_alias") or "—"
        # Shorten model names for display
        model = model.split("/")[-1] if "/" in model else model
        latency = (
            f"{row['latency_ms']} ms" if row.get("latency_ms") is not None else "—"
        )
        star = "⭐" * int(row["star_rating"]) if row.get("star_rating") else "—"
        sentiment = row.get("sentiment") or "—"
        sentiment_styled = (
            f"[green]{sentiment}[/green]"
            if sentiment == "positive"
            else f"[red]{sentiment}[/red]"
            if sentiment == "negative"
            else "—"
        )
        table.add_row(created, question, model, latency, star, sentiment_styled)

    console.print(table)
    stats = store.stats()
    console.print(
        f"\n[dim]Total traces: {stats['total_traces']} | "
        f"Feedback: {stats['total_feedback']} | "
        f"Avg ⭐: {stats['avg_star'] or '—'}[/dim]"
    )


def export(
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output file (default: stdout)"),
    ] = None,
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Export format: jsonl | ragas"),
    ] = "jsonl",
    limit: Annotated[
        int, typer.Option("--limit", help="Maximum number of traces")
    ] = 1000,
    db: Annotated[
        Optional[Path],
        typer.Option("--db", help="Path to traces.db (default: .rag-facile/traces.db)"),
    ] = None,
) -> None:
    """Export traces as JSONL or in RAGAS-compatible format."""
    store = _get_store(db)

    if fmt == "ragas":
        rows = store.export_ragas(limit=limit)
    else:
        raw = store.recent(n=limit)
        rows = raw

    lines = [json.dumps(r, ensure_ascii=False, default=str) for r in rows]
    content = "\n".join(lines)

    if output:
        output.write_text(content + "\n", encoding="utf-8")
        console.print(
            f"[green]✓[/green] Exported {len(lines)} traces to [bold]{output}[/bold]"
        )
    else:
        console.print(content)


def stats(
    db: Annotated[
        Optional[Path],
        typer.Option("--db", help="Path to traces.db (default: .rag-facile/traces.db)"),
    ] = None,
) -> None:
    """Show quality statistics over all recorded traces."""
    store = _get_store(db)
    s = store.stats()

    console.print("\n[bold]📊 Trace Statistics[/bold]\n")
    console.print(f"  Total traces:   [cyan]{s['total_traces']}[/cyan]")
    console.print(f"  With feedback:  [cyan]{s['total_feedback']}[/cyan]")

    coverage = (
        f"{100 * s['total_feedback'] / s['total_traces']:.0f}%"
        if s["total_traces"] > 0
        else "—"
    )
    console.print(f"  Coverage:       [cyan]{coverage}[/cyan]")

    avg = s["avg_star"]
    console.print(f"  Avg ⭐ rating:  [cyan]{avg if avg is not None else '—'}[/cyan]")

    if s["top_tags"]:
        console.print("\n  [bold]Top quality tags:[/bold]")
        for tag, count in s["top_tags"]:
            bar = "█" * min(count, 20)
            console.print(f"    {tag:<35} {bar} {count}")
    console.print()


def prune(
    older_than: Annotated[
        int,
        typer.Option("--older-than", help="Delete traces older than N days"),
    ] = 365,
    db: Annotated[
        Optional[Path],
        typer.Option("--db", help="Path to traces.db (default: .rag-facile/traces.db)"),
    ] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete traces older than N days (RGPD data retention)."""
    if not yes:
        typer.confirm(
            f"Delete all traces older than {older_than} days?",
            abort=True,
        )
    store = _get_store(db)
    deleted = store.prune(older_than_days=older_than)
    if deleted:
        console.print(
            f"[green]✓[/green] Deleted {deleted} traces older than {older_than} days."
        )
    else:
        console.print(f"[dim]No traces older than {older_than} days found.[/dim]")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_store(db: Path | None):
    """Return a TraceStore, optionally at a custom db path."""
    if db is not None:
        from rag_facile.tracing._store import TraceStore

        return TraceStore(db)
    return get_store()
