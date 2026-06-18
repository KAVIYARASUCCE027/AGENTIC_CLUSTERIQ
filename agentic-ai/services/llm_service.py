"""
LLM Service Module.

Provides a singleton Google Gemini LLM instance via LangChain's
ChatGoogleGenerativeAI integration. Handles initialization, error
handling, and logging.
"""

import logging
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    """
    Return a cached singleton instance of the Google Gemini LLM.

    Initializes ChatGoogleGenerativeAI with the configured model name,
    API key, and temperature. Uses lru_cache to ensure only one instance
    is created throughout the application lifecycle.

    Returns:
        ChatGoogleGenerativeAI: The initialized Gemini LLM instance.

    Raises:
        RuntimeError: If the LLM fails to initialize due to missing
                      API key or other configuration issues.
    """
    settings = get_settings()

    if not settings.GOOGLE_API_KEY:
        error_msg = (
            "Cannot initialize Gemini LLM: GOOGLE_API_KEY is not set. "
            "Please configure it in the .env file."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        logger.info("Initializing Gemini LLM with model: %s", settings.MODEL_NAME)

        llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0,
            convert_system_message_to_human=True,
        )

        logger.info("Gemini LLM initialized successfully.")
        return llm

    except Exception as exc:
        error_msg = f"Failed to initialize Gemini LLM: {exc}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from exc
