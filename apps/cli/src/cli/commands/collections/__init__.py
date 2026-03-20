"""Albert API collection management commands.

Commands for creating, deleting, and managing RAG collections on the Albert API.
Collections are the primary storage mechanism for documents in the RAG pipeline.
"""

from pathlib import Path
from typing import Annotated, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
import typer
from rich import print as rprint
from rich.table import Table

from ragtime.core import load_config_or_default, save_config


def _get_client() -> Any:
    """Get Albert client, handling import and auth errors."""
    try:
        from albert import AlbertClient
    except ImportError:
        rprint("[red]✗ albert-client package is required.[/red]")
        rprint("[dim]Install with: uv pip install albert-client[/dim]")
        raise typer.Exit(1)

    try:
        return AlbertClient()
    except ValueError as e:
        rprint(f"[red]✗ {e}[/red]")
        rprint("[dim]Set ALBERT_API_KEY or OPENAI_API_KEY environment variable.[/dim]")
        raise typer.Exit(1)


def _get_supported_extensions() -> list[str]:
    """Get supported file extensions for upload."""
    return [".pdf", ".md", ".html", ".markdown"]


def _find_collection_by_id(client: Any, collection_id: int) -> "Any | None":
    """Find a collection by ID, handling pagination for users with many collections.

    Args:
        client: The Albert client instance.
        collection_id: The ID of the collection to find.

    Returns:
        The collection if found, None otherwise.
    """
    # Try with a high limit first (most users won't have more than 1000 collections)
    try:
        result = client.list_collections(limit=1000)
        collection = next((c for c in result.data if c.id == collection_id), None)
        if collection:
            return collection
    except httpx.HTTPStatusError:
        pass

    # If not found and there might be more, we could implement pagination here
    # For now, return None - the API doesn't expose a direct get-by-id endpoint
    return None


def _expand_paths(paths: list[Path], pattern: str | None = None) -> list[Path]:
    """Expand paths to individual files, filtering by supported extensions.

    Args:
        paths: List of file or directory paths.
        pattern: Optional glob pattern for directory expansion.

    Returns:
        List of file paths to upload.
    """
    files: set[Path] = set()
    supported = _get_supported_extensions()
    glob_pattern = pattern or "*"

    for path in paths:
        path = path.resolve()
        if path.is_file():
            if path.suffix.lower() in supported:
                files.add(path)
            else:
                rprint(f"[yellow]⚠ Skipping unsupported file: {path}[/yellow]")
        elif path.is_dir():
            # Use rglob for recursive search with a single pattern
            for ext in supported:
                files.update(path.rglob(f"{glob_pattern}{ext}"))

    return sorted(files)


def _add_collection_to_config(
    collection_id: int, config_path: str = "ragtime.toml"
) -> None:
    """Add a collection ID to the config file.

    Args:
        collection_id: The collection ID to add.
        config_path: Path to the config file.
    """
    config = load_config_or_default(config_path)
    current_ids = set(config.storage.collections)
    current_ids.add(collection_id)
    config.storage.collections = sorted(current_ids)
    save_config(config, config_path)


def _remove_collection_from_config(
    collection_id: int, config_path: str = "ragtime.toml"
) -> None:
    """Remove a collection ID from the config file.

    Args:
        collection_id: The collection ID to remove.
        config_path: Path to the config file.
    """
    config = load_config_or_default(config_path)
    current_ids = set(config.storage.collections)
    current_ids.discard(collection_id)
    config.storage.collections = sorted(current_ids)
    save_config(config, config_path)


def list_collections(
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of collections to show"),
    ] = 50,
) -> None:
    """List accessible collections on the Albert API.

    Shows all collections you have access to, including public collections
    shared across the platform. Public collections (marked in green) can be
    added to your RAG pipeline configuration.

    Requires ALBERT_API_KEY or OPENAI_API_KEY environment variable.

    Examples:
        # List all accessible collections
        ragtime collections list

        # Limit results
        ragtime collections list --limit 20
    """
    client = _get_client()

    # Fetch collections
    try:
        result = client.list_collections(limit=limit)
    except httpx.HTTPStatusError as e:
        rprint(f"[red]✗ Failed to fetch collections: {e}[/red]")
        raise typer.Exit(1)

    collections = result.data
    if not collections:
        rprint("[yellow]No collections found.[/yellow]")
        raise typer.Exit(0)

    # Build table
    table = Table(title="📚 Collections", expand=True)
    table.add_column("ID", style="cyan", no_wrap=True, min_width=6)
    table.add_column("Name", style="bold", min_width=20)
    table.add_column("Description", ratio=1)
    table.add_column("Docs", justify="right", no_wrap=True, min_width=6)
    table.add_column("Visibility", no_wrap=True, min_width=10)

    for col in collections:
        visibility_style = "green" if col.visibility == "public" else "dim"
        table.add_row(
            str(col.id),
            col.name or "—",
            col.description or "—",
            f"{col.documents:,}" if col.documents else "0",
            f"[{visibility_style}]{col.visibility or '—'}[/{visibility_style}]",
        )

    rprint()
    rprint(table)
    rprint()

    # Educational hint: show public collection IDs for easy copy-paste
    public_cols = [c for c in collections if c.visibility == "public"]
    if public_cols:
        public_ids = [str(c.id) for c in public_cols]
        rprint(
            "[dim]💡 Add public collections to your RAG pipeline in ragtime.toml:[/dim]"
        )
        rprint(
            f'[dim]   ragtime config set storage.collections "[{", ".join(public_ids)}]"[/dim]'
        )
    else:
        rprint("[dim]💡 Add collection IDs to your RAG pipeline in ragtime.toml:[/dim]")
        example_ids = [str(c.id) for c in collections[:2]]
        rprint(
            f'[dim]   ragtime config set storage.collections "[{", ".join(example_ids)}]"[/dim]'
        )


def create_collection(
    name: Annotated[str, typer.Argument(help="Collection name")],
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="Collection description"),
    ] = None,
    visibility: Annotated[
        str,
        typer.Option(
            "--visibility", "-v", help="Collection visibility (private or public)"
        ),
    ] = "private",
    enable: Annotated[
        bool,
        typer.Option("--enable/--no-enable", help="Add to config after creation"),
    ] = True,
    config_path: Annotated[
        str,
        typer.Option("--config", "-c", help="Path to config file"),
    ] = "ragtime.toml",
) -> None:
    """Create a new RAG collection on the Albert API.

    By default, the collection is automatically added to your RAG pipeline
    configuration. Use --no-enable to skip this step.

    Examples:
        # Create a private collection
        ragtime collections create "My Documents"

        # Create with description
        ragtime collections create "Legal Docs" --description "Legal documentation"

        # Create a public collection
        ragtime collections create "Shared Docs" --visibility public

        # Create without adding to config
        ragtime collections create "Temp" --no-enable
    """
    client = _get_client()

    try:
        collection = client.create_collection(
            name=name,
            description=description,
            visibility=visibility,
        )
    except httpx.HTTPStatusError as e:
        rprint(f"[red]✗ Failed to create collection: {e}[/red]")
        raise typer.Exit(1)

    rprint(f"[green]✓ Created collection: {collection.name}[/green]")
    rprint(f"  [dim]ID:[/dim] {collection.id}")
    rprint(f"  [dim]Visibility:[/dim] {collection.visibility}")

    if enable and collection.id:
        try:
            _add_collection_to_config(collection.id, config_path)
            rprint(f"  [dim]Added to config:[/dim] {config_path}")
        except Exception as e:
            rprint(
                f"[yellow]⚠ Collection created but not added to config: {e}[/yellow]"
            )
            rprint(
                f"[dim]Add manually: ragtime collections enable {collection.id}[/dim]"
            )


def delete_collection(
    collection_id: Annotated[int, typer.Argument(help="Collection ID to delete")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation prompt"),
    ] = False,
    disable: Annotated[
        bool,
        typer.Option(
            "--disable/--no-disable", help="Remove from config after deletion"
        ),
    ] = True,
    config_path: Annotated[
        str,
        typer.Option("--config", "-c", help="Path to config file"),
    ] = "ragtime.toml",
) -> None:
    """Delete a collection from the Albert API.

    This action is irreversible. The collection and all its documents
    will be permanently deleted.

    Examples:
        # Delete with confirmation
        ragtime collections delete 123

        # Force delete without confirmation
        ragtime collections delete 123 --force

        # Delete but keep in config
        ragtime collections delete 123 --no-disable
    """
    client = _get_client()

    # Get collection info first for confirmation
    try:
        collection = _find_collection_by_id(client, collection_id)
    except httpx.HTTPStatusError:
        collection = None

    if not collection:
        rprint(
            f"[yellow]⚠ Collection {collection_id} not found or not accessible[/yellow]"
        )
        if not force:
            raise typer.Exit(1)

    # Confirm deletion
    if not force:
        name = collection.name if collection else f"ID {collection_id}"
        docs = collection.documents if collection else "unknown"
        rprint(f"[red]⚠ This will permanently delete collection: {name}[/red]")
        rprint(f"[red]  Documents: {docs}[/red]")
        rprint("[red]  This action cannot be undone.[/red]")
        confirm = typer.confirm("Are you sure?")
        if not confirm:
            rprint("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    # Delete
    try:
        client.delete_collection(collection_id)
        rprint(f"[green]✓ Deleted collection {collection_id}[/green]")
    except httpx.HTTPStatusError as e:
        rprint(f"[red]✗ Failed to delete collection: {e}[/red]")
        raise typer.Exit(1)

    # Remove from config
    if disable:
        try:
            _remove_collection_from_config(collection_id, config_path)
            rprint(f"  [dim]Removed from config: {config_path}[/dim]")
        except Exception as e:
            rprint(
                f"[yellow]⚠ Collection deleted but not removed from config: {e}[/yellow]"
            )


def show_collection(
    collection_id: Annotated[int, typer.Argument(help="Collection ID to show")],
    docs: Annotated[
        bool,
        typer.Option("--docs", help="Show documents in the collection"),
    ] = False,
    doc_limit: Annotated[
        int,
        typer.Option("--doc-limit", "-n", help="Maximum documents to show"),
    ] = 20,
) -> None:
    """Show collection details and optionally list its documents.

    Examples:
        # Show collection info
        ragtime collections show 123

        # Show collection with documents
        ragtime collections show 123 --docs

        # Show with more documents
        ragtime collections show 123 --docs --doc-limit 50
    """
    client = _get_client()

    # Get collection info using helper with pagination support
    try:
        collection = _find_collection_by_id(client, collection_id)
    except httpx.HTTPStatusError as e:
        rprint(f"[red]✗ Failed to fetch collection: {e}[/red]")
        raise typer.Exit(1)

    if not collection:
        rprint(f"[red]✗ Collection {collection_id} not found or not accessible[/red]")
        raise typer.Exit(1)

    # Display collection info
    rprint()
    rprint(f"[bold cyan]📚 {collection.name}[/bold cyan]")
    rprint(f"  [dim]ID:[/dim] {collection.id}")
    rprint(f"  [dim]Visibility:[/dim] {collection.visibility}")
    rprint(f"  [dim]Documents:[/dim] {collection.documents or 0}")
    if collection.description:
        rprint(f"  [dim]Description:[/dim] {collection.description}")
    rprint()

    # Show documents if requested
    if docs:
        try:
            result = client.list_documents(collection_id=collection_id, limit=doc_limit)
        except httpx.HTTPStatusError as e:
            rprint(f"[red]✗ Failed to fetch documents: {e}[/red]")
            raise typer.Exit(1)

        if not result.data:
            rprint("[dim]No documents in this collection.[/dim]")
            raise typer.Exit(0)

        table = Table(title="📄 Documents", expand=True)
        table.add_column("ID", style="cyan", no_wrap=True, min_width=6)
        table.add_column("Name", style="bold", min_width=20)
        table.add_column("Status", no_wrap=True, min_width=10)

        for doc in result.data:
            table.add_row(
                str(doc.id),
                doc.name or "—",
                doc.status or "—",
            )

        rprint(table)
        if result.total > doc_limit:
            rprint(f"[dim]Showing {doc_limit} of {result.total} documents[/dim]")


def upload_documents(
    collection_id: Annotated[int, typer.Argument(help="Collection ID to upload to")],
    paths: Annotated[
        list[Path],
        typer.Argument(help="Files or directories to upload", exists=True),
    ],
    pattern: Annotated[
        str | None,
        typer.Option("--pattern", "-p", help="Glob pattern for directory expansion"),
    ] = None,
    chunk_size: Annotated[
        int,
        typer.Option("--chunk-size", help="Chunk size in tokens"),
    ] = 2048,
    chunk_overlap: Annotated[
        int,
        typer.Option("--chunk-overlap", help="Chunk overlap in tokens"),
    ] = 0,
    jobs: Annotated[
        int,
        typer.Option("--jobs", "-j", help="Parallel upload jobs"),
    ] = 4,
) -> None:
    """Upload documents to a collection.

    Supports single files, multiple files, and directories. For directories,
    use --pattern to filter files.

    Examples:
        # Upload a single file
        ragtime collections upload 123 document.pdf

        # Upload multiple files
        ragtime collections upload 123 doc1.pdf doc2.md

        # Upload a directory
        ragtime collections upload 123 ./docs/

        # Upload with pattern
        ragtime collections upload 123 ./docs/ --pattern "*.pdf"

        # Upload with custom chunking
        ragtime collections upload 123 ./docs/ --chunk-size 1024 --chunk-overlap 100

        # Parallel uploads
        ragtime collections upload 123 ./docs/ --jobs 8
    """
    client = _get_client()

    # Expand paths to files
    files = _expand_paths(paths, pattern)

    if not files:
        rprint("[yellow]⚠ No supported files found to upload.[/yellow]")
        rprint(
            f"[dim]Supported formats: {', '.join(_get_supported_extensions())}[/dim]"
        )
        raise typer.Exit(0)

    rprint(
        f"[bold]Uploading {len(files)} file(s) to collection {collection_id}...[/bold]"
    )
    rprint(
        f"[dim]Chunk size: {chunk_size}, Overlap: {chunk_overlap}, Jobs: {jobs}[/dim]"
    )
    rprint()

    success: list[Path] = []
    failed: list[tuple[Path, str]] = []

    def upload_one(file_path: Path) -> tuple[Path, bool, str]:
        """Upload a single file. Returns (path, success, error_message)."""
        try:
            client.upload_document(
                file_path=file_path,
                collection_id=collection_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            return (file_path, True, "")
        except httpx.HTTPStatusError as e:
            return (file_path, False, str(e))
        except OSError as e:
            return (file_path, False, str(e))

    # Upload in parallel with progress
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {executor.submit(upload_one, f): f for f in files}
        for future in as_completed(futures):
            file_path, ok, err = future.result()
            if ok:
                success.append(file_path)
                rprint(f"  [green]✓[/green] {file_path.name}")
            else:
                failed.append((file_path, err))
                rprint(f"  [red]✗[/red] {file_path.name}: {err}")

    # Summary
    rprint()
    rprint(f"[green]✓ Uploaded: {len(success)} files[/green]")
    if failed:
        rprint(f"[red]✗ Failed: {len(failed)} files[/red]")
        for path, err in failed:
            rprint(f"  [dim]{path}: {err}[/dim]")


def enable_collection(
    collection_id: Annotated[int, typer.Argument(help="Collection ID to enable")],
    config_path: Annotated[
        str,
        typer.Option("--config", "-c", help="Path to config file"),
    ] = "ragtime.toml",
) -> None:
    """Add a collection to the RAG pipeline configuration.

    The collection will be searched during RAG queries.

    Examples:
        ragtime collections enable 123
        ragtime collections enable 123 --config my-rag.toml
    """
    config = load_config_or_default(config_path)
    if collection_id in config.storage.collections:
        rprint(f"[yellow]Collection {collection_id} is already enabled.[/yellow]")
        return

    try:
        _add_collection_to_config(collection_id, config_path)
        rprint(f"[green]✓ Enabled collection {collection_id}[/green]")
        rprint(f"  [dim]Added to: {config_path}[/dim]")
    except Exception as e:
        rprint(f"[red]✗ Failed to enable collection: {e}[/red]")
        raise typer.Exit(1)


def disable_collection(
    collection_id: Annotated[int, typer.Argument(help="Collection ID to disable")],
    config_path: Annotated[
        str,
        typer.Option("--config", "-c", help="Path to config file"),
    ] = "ragtime.toml",
) -> None:
    """Remove a collection from the RAG pipeline configuration.

    The collection will no longer be searched during RAG queries.
    The collection itself is not deleted from Albert.

    Examples:
        ragtime collections disable 123
        ragtime collections disable 123 --config my-rag.toml
    """
    config = load_config_or_default(config_path)
    if collection_id not in config.storage.collections:
        rprint(f"[yellow]Collection {collection_id} is not in config.[/yellow]")
        return

    try:
        _remove_collection_from_config(collection_id, config_path)
        rprint(f"[green]✓ Disabled collection {collection_id}[/green]")
        rprint(f"  [dim]Removed from: {config_path}[/dim]")
    except Exception as e:
        rprint(f"[red]✗ Failed to disable collection: {e}[/red]")
        raise typer.Exit(1)


__all__ = [
    "list_collections",
    "create_collection",
    "delete_collection",
    "show_collection",
    "upload_documents",
    "enable_collection",
    "disable_collection",
]
