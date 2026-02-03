"""Search for evaluation datasets."""

import os
from typing import Annotated, Optional

import httpx
import typer
from dotenv import load_dotenv
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

load_dotenv()

console = Console()
app = typer.Typer(help="Search for evaluation datasets")


class HFDataset(BaseModel):
    """HuggingFace dataset metadata."""

    id: str
    author: Optional[str] = None
    downloads: int = 0
    likes: int = 0
    tags: list[str] = []
    description: Optional[str] = None

    @property
    def url(self) -> str:
        return f"https://huggingface.co/datasets/{self.id}"


def search_huggingface(
    query: str,
    *,
    author: str | None = None,
    limit: int = 20,
) -> list[HFDataset]:
    """Search HuggingFace for datasets matching the query.

    Args:
        query: Search query string
        author: Filter by author/organization (e.g., "AgentPublic")
        limit: Maximum number of results to return

    Returns:
        List of matching datasets
    """
    hf_token = os.getenv("HF_TOKEN")

    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"

    params: dict[str, str | int] = {
        "search": query,
        "limit": limit,
        "full": "true",  # Get full metadata
    }

    if author:
        params["author"] = author

    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            "https://huggingface.co/api/datasets",
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    datasets = []
    for item in data:
        datasets.append(
            HFDataset(
                id=item.get("id", ""),
                author=item.get("author"),
                downloads=item.get("downloads", 0),
                likes=item.get("likes", 0),
                tags=item.get("tags", []),
                description=item.get("description"),
            )
        )

    return datasets


def display_datasets(datasets: list[HFDataset], title: str = "Search Results"):
    """Display datasets in a rich table."""
    if not datasets:
        console.print("[yellow]No datasets found.[/yellow]")
        return

    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Dataset ID", style="green", no_wrap=True)
    table.add_column("Downloads", justify="right", style="yellow")
    table.add_column("Likes", justify="right", style="magenta")
    table.add_column("Tags", style="dim")

    for ds in datasets:
        # Truncate tags for display
        tags_str = ", ".join(ds.tags[:5])
        if len(ds.tags) > 5:
            tags_str += f" (+{len(ds.tags) - 5})"

        table.add_row(
            ds.id,
            str(ds.downloads),
            str(ds.likes),
            tags_str,
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(datasets)} dataset(s)[/dim]")


@app.command(name="hf")
def search_hf(
    query: Annotated[str, typer.Argument(help="Search query for datasets")],
    author: Annotated[
        Optional[str],
        typer.Option("--author", "-a", help="Filter by author/organization"),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of results"),
    ] = 20,
):
    """Search HuggingFace for evaluation datasets.

    Examples:
        rag-eval search hf "french QA"
        rag-eval search hf "RAG evaluation" --author AgentPublic
        rag-eval search hf "legislation" -a AgentPublic -n 10
    """
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        console.print(
            "[yellow]Warning: HF_TOKEN not set. Some datasets may not be accessible.[/yellow]"
        )
        console.print("[dim]Set HF_TOKEN in your .env file for full access.[/dim]\n")

    with console.status(f"[cyan]Searching HuggingFace for '{query}'..."):
        try:
            datasets = search_huggingface(query, author=author, limit=limit)
        except httpx.HTTPError as e:
            console.print(f"[red]Error searching HuggingFace: {e}[/red]")
            raise typer.Exit(1)

    title = f"HuggingFace Datasets: '{query}'"
    if author:
        title += f" (author: {author})"

    display_datasets(datasets, title=title)


@app.command(name="agent-public")
def search_agent_public(
    query: Annotated[
        Optional[str],
        typer.Argument(help="Optional search query within AgentPublic datasets"),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of results"),
    ] = 50,
):
    """Search datasets from the AgentPublic organization (MediaTech collection).

    This is a convenience command that filters HuggingFace search to the
    AgentPublic organization, which hosts French government datasets.

    Examples:
        rag-eval search agent-public
        rag-eval search agent-public "legislation"
    """
    search_query = query or ""

    with console.status("[cyan]Searching AgentPublic datasets..."):
        try:
            datasets = search_huggingface(
                search_query,
                author="AgentPublic",
                limit=limit,
            )
        except httpx.HTTPError as e:
            console.print(f"[red]Error searching HuggingFace: {e}[/red]")
            raise typer.Exit(1)

    display_datasets(datasets, title="AgentPublic Datasets (MediaTech Collection)")


@app.command(name="comparia")
def search_comparia(
    query: Annotated[
        Optional[str],
        typer.Argument(help="Optional search query within Compar:IA datasets"),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of results"),
    ] = 50,
):
    """Search datasets from Compar:IA (French Ministry of Culture chatbot arena).

    Compar:IA is a conversational AI comparison tool that collects user preferences
    and conversations across 30+ models. Useful for preference tuning and evaluation.

    Key datasets:
    - comparia-conversations: 289k+ questions & answers from real users
    - comparia-votes: 97k+ user preferences comparing two models
    - comparia-reactions: 59k+ message-level reactions

    Examples:
        rag-eval search comparia
        rag-eval search comparia "votes"
    """
    search_query = query or ""

    with console.status("[cyan]Searching Compar:IA datasets..."):
        try:
            datasets = search_huggingface(
                search_query,
                author="ministere-culture",
                limit=limit,
            )
        except httpx.HTTPError as e:
            console.print(f"[red]Error searching HuggingFace: {e}[/red]")
            raise typer.Exit(1)

    display_datasets(datasets, title="Compar:IA Datasets (ministere-culture)")
