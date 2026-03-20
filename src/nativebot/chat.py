"""Interactive chat loop for NativeBot.

Manages the conversation between the user and Claude inside a project,
with loading indicator, summary output, inline preview, and conversation
persistence.
"""

import asyncio
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Optional

from .agent import run_generation, extract_session_id, extract_result_text, extract_metadata
from .constants import DEFAULT_MODEL, SYSTEM_RULES
from .display import console, print_error
from .projects import (
    get_conversation,
    get_metadata,
    get_project_files,
    save_conversation,
)


def build_first_prompt(project_dir: Path, user_prompt: str) -> str:
    """Build the first prompt with file listing and directory context."""
    files = get_project_files(project_dir)
    file_listing = "\n".join(f"  {f}" for f in files[:100])
    extra = ""
    if len(files) > 100:
        extra = f"\n  ... and {len(files) - 100} more files"

    return f"""You are working inside: {project_dir}

{SYSTEM_RULES}

This project already has these files:
{file_listing}{extra}

Review the existing code and build on top of it.

User expo app generation request: {user_prompt}"""


def build_followup_prompt(project_dir: Path, user_prompt: str) -> str:
    """Build follow-up prompts with same rules."""
    return f"""You are working inside: {project_dir}

{SYSTEM_RULES}

{user_prompt}"""


def _parse_activity_from_block(block_str: str, project_dir_str: str) -> Optional[str]:
    """Parse a SDK content block string to extract activity info.

    SDK blocks come as strings like:
      ToolUseBlock(id='...', name='Edit', input={'file_path': '/path/to/file', ...})
      TextBlock(text='Done.')
    """
    import re

    # Match ToolUseBlock
    tool_match = re.search(r"ToolUseBlock\(.*?name='(\w+)'", block_str)
    if not tool_match:
        return None

    name = tool_match.group(1)

    # Extract file_path if present
    path_match = re.search(r"'file_path':\s*'([^']+)'", block_str)
    path = path_match.group(1) if path_match else ""
    # Make path relative
    path = path.replace(project_dir_str + "/", "")

    # Extract command for Bash
    cmd_match = re.search(r"'command':\s*'([^']*)'", block_str)
    cmd = cmd_match.group(1) if cmd_match else ""

    # Extract pattern for Glob/Grep
    pattern_match = re.search(r"'pattern':\s*'([^']*)'", block_str)
    pattern = pattern_match.group(1) if pattern_match else ""

    if name == "Bash":
        return f"Running: [dim]{cmd[:60]}[/dim]" if cmd else "Running command..."
    elif name == "Write":
        return f"Writing: [dim]{path}[/dim]" if path else "Writing file..."
    elif name == "Edit":
        return f"Editing: [dim]{path}[/dim]" if path else "Editing file..."
    elif name == "Read":
        return f"Reading: [dim]{path}[/dim]" if path else "Reading file..."
    elif name == "Glob":
        return f"Searching: [dim]{pattern}[/dim]" if pattern else "Searching files..."
    elif name == "Grep":
        return f"Searching: [dim]{pattern}[/dim]" if pattern else "Searching code..."
    else:
        return f"{name}..."


def _ensure_eas(project_dir: Path) -> bool:
    """Check eas-cli is installed and user is logged in. Returns True if ready."""
    import shutil

    if not shutil.which("eas"):
        console.print("[yellow]EAS CLI not found. Installing...[/yellow]")
        result = subprocess.run(["npm", "install", "-g", "eas-cli"], capture_output=False)
        if result.returncode != 0:
            console.print("[red]Failed to install eas-cli. Run: npm install -g eas-cli[/red]")
            return False

    whoami = subprocess.run(["eas", "whoami"], capture_output=True, text=True, cwd=project_dir)
    if whoami.returncode != 0:
        console.print("[yellow]You need to log in to Expo.[/yellow]")
        console.print("[dim]If you don't have an account, sign up at https://expo.dev[/dim]")
        console.print()
        login_result = subprocess.run(["eas", "login"], cwd=project_dir)
        if login_result.returncode != 0:
            console.print("[red]Login failed.[/red]")
            return False
    else:
        console.print(f"[green]Logged in as:[/green] {whoami.stdout.strip()}")

    eas_json = project_dir / "eas.json"
    if not eas_json.exists():
        console.print("[dim]Configuring EAS...[/dim]")
        subprocess.run(["eas", "build:configure", "--platform", "all"], cwd=project_dir)

    return True


def _pick_platform(command: str) -> Optional[str]:
    """Pick platform from command or ask interactively."""
    if "ios" in command:
        return "ios"
    if "android" in command:
        return "android"

    try:
        from InquirerPy import inquirer
        return inquirer.select(
            message="Platform:",
            choices=[
                {"name": "iOS (App Store)", "value": "ios"},
                {"name": "Android (Google Play)", "value": "android"},
                {"name": "Both", "value": "all"},
            ],
        ).execute()
    except ImportError:
        try:
            p = console.input("[bold cyan]Platform (ios/android/all):[/bold cyan] ").strip().lower()
            return p if p in ("ios", "android", "all") else None
        except (EOFError, KeyboardInterrupt):
            return None


def _build(project_dir: Path, project_name: str, command: str):
    """Build app with EAS."""
    console.print()
    if not _ensure_eas(project_dir):
        return

    platform = _pick_platform(command)
    if not platform:
        console.print("[red]Invalid platform.[/red]")
        return

    console.print()
    console.print(f"[bold]Building {project_name} for {platform}...[/bold]")
    console.print("[dim]This runs on Expo's build servers (5-15 minutes)[/dim]")
    console.print()

    build_result = subprocess.run(
        ["eas", "build", "--platform", platform, "--non-interactive"],
        cwd=project_dir,
    )

    if build_result.returncode != 0:
        console.print("[red]Build failed. Check the errors above.[/red]")
    else:
        console.print()
        console.print("[green]Build complete![/green]")
        console.print("[dim]Run 'submit' to submit to the store.[/dim]")
    console.print()


def _submit(project_dir: Path, project_name: str, command: str):
    """Submit app to App Store / Google Play."""
    console.print()
    if not _ensure_eas(project_dir):
        return

    platform = _pick_platform(command)
    if not platform:
        console.print("[red]Invalid platform.[/red]")
        return

    console.print()
    if platform in ("ios", "all"):
        console.print("[bold]Submitting to App Store...[/bold]")
        console.print("[dim]You'll need your Apple ID and an app-specific password.[/dim]")
        console.print("[dim]Generate one at: appleid.apple.com → Sign-In and Security → App-Specific Passwords[/dim]")
        console.print()
        subprocess.run(["eas", "submit", "--platform", "ios"], cwd=project_dir)

    if platform in ("android", "all"):
        console.print("[bold]Submitting to Google Play...[/bold]")
        console.print("[dim]You'll need a Google Play service account key.[/dim]")
        console.print("[dim]See: https://docs.expo.dev/submit/android/[/dim]")
        console.print()
        subprocess.run(["eas", "submit", "--platform", "android"], cwd=project_dir)

    console.print()
    console.print("[green]Done! Check your store dashboard for status.[/green]")
    console.print()


def _setup_env(project_dir: Path):
    """Interactive .env setup for Supabase and other services."""
    env_path = project_dir / ".env"
    existing = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                existing[key.strip()] = val.strip()

    console.print("[bold]Environment Variables[/bold]")
    console.print("[dim]Press Enter to keep existing value, or type new value[/dim]")
    console.print()

    env_vars = {
        "EXPO_PUBLIC_SUPABASE_URL": {
            "prompt": "Supabase URL",
            "hint": "https://yourproject.supabase.co",
        },
        "EXPO_PUBLIC_SUPABASE_ANON_KEY": {
            "prompt": "Supabase Anon Key",
            "hint": "eyJ...",
        },
    }

    updated = dict(existing)
    for key, info in env_vars.items():
        current = existing.get(key, "")
        display = f"{current[:20]}..." if len(current) > 20 else current
        prompt_text = f"  {info['prompt']}"
        if current:
            prompt_text += f" [{display}]"
        else:
            prompt_text += f" ({info['hint']})"

        try:
            val = console.input(f"{prompt_text}: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            return

        if val:
            updated[key] = val
        elif current:
            updated[key] = current

    # Write .env
    lines = []
    for key, val in updated.items():
        if val:
            lines.append(f"{key}={val}")
    env_path.write_text("\n".join(lines) + "\n")

    has_supabase = bool(updated.get("EXPO_PUBLIC_SUPABASE_URL"))
    console.print()
    console.print(f"[green]Saved .env[/green] ({len([v for v in updated.values() if v])} variables)")
    if has_supabase:
        console.print("[dim]Supabase is ready. Ask NativeBot to add auth, database, or storage.[/dim]")
    console.print()


def _launch_preview_background(project_dir: Path, web: bool = False):
    """Launch Expo preview in a new terminal window."""
    expo_cmd = "npx expo start --clear" + (" --web" if web else "")
    full_cmd = f"cd {project_dir} && npm install && {expo_cmd}"

    system = platform.system()
    if system == "Darwin":
        # macOS: create a temp script and open it in Terminal (no permission needed)
        import tempfile
        script_path = Path(tempfile.mktemp(suffix=".command"))
        script_path.write_text(f"#!/bin/bash\n{full_cmd}\n")
        script_path.chmod(0o755)
        subprocess.Popen(["open", str(script_path)])
    elif system == "Linux":
        # Try common terminal emulators
        for term in ["gnome-terminal", "xterm", "konsole"]:
            import shutil
            if shutil.which(term):
                if term == "gnome-terminal":
                    subprocess.Popen([term, "--", "bash", "-c", full_cmd])
                else:
                    subprocess.Popen([term, "-e", f"bash -c '{full_cmd}'"])
                break
        else:
            console.print(f"[dim]Run in another terminal: {full_cmd}[/dim]")
            return
    else:
        # Windows or unknown
        console.print(f"[dim]Run in another terminal: {full_cmd}[/dim]")
        return

    mode = "web browser" if web else "Expo Go"
    console.print(f"[green]Preview started in a new terminal ({mode})[/green]")
    if not web:
        console.print("[dim]Scan the QR code with Expo Go on your phone[/dim]")
    console.print()


async def chat_session(project_dir: Path, model: str = DEFAULT_MODEL):
    """Run an interactive chat session with Claude for a project."""
    metadata = get_metadata(project_dir) or {}
    conversation = get_conversation(project_dir)
    session_id: Optional[str] = None
    preview_running = False

    # Restore session_id from previous conversation
    if conversation:
        for msg in reversed(conversation):
            if msg.get("session_id"):
                session_id = msg["session_id"]
                break

    is_first = len(conversation) == 0
    turn_count = 0
    project_name = metadata.get("name", project_dir.name)

    console.print(f"[bold]Project:[/bold] {project_name}")
    console.print(f"[bold]Path:[/bold] {project_dir}")
    console.print(f"[bold]Model:[/bold] {model}")
    if session_id:
        console.print("[dim]Resuming previous session[/dim]")
    console.print()
    console.print("[dim]Commands:[/dim]")
    console.print("[dim]  preview       — Launch Expo Go preview in new terminal[/dim]")
    console.print("[dim]  preview web   — Launch web preview in new terminal[/dim]")
    console.print("[dim]  build         — Build app with EAS (iOS / Android)[/dim]")
    console.print("[dim]  submit        — Submit to App Store / Google Play[/dim]")
    console.print("[dim]  env           — Set up Supabase keys (for auth/database)[/dim]")
    console.print("[dim]  files         — Show project file tree[/dim]")
    console.print("[dim]  quit          — Exit chat[/dim]")
    console.print()

    while True:
        try:
            user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if not user_input:
            continue

        # --- Built-in commands ---
        lower = user_input.lower()

        if lower in ("quit", "exit", "q"):
            break

        if lower == "preview" or lower == "preview expo" or lower == "preview expo go":
            _launch_preview_background(project_dir, web=False)
            preview_running = True
            continue

        if lower == "preview web":
            _launch_preview_background(project_dir, web=True)
            preview_running = True
            continue

        if lower == "files":
            from .display import print_file_tree
            file_list = get_project_files(project_dir)
            print_file_tree(file_list, project_name)
            console.print()
            continue

        if lower == "env" or lower == "supabase":
            _setup_env(project_dir)
            continue

        if lower in ("build", "build ios", "build android"):
            _build(project_dir, project_name, lower)
            continue

        if lower in ("submit", "submit ios", "submit android", "deploy"):
            _submit(project_dir, project_name, lower)
            continue

        # --- AI generation ---
        if is_first and turn_count == 0:
            prompt = build_first_prompt(project_dir, user_input)
        else:
            prompt = build_followup_prompt(project_dir, user_input)

        conversation.append({"role": "user", "content": user_input})

        console.print()
        start_time = time.time()
        all_messages: list[dict] = []

        # Show live status with elapsed time (ticks every second)
        current_activity = "NativeBot is starting..."
        uses_subscription = not bool(os.environ.get("ANTHROPIC_API_KEY"))
        _timer_running = True

        def _format_time(seconds: int) -> str:
            if seconds < 60:
                return f"{seconds}s"
            m, s = divmod(seconds, 60)
            return f"{m}m{s:02d}s"

        def _status_text() -> str:
            elapsed = int(time.time() - start_time)
            return f"[bold magenta]{current_activity}[/bold magenta] [dim]— {_format_time(elapsed)}[/dim]"

        status = console.status(_status_text())

        async def _tick_timer():
            """Update the status every second so the timer ticks up."""
            while _timer_running:
                status.update(_status_text())
                await asyncio.sleep(1)

        timer_task = asyncio.create_task(_tick_timer())

        try:
            status.start()
            async for message in run_generation(
                prompt=prompt,
                project_dir=project_dir,
                model=model,
                session_id=session_id,
            ):
                all_messages.append(message)

                # Debug log
                if os.environ.get("NATIVEBOT_DEBUG"):
                    import json as _json
                    try:
                        raw = _json.dumps(message, indent=2, default=str)[:500]
                    except Exception:
                        raw = str(message)[:500]
                    with open("/tmp/nativebot_debug.log", "a") as f:
                        f.write(f"--- message ---\n{raw}\n\n")

                # Update status with what Claude is doing
                msg_type = message.get("type", "")
                content = message.get("content")
                if msg_type == "assistant" and isinstance(content, list):
                    found_activity = False
                    for block in content:
                        block_str = str(block)
                        activity = _parse_activity_from_block(block_str, str(project_dir))
                        if activity:
                            current_activity = activity
                            found_activity = True
                    if not found_activity:
                        current_activity = "NativeBot is thinking..."
                elif msg_type == "system":
                    current_activity = "NativeBot is starting..."
                elif msg_type == "user":
                    current_activity = "NativeBot is working..."

                status.update(_status_text())

                if message.get("subtype") == "success":
                    new_sid = message.get("session_id")
                    if new_sid:
                        session_id = new_sid
            _timer_running = False
            timer_task.cancel()
            status.stop()

        except Exception as e:
            _timer_running = False
            timer_task.cancel()
            status.stop()
            print_error(str(e))
            save_conversation(project_dir, conversation)
            continue

        # Install dependencies after generation
        with console.status("[bold cyan]Installing dependencies...[/bold cyan]"):
            install_result = subprocess.run(
                ["npm", "install"],
                cwd=project_dir,
                capture_output=True,
                text=True,
            )

        # Self-heal: if npm install failed, ask NativeBot to fix it
        if install_result.returncode != 0:
            npm_error = (install_result.stderr or install_result.stdout or "")[-1500:]
            fix_prompt = f"""IMPORTANT: You are working inside: {project_dir}
ALL file operations MUST stay within this directory.

`npm install` failed with this error:

{npm_error}

Fix the issue. Common fixes:
- If a package is missing or incompatible, update package.json with correct versions
- If there are peer dependency conflicts, adjust versions to be compatible
- Do NOT use --legacy-peer-deps or --force
- After fixing, run: npm install
"""
            console.print("[yellow]Fixing dependency issues...[/yellow]")
            try:
                with console.status("[bold magenta]NativeBot is fixing dependencies...[/bold magenta]"):
                    async for msg in run_generation(
                        prompt=fix_prompt,
                        project_dir=project_dir,
                        model=model,
                        session_id=session_id,
                    ):
                        all_messages.append(msg)
                        if msg.get("subtype") == "success":
                            new_sid = msg.get("session_id")
                            if new_sid:
                                session_id = new_sid
            except Exception:
                pass

        # Verify build: run expo export check (typecheck without actually starting)
        with console.status("[bold cyan]Verifying build...[/bold cyan]"):
            verify_result = subprocess.run(
                ["npx", "expo", "export", "--dump-sourcemap", "--output-dir", "/tmp/nativebot-verify-build"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            # Clean up temp build
            import shutil as _shutil
            _shutil.rmtree("/tmp/nativebot-verify-build", ignore_errors=True)

        # Self-heal: if build verification failed, ask NativeBot to fix it
        if verify_result.returncode != 0:
            build_error = (verify_result.stderr or verify_result.stdout or "")[-2000:]
            fix_prompt = f"""IMPORTANT: You are working inside: {project_dir}
ALL file operations MUST stay within this directory.

The app failed to build. Here is the error from `npx expo export`:

{build_error}

Fix the issue. Common fixes:
- Missing module: install it with `npm install <package>` or fix the import
- TypeScript error: fix the type issue in the source file
- Babel/Metro config error: fix babel.config.js or metro.config.js
- Cannot resolve: check the import path is correct

After fixing, run: npm install
Do NOT run expo start or expo export yourself.
"""
            console.print("[yellow]Fixing build errors...[/yellow]")
            try:
                with console.status("[bold magenta]NativeBot is fixing build errors...[/bold magenta]"):
                    async for msg in run_generation(
                        prompt=fix_prompt,
                        project_dir=project_dir,
                        model=model,
                        session_id=session_id,
                    ):
                        all_messages.append(msg)
                        if msg.get("subtype") == "success":
                            new_sid = msg.get("session_id")
                            if new_sid:
                                session_id = new_sid
            except Exception:
                pass

        duration = time.time() - start_time

        # Extract results
        result_text = extract_result_text(all_messages)
        meta = extract_metadata(all_messages)
        new_sid = extract_session_id(all_messages)
        if new_sid:
            session_id = new_sid

        # Show summary
        turns = meta.get("num_turns", 0)
        cost = meta.get("total_cost_usd", 0)

        if uses_subscription:
            cost_str = f"saved ${cost:.4f}" if cost else ""
        else:
            cost_str = f"${cost:.4f}" if cost else ""

        parts = [f"{duration:.0f}s"]
        if turns:
            parts.append(f"{turns} turns")
        if cost_str:
            parts.append(cost_str)

        console.print(f"[green]Done![/green] [dim]({', '.join(parts)})[/dim]")

        if result_text:
            # Show a brief summary, not the full Claude response
            lines = result_text.strip().split("\n")
            summary = "\n".join(lines[:8])
            if len(lines) > 8:
                summary += f"\n[dim]... ({len(lines) - 8} more lines)[/dim]"
            console.print()
            console.print(summary)

        console.print()

        # Hint about preview if not running
        if not preview_running and turn_count == 0:
            console.print("[dim]Type 'preview' to see your app in Expo Go[/dim]")
            console.print()

        # Save conversation
        conversation.append(
            {
                "role": "assistant",
                "content": result_text or "(no text response)",
                "session_id": session_id,
            }
        )
        save_conversation(project_dir, conversation)

        turn_count += 1

    console.print("[dim]Chat ended.[/dim]")
