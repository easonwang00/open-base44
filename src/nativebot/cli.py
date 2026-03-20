"""NativeBot CLI -- main entry point.

Provides both a subcommand interface (nativebot create, nativebot open, etc.)
and a fully interactive menu when run without arguments.
"""

import asyncio
import os
import sys
from pathlib import Path

import click

from . import __version__
from .constants import DEFAULT_MODEL, MODELS
from .display import console, print_banner, print_file_tree, print_project_list
from .projects import (
    create_project,
    delete_project,
    get_project,
    get_project_files,
    list_projects,
)


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="nativebot")
@click.pass_context
def cli(ctx):
    """NativeBot -- Build mobile apps by chatting with AI."""
    if ctx.invoked_subcommand is None:
        interactive_menu()


@cli.command()
@click.argument("name")
@click.option("--description", "-d", default="", help="Project description")
def create(name: str, description: str):
    """Create a new project."""
    try:
        with console.status("[bold cyan]Preparing workspace...[/bold cyan]"):
            project_dir = create_project(name, description)
        console.print(f"[green]Project created:[/green] {project_dir}")
        console.print(f"[dim]Run 'nativebot open {name}' to start building[/dim]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command("list")
def list_cmd():
    """List all projects."""
    projects = list_projects()
    print_project_list(projects)


@cli.command()
@click.argument("name")
@click.option(
    "--model",
    "-m",
    default=None,
    help="Claude model: sonnet, opus, haiku, or full model ID",
)
def open(name: str, model: str):
    """Open a project and start chatting with Claude."""
    project = get_project(name)
    if not project:
        console.print(f"[red]Project '{name}' not found.[/red]")
        console.print("[dim]Run 'nativebot list' to see available projects.[/dim]")
        sys.exit(1)

    # Resolve model alias or use as-is
    model_id = MODELS.get(model, model) if model else DEFAULT_MODEL

    project_dir = Path(project["path"])

    from .chat import chat_session

    asyncio.run(chat_session(project_dir, model=model_id))


@cli.command()
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this project?")
def delete(name: str):
    """Delete a project."""
    if delete_project(name):
        console.print(f"[green]Deleted project '{name}'[/green]")
    else:
        console.print(f"[red]Project '{name}' not found.[/red]")
        sys.exit(1)



def _run_preview(project_dir: Path, project_name: str, web: bool = False):
    """Install deps and launch Expo preview."""
    import subprocess

    console.print(f"[bold]Previewing:[/bold] {project_name}")
    console.print(f"[dim]{project_dir}[/dim]")
    console.print()

    # Always reinstall dependencies to ensure they're fresh and up to date
    console.print("[yellow]Installing dependencies...[/yellow]")
    console.print()
    result = subprocess.run(
        ["npm", "install"],
        cwd=project_dir,
        capture_output=False,
    )
    if result.returncode != 0:
        console.print("[red]npm install failed. Fix errors above and try again.[/red]")
        return

    # Clear Metro cache to avoid stale bundles
    expo_dir = project_dir / ".expo"
    if expo_dir.exists():
        import shutil
        shutil.rmtree(expo_dir, ignore_errors=True)

    console.print()

    if web:
        console.print("[bold cyan]Starting web preview...[/bold cyan]")
        console.print("[dim]Your app will open in the browser.[/dim]")
        console.print()
        os.chdir(project_dir)
        os.execvp("npx", ["npx", "expo", "start", "--web", "--clear"])
    else:
        console.print("[bold cyan]Starting Expo Go preview...[/bold cyan]")
        console.print("[dim]Scan the QR code with Expo Go on your phone.[/dim]")
        console.print("[dim]iOS: Camera app → scan QR. Android: Expo Go app → scan QR.[/dim]")
        console.print()
        os.chdir(project_dir)
        os.execvp("npx", ["npx", "expo", "start", "--clear"])


@cli.command()
@click.argument("name")
def files(name: str):
    """Show project file tree."""
    project = get_project(name)
    if not project:
        console.print(f"[red]Project '{name}' not found.[/red]")
        sys.exit(1)

    project_dir = Path(project["path"])
    file_list = get_project_files(project_dir)
    print_file_tree(file_list, project["name"])


@cli.command()
@click.argument("name")
def export(name: str):
    """Show how to build and submit your app."""
    project = get_project(name)
    if not project:
        console.print(f"[red]Project '{name}' not found.[/red]")
        sys.exit(1)

    project_dir = project["path"]
    console.print(
        f"""
[bold]Build & Submit Your App[/bold]

[bold cyan]1. Navigate to your project:[/bold cyan]
   cd {project_dir}

[bold cyan]2. Install EAS CLI:[/bold cyan]
   npm install -g eas-cli

[bold cyan]3. Login to Expo:[/bold cyan]
   eas login

[bold cyan]4. Build for iOS:[/bold cyan]
   eas build --platform ios

[bold cyan]5. Submit to App Store:[/bold cyan]
   eas submit --platform ios

[bold cyan]6. Build for Android:[/bold cyan]
   eas build --platform android
"""
    )


@cli.command()
@click.option("--token", "-t", default=None, help="Telegram bot token (or set TELEGRAM_BOT_TOKEN)")
def telegram(token: str):
    """Start the Telegram bot interface."""
    bot_token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        console.print("[red]Telegram bot token required.[/red]")
        console.print()
        console.print("[bold]Setup:[/bold]")
        console.print("  1. Message @BotFather on Telegram → /newbot")
        console.print("  2. Copy the token")
        console.print("  3. Run: [cyan]export TELEGRAM_BOT_TOKEN=your-token[/cyan]")
        console.print("     Or: [cyan]nativebot telegram --token your-token[/cyan]")
        sys.exit(1)

    from .telegram_bot import run_telegram_bot

    run_telegram_bot(bot_token)


def interactive_menu():
    """Interactive menu when nativebot is run without arguments."""
    try:
        from InquirerPy import inquirer
    except ImportError:
        console.print(
            "[red]InquirerPy is required for interactive mode.[/red]"
        )
        console.print("[dim]Install it: pip install InquirerPy[/dim]")
        console.print("[dim]Or use subcommands: nativebot create, nativebot open, etc.[/dim]")
        sys.exit(1)

    print_banner()

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        import shutil

        if not shutil.which("claude"):
            console.print("[yellow]Warning: ANTHROPIC_API_KEY not set.[/yellow]")
            console.print("[dim]Set it: export ANTHROPIC_API_KEY=sk-ant-...[/dim]")
            console.print(
                "[dim]Or login with Claude CLI: claude auth login[/dim]"
            )
            console.print()

    while True:
        projects = list_projects()

        choices = ["Create new app"]
        if projects:
            choices.insert(0, "Open existing app")
            choices.append("Delete app")
        choices.append("Exit")

        action = inquirer.select(
            message="What would you like to do?",
            choices=choices,
        ).execute()

        if action == "Exit":
            console.print("[dim]Goodbye![/dim]")
            break

        elif action == "Create new app":
            name = inquirer.text(message="App name:").execute()
            if not name.strip():
                continue

            try:
                with console.status("[bold cyan]Preparing workspace...[/bold cyan]"):
                    project_dir = create_project(name.strip())
                console.print(
                    f"[green]Created '{name}'[/green] at {project_dir}"
                )
                console.print()

                start = inquirer.confirm(
                    message="Start building now?", default=True
                ).execute()
                if start:
                    model_choice = inquirer.select(
                        message="Choose model:",
                        choices=[
                            {
                                "name": "Sonnet 4.6 (recommended)",
                                "value": "claude-sonnet-4-6",
                            },
                            {
                                "name": "Opus 4.6 (most capable)",
                                "value": "claude-opus-4-6",
                            },
                            {
                                "name": "Haiku 4.5 (fastest)",
                                "value": "claude-haiku-4-5-20251001",
                            },
                        ],
                    ).execute()

                    from .chat import chat_session

                    asyncio.run(
                        chat_session(project_dir, model=model_choice)
                    )
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        elif action == "Open existing app":
            project_choices = [
                {
                    "name": f"{p['name']} ({p.get('file_count', 0)} files)",
                    "value": p,
                }
                for p in projects
            ]
            selected = inquirer.select(
                message="Select app:", choices=project_choices
            ).execute()

            model_choice = inquirer.select(
                message="Choose model:",
                choices=[
                    {
                        "name": "Sonnet 4.6 (recommended)",
                        "value": "claude-sonnet-4-6",
                    },
                    {
                        "name": "Opus 4.6 (most capable)",
                        "value": "claude-opus-4-6",
                    },
                    {
                        "name": "Haiku 4.5 (fastest)",
                        "value": "claude-haiku-4-5-20251001",
                    },
                ],
            ).execute()

            from .chat import chat_session

            asyncio.run(
                chat_session(
                    Path(selected["path"]), model=model_choice
                )
            )

        elif action == "Delete app":
            project_choices = [
                {"name": p["name"], "value": p["name"]} for p in projects
            ]
            selected = inquirer.select(
                message="Select app to delete:",
                choices=project_choices,
            ).execute()

            confirm = inquirer.confirm(
                message=f"Delete '{selected}'? This cannot be undone.",
                default=False,
            ).execute()
            if confirm:
                delete_project(selected)
                console.print(f"[green]Deleted '{selected}'[/green]")

        console.print()


def main():
    """Entry point for the nativebot command."""
    cli()


if __name__ == "__main__":
    main()
