"""Rich console formatting for NativeBot CLI.

Provides consistent, colorful terminal output for project listings,
activity logs, file trees, and generation progress.
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.tree import Tree

console = Console()


def print_banner():
    """Print the NativeBot welcome banner."""
    console.print()
    console.print("[bold bright_cyan]  NativeBot[/bold bright_cyan]", justify="center")
    console.print(
        "[dim]AI App Builder -- Create mobile apps by chatting with AI[/dim]",
        justify="center",
    )
    console.print()


def print_project_list(projects: list[dict]):
    """Print a formatted table of projects."""
    if not projects:
        console.print("[dim]No projects yet. Create one to get started![/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="bold")
    table.add_column("Description", style="dim")
    table.add_column("Files", justify="right")
    table.add_column("Created", style="dim")

    for i, p in enumerate(projects, 1):
        table.add_row(
            str(i),
            p["name"],
            p.get("description", "")[:50],
            str(p.get("file_count", 0)),
            p.get("created_at", "")[:10],
        )

    console.print(table)


def print_activity(text: str):
    """Print a Claude activity line (tool use)."""
    console.print(f"  [dim]|--[/dim] [yellow]{text}[/yellow]")


def print_activity_last(text: str):
    """Print the last activity line in a group."""
    console.print(f"  [dim]`--[/dim] [yellow]{text}[/yellow]")


def print_assistant_text(text: str):
    """Print assistant response text as rendered Markdown."""
    console.print()
    console.print(Markdown(text))
    console.print()


def print_done(changed_files: list[str], duration_s: float = 0):
    """Print generation complete summary."""
    count = len(changed_files)
    time_str = f" in {duration_s:.0f}s" if duration_s else ""
    console.print()
    console.print(
        f"  [bold green]Done![/bold green] "
        f"{count} file{'s' if count != 1 else ''} changed{time_str}"
    )
    if changed_files:
        for f in changed_files[:10]:
            console.print(f"     [dim]{f}[/dim]")
        if len(changed_files) > 10:
            console.print(f"     [dim]... and {len(changed_files) - 10} more[/dim]")
    console.print()


def print_error(text: str):
    """Print an error message."""
    console.print(f"  [bold red]Error:[/bold red] {text}")


def print_file_tree(files: list[str], project_name: str):
    """Print a tree view of project files."""
    tree = Tree(f"[bold]{project_name}[/bold]")
    dirs: dict[str, object] = {}

    for f in sorted(files):
        parts = f.split("/")
        current = tree
        for i, part in enumerate(parts[:-1]):
            key = "/".join(parts[: i + 1])
            if key not in dirs:
                dirs[key] = current.add(f"[bold blue]{part}/[/bold blue]")
            current = dirs[key]
        current.add(f"[green]{parts[-1]}[/green]")

    console.print(tree)
