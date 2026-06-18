"""
Conversation Memory Module.

Provides in-memory conversation history management for agent interactions.
Stores messages as a simple list of dictionaries with role and content.
Designed to be replaced with a persistent store in future phases.
"""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# In-memory conversation store
_conversation_history: list[dict[str, Any]] = []


def save_message(role: str, content: str) -> None:
    """
    Save a message to the conversation history.

    Args:
        role: The role of the message sender (e.g., 'user', 'assistant', 'system').
        content: The text content of the message.
    """
    message: dict[str, Any] = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _conversation_history.append(message)
    logger.debug(
        "Message saved to memory. Role: '%s', History length: %d.",
        role,
        len(_conversation_history),
    )


def load_messages() -> list[dict[str, Any]]:
    """
    Load all messages from the conversation history.

    Returns:
        A list of message dictionaries, each containing 'role',
        'content', and 'timestamp' keys.
    """
    logger.debug("Loading conversation history. Total messages: %d.", len(_conversation_history))
    return list(_conversation_history)


def clear_memory() -> None:
    """
    Clear all messages from the conversation history.

    Removes all stored messages, resetting the memory to an empty state.
    """
    message_count: int = len(_conversation_history)
    _conversation_history.clear()
    logger.info("Conversation memory cleared. Removed %d messages.", message_count)
