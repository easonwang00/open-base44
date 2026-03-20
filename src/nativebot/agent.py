"""Claude Agent SDK integration for streaming code generation.

Provides an async generator that yields normalized message dicts
from the Claude Agent SDK, with environment protection and session
continuity support.
"""

import os
import logging
from pathlib import Path
from typing import AsyncGenerator, Optional

from claude_agent_sdk import query, ClaudeAgentOptions

from .constants import ALLOWED_TOOLS, DEFAULT_MAX_TURNS, SENSITIVE_ENV_KEYS

logger = logging.getLogger(__name__)


async def run_generation(
    prompt: str,
    project_dir: Path,
    model: str = "claude-sonnet-4-6",
    session_id: Optional[str] = None,
    system_prompt: Optional[str] = None,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> AsyncGenerator[dict, None]:
    """Run Claude Agent SDK and yield normalized message dicts.

    Args:
        prompt: The user prompt to send to Claude.
        project_dir: Working directory for file operations.
        model: Claude model identifier.
        session_id: Optional session ID to resume a previous conversation.
        system_prompt: Optional custom system prompt text.
        max_turns: Maximum number of agent turns.

    Yields:
        Normalized message dicts from the SDK.
    """
    options = ClaudeAgentOptions(
        max_turns=max_turns,
        cwd=project_dir,
        model=model,
        allowed_tools=ALLOWED_TOOLS,
        permission_mode="bypassPermissions",
    )

    # Use a simple text system prompt — NOT the claude_code preset
    # The preset enables sub-agents (Task tool) which causes slow sleep/poll cycles
    from .constants import SYSTEM_RULES
    prompt_text = system_prompt or SYSTEM_RULES
    options.system_prompt = {"type": "text", "text": prompt_text}

    if session_id:
        options.resume = session_id

    # Hide sensitive env vars during execution
    hidden = {}
    for key in SENSITIVE_ENV_KEYS:
        if key in os.environ:
            hidden[key] = os.environ.pop(key)

    try:
        async for message in query(prompt=prompt, options=options):
            yield _normalize_message(message)
    finally:
        # Always restore hidden env vars
        for key, val in hidden.items():
            os.environ[key] = val


def _normalize_message(message) -> dict:
    """Convert an SDK message (object or dict) to a consistent dict format.

    Tags each message with a 'type' field based on its SDK class name:
    - AssistantMessage -> type='assistant'
    - SystemMessage -> type='system'
    - ResultMessage -> type='result'
    - StreamEvent -> type='stream_event'

    Preserves content blocks as-is (SDK objects with .text, .name, .input).
    """
    if isinstance(message, dict):
        return message

    # Detect SDK type and add 'type' field
    class_name = type(message).__name__
    type_map = {
        "AssistantMessage": "assistant",
        "SystemMessage": "system",
        "ResultMessage": "result",
        "StreamEvent": "stream_event",
        "UserMessage": "user",
        "RateLimitEvent": "rate_limit",
    }

    result = {"type": type_map.get(class_name, class_name.lower())}

    # Copy all public attributes
    for attr in dir(message):
        if attr.startswith("_"):
            continue
        try:
            val = getattr(message, attr)
            if not callable(val):
                result[attr] = val
        except Exception:
            pass

    if os.environ.get("NATIVEBOT_DEBUG"):
        logger.info(f"SDK message type={class_name} -> {result.get('type')} keys={list(result.keys())}")
        if "content" in result and isinstance(result["content"], list):
            for i, block in enumerate(result["content"]):
                block_type = getattr(block, "type", type(block).__name__)
                logger.info(f"  content[{i}] type={block_type}")

    return result


def extract_session_id(messages: list[dict]) -> Optional[str]:
    """Extract session_id from SDK messages for conversation continuity.

    Checks ResultMessage (subtype=success) and SystemMessage (subtype=init).
    """
    for msg in messages:
        if msg.get("subtype") == "success" and "session_id" in msg:
            return msg["session_id"]

    for msg in messages:
        if msg.get("subtype") == "init" and "data" in msg:
            data = msg["data"]
            if isinstance(data, dict) and "session_id" in data:
                return data["session_id"]

    return None


def extract_result_text(messages: list[dict]) -> Optional[str]:
    """Extract the final assistant text from SDK messages.

    Checks ResultMessage first, then falls back to the last
    AssistantMessage with text content.
    """
    # Check for ResultMessage
    for msg in messages:
        if msg.get("subtype") == "success" and "result" in msg:
            return msg["result"]

    # Fall back to last AssistantMessage with text content
    last_text = None
    for msg in messages:
        if "content" not in msg or not isinstance(msg["content"], list):
            continue
        parts = []
        for block in msg["content"]:
            if hasattr(block, "text"):
                parts.append(block.text)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        if parts:
            last_text = "\n".join(parts)

    return last_text


def extract_metadata(messages: list[dict]) -> dict:
    """Extract cost, duration, and session metadata from SDK messages."""
    metadata = {
        "session_id": None,
        "total_cost_usd": 0.0,
        "duration_ms": 0,
        "num_turns": 0,
        "model": None,
    }

    for message in messages:
        if message.get("subtype") == "success" and "total_cost_usd" in message:
            metadata.update(
                {
                    "total_cost_usd": message.get("total_cost_usd", 0.0),
                    "duration_ms": message.get("duration_ms", 0),
                    "num_turns": message.get("num_turns", 0),
                    "session_id": message.get("session_id"),
                }
            )
        elif message.get("subtype") == "init" and "data" in message:
            data = message["data"]
            if isinstance(data, dict):
                metadata.update(
                    {
                        "session_id": data.get("session_id"),
                        "model": data.get("model"),
                    }
                )

    return metadata
