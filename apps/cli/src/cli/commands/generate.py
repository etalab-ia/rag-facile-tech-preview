"""Generate command - orchestrates workspace generation using Init + Patch architecture."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import questionary
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

# Available frontends
FRONTENDS = {
    "Chainlit": "chainlit-chat",
    "Reflex": "reflex-chat",
}

# Available modules (packages)
MODULES = {
    "PDF": {"template": "pdf-context", "available": True},
    "Chroma": {"template": "chroma-context", "available": False},
}


def get_templates_dir() -> Path:
    """Get the templates directory from the rag-facile repository."""
    # When running from installed CLI, we need to find the templates
    # For now, assume we're running from within the rag-facile repo
    repo_root = Path(__file__).resolve().parents[5]
    return repo_root / ".moon" / "templates"


def run_command(cmd: list[str], description: str, cwd: Path | None = None) -> bool:
    """Run a shell command and handle errors."""
    console.print(f"[dim]{' '.join(cmd)}[/dim]")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        console.print(f"[red]Error: {description} failed[/red]")
        if result.stderr:
            console.print(f"[red]{result.stderr}[/red]")
        return False
    return True


@app.command()
def workspace(
    target: Annotated[
        str,
        typer.Argument(help="Target directory for the new workspace"),
    ] = "",
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing files"),
    ] = False,
):
    """Generate a new RAG Facile workspace with interactive configuration.

    Uses the Init + Patch architecture:
    1. Bootstrap with `moon init`
    2. Apply RAG Facile configuration
    3. Generate selected app and packages
    """
    # 1. Gather inputs interactively
    if not target:
        target = questionary.text(
            "Target directory:",
            default="./my-rag-app",
        ).ask()
        if not target:
            console.print("[red]Aborted.[/red]")
            raise typer.Exit(1)

    target_path = Path(target).resolve()
    # On macOS, /tmp resolves to /private/tmp - normalize for cleaner output
    target_display = str(target_path).replace("/private/tmp/", "/tmp/")

    # Check if target exists and has content
    if target_path.exists() and any(target_path.iterdir()) and not force:
        overwrite = questionary.confirm(
            f"Directory {target_path} is not empty. Continue anyway?",
            default=False,
        ).ask()
        if not overwrite:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(0)

    # Select frontend
    frontend_choice = questionary.select(
        "Select your frontend app:",
        choices=list(FRONTENDS.keys()),
    ).ask()
    if not frontend_choice:
        console.print("[red]Aborted.[/red]")
        raise typer.Exit(1)

    # Select modules (multi-select)
    module_choices = questionary.checkbox(
        "Select modules to include:",
        choices=[
            questionary.Choice(
                f"{name} {'(Coming Soon)' if not info['available'] else ''}",
                value=name,
                disabled="Coming Soon" if not info["available"] else None,
            )
            for name, info in MODULES.items()
        ],
    ).ask()
    if module_choices is None:
        console.print("[red]Aborted.[/red]")
        raise typer.Exit(1)

    # Filter to only available modules
    selected_modules = [m for m in module_choices if MODULES[m]["available"]]

    # Prompt for environment configuration (use current env as defaults)
    console.print()
    console.print("[bold blue]Environment Configuration[/bold blue]")
    console.print("[dim]These values will be saved to .env in your app directory.[/dim]")
    console.print("[dim]Get an API key at https://albert.sites.beta.gouv.fr/access/[/dim]")
    console.print()

    env_config = {}

    env_config["openai_api_key"] = questionary.text(
        "OpenAI/Albert API Key:",
        default=os.getenv("OPENAI_API_KEY", ""),
    ).ask()
    if env_config["openai_api_key"] is None:
        console.print("[red]Aborted.[/red]")
        raise typer.Exit(1)

    env_config["openai_base_url"] = questionary.text(
        "OpenAI Base URL:",
        default=os.getenv("OPENAI_BASE_URL", "https://albert.api.etalab.gouv.fr/v1"),
    ).ask()
    if env_config["openai_base_url"] is None:
        console.print("[red]Aborted.[/red]")
        raise typer.Exit(1)

    env_config["openai_model"] = questionary.text(
        "Default model:",
        default=os.getenv("OPENAI_MODEL", "openweight-large"),
    ).ask()
    if env_config["openai_model"] is None:
        console.print("[red]Aborted.[/red]")
        raise typer.Exit(1)

    console.print()
    console.print("[bold blue]Configuration Summary[/bold blue]")
    console.print(f"  Target: {target_display}")
    console.print(f"  Frontend: {frontend_choice}")
    console.print(f"  Modules: {', '.join(selected_modules) if selected_modules else 'None'}")
    console.print(f"  API: {env_config['openai_base_url']}")
    console.print()

    # Confirm
    if not questionary.confirm("Proceed with generation?", default=True).ask():
        console.print("[yellow]Aborted.[/yellow]")
        raise typer.Exit(0)

    # Get templates directory
    templates_dir = get_templates_dir()
    if not templates_dir.exists():
        console.print(f"[red]Error: Templates directory not found at {templates_dir}[/red]")
        console.print("[dim]Make sure you're running from within the rag-facile repository.[/dim]")
        raise typer.Exit(1)

    # 2. Bootstrap with moon init
    console.print()
    console.print("[bold green]Step 1:[/bold green] Initializing Moon workspace...")
    if not target_path.exists():
        target_path.mkdir(parents=True)

    # moon init must be run from within the target directory
    if not run_command(
        ["moon", "init", "--yes"],
        "moon init",
        cwd=target_path,
    ):
        raise typer.Exit(1)
    console.print("[green]✓[/green] Moon workspace initialized")

    # 3. Apply system configuration patch
    console.print()
    console.print("[bold green]Step 2:[/bold green] Applying RAG Facile configuration...")

    # Copy templates to target (moon generate expects templates in the workspace)
    target_templates = target_path / ".moon" / "templates"
    if not target_templates.exists():
        target_templates.mkdir(parents=True)

    # Copy all templates to target workspace
    import shutil

    console.print(f"[dim]Copying templates from {templates_dir}[/dim]")
    for template_name in ["sys-config", "chainlit-chat", "reflex-chat", "pdf-context", "chroma-context"]:
        src = templates_dir / template_name
        dst = target_templates / template_name
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            console.print(f"[dim]  ✓ {template_name}[/dim]")
        else:
            console.print(f"[yellow]  ⚠ {template_name} not found at {src}[/yellow]")

    # Patch workspace.yml to add generator.templates BEFORE running moon generate
    # (moon needs this config to find templates, but sys-config template provides it)
    workspace_yml = target_path / ".moon" / "workspace.yml"
    if workspace_yml.exists():
        import yaml
        with open(workspace_yml) as f:
            config = yaml.safe_load(f) or {}
        if "generator" not in config:
            config["generator"] = {"templates": [".moon/templates"]}
            with open(workspace_yml, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            console.print("[dim]  ✓ Added generator.templates config[/dim]")

    # Run moon generate for sys-config from within the target (DEST is . since we're in the target)
    sys_config_cmd = ["moon", "generate", "sys-config", ".", "--defaults", "--force"]
    if not run_command(sys_config_cmd, "apply system config", cwd=target_path):
        raise typer.Exit(1)
    console.print("[green]✓[/green] System configuration applied")

    # 4. Generate the app with feature flags
    console.print()
    console.print(f"[bold green]Step 3:[/bold green] Generating {frontend_choice} app...")

    frontend_template = FRONTENDS[frontend_choice]
    # moon generate <NAME> --defaults --force [-- --bool_flag ...]
    # Don't pass DEST - let the template.yml destination be used (e.g., apps/chainlit-chat)
    app_cmd = ["moon", "generate", frontend_template, "--defaults"]
    if force:
        app_cmd.append("--force")

    # Add template variables and feature flags after --
    app_cmd.append("--")

    # Pass env config values to moon template
    app_cmd.append(f"--openai_api_key={env_config['openai_api_key']}")
    app_cmd.append(f"--openai_base_url={env_config['openai_base_url']}")
    app_cmd.append(f"--openai_model={env_config['openai_model']}")

    # Add feature flags (boolean variables passed as flags)
    if "PDF" in selected_modules:
        app_cmd.append("--use_pdf")
    if "Chroma" in selected_modules:
        app_cmd.append("--use_chroma")

    if not run_command(app_cmd, f"generate {frontend_template}", cwd=target_path):
        raise typer.Exit(1)
    console.print(f"[green]✓[/green] {frontend_choice} app generated")

    # Create .env file from template values
    app_dir = target_path / "apps" / frontend_template
    env_file = app_dir / ".env"
    env_content = f"""\
OPENAI_API_KEY={env_config['openai_api_key']}
OPENAI_BASE_URL={env_config['openai_base_url']}
OPENAI_MODEL={env_config['openai_model']}
"""
    env_file.write_text(env_content)
    console.print(f"[green]✓[/green] Created .env file")

    # 5. Generate selected packages
    if selected_modules:
        console.print()
        console.print("[bold green]Step 4:[/bold green] Generating packages...")

        for module in selected_modules:
            module_info = MODULES[module]
            if not module_info["available"]:
                console.print(f"[yellow]⚠[/yellow] {module} is not yet available, skipping...")
                continue

            template_name = module_info["template"]
            console.print(f"  Generating {module}...")
            # Don't pass DEST - let the template.yml destination be used
            pkg_cmd = ["moon", "generate", template_name, "--defaults"]
            if force:
                pkg_cmd.append("--force")
            if not run_command(pkg_cmd, f"generate {template_name}", cwd=target_path):
                raise typer.Exit(1)
            console.print(f"  [green]✓[/green] {module} package generated")

    # Done!
    console.print()
    console.print("[bold green]✨ Workspace generation complete![/bold green]")
    console.print()
    console.print("Next steps:")
    console.print(f"  cd {target_display}")
    console.print("  uv sync")
    console.print("  # Configure your .env file")
    console.print(f"  moon run {FRONTENDS[frontend_choice]}:dev")


if __name__ == "__main__":
    app()
