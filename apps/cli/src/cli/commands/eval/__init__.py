"""Evaluation commands for RAG Facile CLI."""

import typer

from cli.commands.eval import generate

app = typer.Typer(
    help="Generate and manage evaluation datasets",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=True,
)

app.command(name="generate")(generate.run)
