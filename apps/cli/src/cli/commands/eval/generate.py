"""Generate synthetic Q/A evaluation datasets using Letta Cloud.

This module implements the Data Foundry feature - an agentic RAG evaluation
dataset generator that creates Question/Answer/Context triplets from French
government documents.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def run(
    input_dir: Annotated[
        Path,
        typer.Argument(
            help="Directory containing PDF/Markdown files to process",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output JSONL file path",
        ),
    ] = Path("golden_dataset.jsonl"),
    samples: Annotated[
        int,
        typer.Option(
            "--samples",
            "-n",
            help="Target number of Q/A pairs to generate",
        ),
    ] = 50,
    agent_id: Annotated[
        str,
        typer.Option(
            "--agent-id",
            envvar="DATA_FOUNDRY_AGENT_ID",
            help="Data Foundry agent ID on Letta Cloud",
        ),
    ] = "",
) -> None:
    """Generate synthetic Q/A evaluation dataset from documents.

    Uses the Data Foundry agent on Letta Cloud to generate high-quality
    Question/Answer/Context triplets in French from your documents.

    Example:
        rag-facile eval generate ./docs -o golden_dataset.jsonl -n 50
    """
    # Validate environment
    api_key = os.getenv("LETTA_API_KEY")
    if not api_key:
        console.print(
            "[red]Error: LETTA_API_KEY environment variable is required.[/red]"
        )
        console.print("[dim]Get your API key at https://app.letta.com/api-keys[/dim]")
        raise typer.Exit(1)

    if not agent_id:
        console.print(
            "[red]Error: DATA_FOUNDRY_AGENT_ID environment variable or --agent-id is required.[/red]"
        )
        raise typer.Exit(1)

    # Import letta_client here to provide helpful error if not installed
    try:
        from letta_client import Letta
    except ImportError:
        console.print("[red]Error: letta-client package is not installed.[/red]")
        console.print("[dim]Run: uv add letta-client[/dim]")
        raise typer.Exit(1)

    # Find documents
    doc_extensions = {".pdf", ".md", ".txt"}
    documents = [
        f
        for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in doc_extensions
    ]

    if not documents:
        console.print(f"[yellow]No documents found in {input_dir}[/yellow]")
        console.print(f"[dim]Supported formats: {', '.join(doc_extensions)}[/dim]")
        raise typer.Exit(1)

    console.print("\n[cyan]Data Foundry[/cyan] - Synthetic RAG Evaluation Generator\n")
    console.print(f"  Documents: {len(documents)} files in {input_dir}")
    console.print(f"  Target: {samples} Q/A pairs")
    console.print(f"  Output: {output}\n")

    # Initialize Letta client
    client = Letta(api_key=api_key)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Create folder and upload documents
        task = progress.add_task("Creating folder for documents...", total=None)
        folder_name = (
            f"data_foundry_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        folder = client.folders.create(name=folder_name)

        progress.update(task, description="Uploading documents...")
        for doc in documents:
            with open(doc, "rb") as f:
                client.folders.files.upload(file=f, folder_id=folder.id)

        # Attach folder to agent
        progress.update(task, description="Attaching folder to agent...")
        client.agents.folders.attach(agent_id=agent_id, folder_id=folder.id)

        # Step 2: Create new conversation for this run
        progress.update(task, description="Creating conversation...")
        conversation = client.conversations.create(agent_id=agent_id)

        # Step 3: Send generation request
        progress.update(task, description="Generating Q/A pairs...")

        prompt = f"""Generate {samples} Question/Answer pairs from the uploaded documents.

Requirements:
- Questions and answers must be in French
- Each answer must be fully grounded in the document context
- Ensure diversity - avoid similar questions about the same topics
- Self-critique each pair for quality before outputting

Return each sample as a JSON object on its own line with this exact structure:
{{
  "user_input": "Question in French?",
  "retrieved_contexts": ["The exact text passage that answers the question..."],
  "reference": "The answer in French, fully grounded in the context.",
  "_metadata": {{
    "source_file": "filename.pdf",
    "quality_score": 0.95,
    "topic_summary": "Brief topic for diversity tracking"
  }}
}}

Start generating now. Output each JSON sample on its own line as you generate them."""

        progress.remove_task(task)

    # Stream the response and collect samples
    console.print("[cyan]Generating samples...[/cyan]\n")

    generated_samples = []
    stream = client.conversations.messages.create(
        conversation_id=conversation.id,
        messages=[{"role": "user", "content": prompt}],
    )

    current_response = ""
    for msg in stream:
        if hasattr(msg, "message_type") and msg.message_type == "assistant_message":
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            current_response += content

            # Try to extract JSON samples from the response
            samples_found = _extract_json_samples(current_response)
            for sample in samples_found:
                if sample not in generated_samples:
                    generated_samples.append(sample)
                    console.print(
                        f"  [green]Sample {len(generated_samples)}:[/green] {sample.get('user_input', '')[:60]}..."
                    )

    # Write output file
    if generated_samples:
        with open(output, "w", encoding="utf-8") as f:
            for sample in generated_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")

        console.print(
            f"\n[green]Success![/green] Generated {len(generated_samples)} samples"
        )
        console.print(f"[dim]Output saved to: {output}[/dim]")
    else:
        console.print("\n[yellow]Warning: No samples were generated.[/yellow]")
        console.print(
            "[dim]The agent response may not have contained valid JSON samples.[/dim]"
        )
        console.print(f"\n[dim]Raw response:[/dim]\n{current_response[:500]}...")

    # Cleanup: detach folder (optional, keeps Cloud tidy)
    try:
        client.agents.folders.detach(agent_id=agent_id, folder_id=folder.id)
    except Exception:
        pass  # Non-critical


def _extract_json_samples(text: str) -> list[dict]:
    """Extract JSON objects from text, handling partial/streaming responses."""
    samples = []

    # Try to find JSON objects line by line
    for line in text.split("\n"):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue

        try:
            # Try to parse as JSON
            sample = json.loads(line)
            # Validate it has expected fields
            if "user_input" in sample and "reference" in sample:
                samples.append(sample)
        except json.JSONDecodeError:
            # Might be incomplete, skip
            continue

    return samples
