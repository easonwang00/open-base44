"""Telegram bot interface for NativeBot.

Lets users create and chat with NativeBot projects from Telegram.
Runs as a self-hosted bot using python-telegram-bot.
"""

import asyncio
import html
import json
import logging
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .agent import run_generation, extract_session_id, extract_result_text, extract_metadata
from .chat import build_first_prompt, build_followup_prompt, _parse_activity_from_block
from .constants import DEFAULT_MODEL, MODELS
from .projects import (
    create_project,
    delete_project,
    get_project,
    get_project_files,
    list_projects,
    get_conversation,
    save_conversation,
)

logger = logging.getLogger(__name__)

# File to persist chat_id -> active project mapping
SESSIONS_FILE = Path.home() / ".nativebot" / "telegram_sessions.json"

# Telegram message length limit
MAX_MESSAGE_LEN = 4000


def _load_sessions() -> dict:
    """Load telegram sessions from disk."""
    if SESSIONS_FILE.exists():
        try:
            return json.loads(SESSIONS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_sessions(sessions: dict):
    """Save telegram sessions to disk."""
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_FILE.write_text(json.dumps(sessions, indent=2))


def _get_active_project(chat_id: int) -> Optional[dict]:
    """Get the active project for a chat."""
    sessions = _load_sessions()
    project_name = sessions.get(str(chat_id))
    if project_name:
        return get_project(project_name)
    return None


def _set_active_project(chat_id: int, project_name: str):
    """Set the active project for a chat."""
    sessions = _load_sessions()
    sessions[str(chat_id)] = project_name
    _save_sessions(sessions)


def _clear_active_project(chat_id: int):
    """Clear the active project for a chat."""
    sessions = _load_sessions()
    sessions.pop(str(chat_id), None)
    _save_sessions(sessions)


def _escape(text: str) -> str:
    """Escape HTML for Telegram."""
    return html.escape(text)


def _split_message(text: str) -> list[str]:
    """Split a long message into chunks that fit Telegram's limit."""
    if len(text) <= MAX_MESSAGE_LEN:
        return [text]

    chunks = []
    while text:
        if len(text) <= MAX_MESSAGE_LEN:
            chunks.append(text)
            break
        # Try to split at a newline
        cut = text.rfind("\n", 0, MAX_MESSAGE_LEN)
        if cut == -1:
            cut = MAX_MESSAGE_LEN
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    return chunks


async def _send_long(update: Update, text: str, parse_mode=None):
    """Send a message, splitting if too long."""
    for chunk in _split_message(text):
        try:
            await update.message.reply_text(chunk, parse_mode=parse_mode)
        except Exception:
            # If HTML parsing fails, send as plain text
            await update.message.reply_text(chunk)


# --- Command Handlers ---

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "🚀 <b>NativeBot</b> — Build mobile apps by chatting with AI\n\n"
        "<b>Commands:</b>\n"
        "/create <code>AppName</code> — Create a new project\n"
        "/open <code>AppName</code> — Open a project to chat\n"
        "/list — List all projects\n"
        "/files — Show file tree of active project\n"
        "/preview — Get Expo preview URL/QR for your phone\n"
        "/model <code>sonnet|opus|haiku</code> — Switch model\n"
        "/close — Close active project\n"
        "/delete <code>AppName</code> — Delete a project\n\n"
        "Or just send a message to chat with Claude about your active project!",
        parse_mode=ParseMode.HTML,
    )


async def cmd_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /create <name> command."""
    if not context.args:
        await update.message.reply_text("Usage: /create <code>AppName</code>", parse_mode=ParseMode.HTML)
        return

    name = " ".join(context.args)
    try:
        project_dir = create_project(name)
        _set_active_project(update.effective_chat.id, name)
        await update.message.reply_text(
            f"✅ Created <b>{_escape(name)}</b>\n"
            f"📁 {_escape(str(project_dir))}\n\n"
            "Project is now active. Send a message to start building!",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await update.message.reply_text(f"❌ {_escape(str(e))}", parse_mode=ParseMode.HTML)


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list command."""
    projects = list_projects()
    if not projects:
        await update.message.reply_text("No projects yet. Create one with /create <code>AppName</code>", parse_mode=ParseMode.HTML)
        return

    active = _get_active_project(update.effective_chat.id)
    active_slug = active["slug"] if active else None

    lines = ["<b>Your Projects:</b>\n"]
    for p in projects:
        marker = " 👈 active" if p["slug"] == active_slug else ""
        lines.append(f"• <b>{_escape(p['name'])}</b> ({p.get('file_count', 0)} files){marker}")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def cmd_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /open <name> command."""
    if not context.args:
        await update.message.reply_text("Usage: /open <code>AppName</code>", parse_mode=ParseMode.HTML)
        return

    name = " ".join(context.args)
    project = get_project(name)
    if not project:
        await update.message.reply_text(
            f"❌ Project '{_escape(name)}' not found.\nRun /list to see your projects.",
            parse_mode=ParseMode.HTML,
        )
        return

    _set_active_project(update.effective_chat.id, project["name"])
    await update.message.reply_text(
        f"📂 Opened <b>{_escape(project['name'])}</b> ({project.get('file_count', 0)} files)\n\n"
        "Send a message to chat with Claude about this project.",
        parse_mode=ParseMode.HTML,
    )


async def cmd_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /close command."""
    _clear_active_project(update.effective_chat.id)
    await update.message.reply_text("Closed active project. Use /open to switch to another.")


async def cmd_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /files command."""
    project = _get_active_project(update.effective_chat.id)
    if not project:
        await update.message.reply_text("No active project. Use /open <code>AppName</code> first.", parse_mode=ParseMode.HTML)
        return

    project_dir = Path(project["path"])
    files = get_project_files(project_dir)
    if not files:
        await update.message.reply_text("No files in this project yet.")
        return

    tree = f"<b>{_escape(project['name'])}</b> ({len(files)} files)\n\n"
    tree += "<code>" + _escape("\n".join(files[:50])) + "</code>"
    if len(files) > 50:
        tree += f"\n... and {len(files) - 50} more"

    await _send_long(update, tree, parse_mode=ParseMode.HTML)


async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delete <name> command."""
    if not context.args:
        await update.message.reply_text("Usage: /delete <code>AppName</code>", parse_mode=ParseMode.HTML)
        return

    name = " ".join(context.args)
    if delete_project(name):
        # Clear if it was the active project
        active = _get_active_project(update.effective_chat.id)
        if active and active["name"].lower() == name.lower():
            _clear_active_project(update.effective_chat.id)
        await update.message.reply_text(f"🗑️ Deleted '{_escape(name)}'", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"❌ Project '{_escape(name)}' not found.", parse_mode=ParseMode.HTML)


async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /model <name> command."""
    if not context.args:
        sessions = _load_sessions()
        current = sessions.get(f"{update.effective_chat.id}_model", "sonnet")
        await update.message.reply_text(
            f"Current model: <b>{_escape(current)}</b>\n\n"
            "Usage: /model <code>sonnet|opus|haiku</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    alias = context.args[0].lower()
    if alias not in MODELS:
        await update.message.reply_text(
            f"Unknown model '{_escape(alias)}'. Choose: sonnet, opus, haiku",
            parse_mode=ParseMode.HTML,
        )
        return

    sessions = _load_sessions()
    sessions[f"{update.effective_chat.id}_model"] = alias
    _save_sessions(sessions)
    await update.message.reply_text(f"Model set to <b>{_escape(alias)}</b> ({_escape(MODELS[alias])})", parse_mode=ParseMode.HTML)


def _get_local_ip() -> str:
    """Get the machine's local network IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


async def cmd_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /preview command — start Expo and send URL/QR back."""
    project = _get_active_project(update.effective_chat.id)
    if not project:
        await update.message.reply_text("No active project. Use /open <code>AppName</code> first.", parse_mode=ParseMode.HTML)
        return

    project_dir = Path(project["path"])
    project_name = project["name"]

    await update.message.reply_text(
        f"📱 Starting preview for <b>{_escape(project_name)}</b>...\nThis may take a moment.",
        parse_mode=ParseMode.HTML,
    )

    # Install deps first
    install = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: subprocess.run(["npm", "install"], cwd=project_dir, capture_output=True, text=True),
    )
    if install.returncode != 0:
        await update.message.reply_text("❌ npm install failed. Check your project for errors.")
        return

    # Start expo in background
    process = subprocess.Popen(
        ["npx", "expo", "start", "--clear", "--port", "0"],
        cwd=project_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Read output in a thread to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    metro_port = None
    start_time = time.time()
    timeout = 60

    output_lines = []

    def _read_until_ready():
        """Read Expo output until we detect the server is ready. Returns the port."""
        nonlocal metro_port
        while time.time() - start_time < timeout:
            line = process.stdout.readline()
            if not line:
                if process.poll() is not None:
                    break  # Process exited
                continue

            output_lines.append(line.rstrip())
            logger.info(f"[expo] {line.rstrip()}")

            # Expo outputs: "Waiting on http://localhost:8081"
            port_match = re.search(r'http://localhost:(\d+)', line)
            if port_match:
                metro_port = port_match.group(1)

            # Ready indicator
            if "Logs for your project" in line or "Waiting on" in line:
                if metro_port:
                    return metro_port

            # Also check for exp:// URL directly (some Expo versions)
            exp_match = re.search(r'(exp://[\S]+)', line)
            if exp_match:
                return exp_match.group(1)

        return metro_port

    result = await loop.run_in_executor(None, _read_until_ready)

    if result:
        # Build the exp:// URL from local IP + port
        local_ip = _get_local_ip()
        if result.startswith("exp://"):
            expo_url = result
        else:
            expo_url = f"exp://{local_ip}:{result}"

        await update.message.reply_text(
            f"✅ <b>{_escape(project_name)}</b> is running!\n\n"
            f"📱 Open in Expo Go:\n<code>{_escape(expo_url)}</code>\n\n"
            "On your phone:\n"
            "• iOS: Open Camera app → paste URL in Safari\n"
            "• Android: Open Expo Go → Enter URL above\n\n"
            f"🌐 Local: <code>http://localhost:{_escape(metro_port or '8081')}</code>\n\n"
            "<i>Preview is running in the background. Keep chatting!</i>",
            parse_mode=ParseMode.HTML,
        )

        # Store the process so we can reference it later
        if "preview_processes" not in context.bot_data:
            context.bot_data["preview_processes"] = {}
        context.bot_data["preview_processes"][update.effective_chat.id] = {
            "process": process,
            "url": expo_url,
            "project": project_name,
        }
    else:
        # Kill the process if we couldn't get a URL
        process.terminate()

        # Collect any remaining output
        try:
            remaining, _ = process.communicate(timeout=5)
            if remaining:
                output_lines.extend(remaining.strip().splitlines())
        except Exception:
            pass

        # Send error with the actual Expo output
        error_output = "\n".join(output_lines[-30:]) if output_lines else "No output captured"
        await _send_long(
            update,
            f"❌ Expo failed to start.\n\n"
            f"<b>Error output:</b>\n<code>{_escape(error_output)}</code>\n\n"
            f"Run manually:\n<code>cd {_escape(str(project_dir))} && npx expo start</code>",
            parse_mode=ParseMode.HTML,
        )


# --- Chat Handler ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages — forward to Claude as chat turns."""
    project = _get_active_project(update.effective_chat.id)
    if not project:
        await update.message.reply_text(
            "No active project. Use /create or /open first.\n"
            "Send /start for help."
        )
        return

    project_dir = Path(project["path"])
    project_name = project["name"]
    user_input = update.message.text.strip()

    if not user_input:
        return

    # Load conversation and session
    conversation = get_conversation(project_dir)
    session_id: Optional[str] = None
    if conversation:
        for msg in reversed(conversation):
            if msg.get("session_id"):
                session_id = msg["session_id"]
                break

    is_first = len(conversation) == 0

    # Get model
    sessions = _load_sessions()
    model_alias = sessions.get(f"{update.effective_chat.id}_model", "sonnet")
    model = MODELS.get(model_alias, DEFAULT_MODEL)

    # Build prompt
    if is_first:
        prompt = build_first_prompt(project_dir, user_input)
    else:
        prompt = build_followup_prompt(project_dir, user_input)

    conversation.append({"role": "user", "content": user_input})

    # Send "working" indicator
    await update.effective_chat.send_action(ChatAction.TYPING)
    status_msg = await update.message.reply_text(
        f"🤖 Working on <b>{_escape(project_name)}</b>...",
        parse_mode=ParseMode.HTML,
    )

    start_time = time.time()
    all_messages: list[dict] = []
    last_activity = ""
    last_update_time = 0.0

    try:
        async for message in run_generation(
            prompt=prompt,
            project_dir=project_dir,
            model=model,
            session_id=session_id,
        ):
            all_messages.append(message)

            # Update status message with current activity (max once per 3s to avoid rate limits)
            msg_type = message.get("type", "")
            content = message.get("content")
            if msg_type == "assistant" and isinstance(content, list):
                for block in content:
                    activity = _parse_activity_from_block(str(block), str(project_dir))
                    if activity:
                        # Strip Rich markup for Telegram
                        clean_activity = re.sub(r'\[/?[a-z ]+\]', '', activity)
                        if clean_activity != last_activity and time.time() - last_update_time > 3:
                            last_activity = clean_activity
                            last_update_time = time.time()
                            elapsed = int(time.time() - start_time)
                            try:
                                await status_msg.edit_text(
                                    f"🤖 <b>{_escape(project_name)}</b> — {elapsed}s\n{_escape(clean_activity)}",
                                    parse_mode=ParseMode.HTML,
                                )
                            except Exception:
                                pass  # Ignore edit failures (rate limit, message unchanged)

            # Keep sending typing action
            if time.time() - last_update_time > 5:
                await update.effective_chat.send_action(ChatAction.TYPING)

            if message.get("subtype") == "success":
                new_sid = message.get("session_id")
                if new_sid:
                    session_id = new_sid

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {_escape(str(e))}", parse_mode=ParseMode.HTML)
        save_conversation(project_dir, conversation)
        return

    # Run npm install
    subprocess.run(
        ["npm", "install"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )

    duration = time.time() - start_time
    result_text = extract_result_text(all_messages)
    meta = extract_metadata(all_messages)
    new_sid = extract_session_id(all_messages)
    if new_sid:
        session_id = new_sid

    # Build summary
    turns = meta.get("num_turns", 0)
    cost = meta.get("total_cost_usd", 0)

    parts = [f"{duration:.0f}s"]
    if turns:
        parts.append(f"{turns} turns")
    if cost:
        parts.append(f"${cost:.4f}")

    summary = f"✅ Done! ({', '.join(parts)})"

    # Delete the status message
    try:
        await status_msg.delete()
    except Exception:
        pass

    # Send the result
    if result_text:
        response = f"{summary}\n\n{result_text}"
    else:
        response = summary

    await _send_long(update, response)

    # Save conversation
    conversation.append({
        "role": "assistant",
        "content": result_text or "(no text response)",
        "session_id": session_id,
    })
    save_conversation(project_dir, conversation)


def run_telegram_bot(token: str):
    """Start the Telegram bot with the given token."""
    app = Application.builder().token(token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("create", cmd_create))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("open", cmd_open))
    app.add_handler(CommandHandler("close", cmd_close))
    app.add_handler(CommandHandler("files", cmd_files))
    app.add_handler(CommandHandler("preview", cmd_preview))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("delete", cmd_delete))

    # Text messages go to chat handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 NativeBot Telegram bot is running!")
    print("Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
