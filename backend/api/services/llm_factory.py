"""
LLM Service Factory

Provides a unified interface to get the configured LLM service.
"""

from django.conf import settings
from .llm_base import BaseLLMService
from .llm_ollama import OllamaService
from .llm_openai import OpenAIService
from .llm_anthropic import AnthropicService
import logging

logger = logging.getLogger(__name__)


def get_llm_service() -> BaseLLMService:
    """
    Get the configured LLM service based on settings.

    Returns:
        An instance of the configured LLM service

    Raises:
        ValueError: If the configured provider is not supported
    """
    provider = getattr(settings, 'LLM_PROVIDER', 'ollama').lower()

    if provider == 'ollama':
        logger.info("Using Ollama LLM service")
        return OllamaService()

    elif provider == 'openai':
        logger.info("Using OpenAI LLM service")
        return OpenAIService()

    elif provider == 'anthropic':
        logger.info("Using Anthropic LLM service")
        return AnthropicService()

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            "Supported providers: ollama, openai, anthropic"
        )


def get_available_providers() -> dict:
    """
    Check which LLM providers are available.

    Returns:
        Dictionary of provider names and their availability status
    """
    providers = {
        'ollama': OllamaService().is_available(),
        'openai': OpenAIService().is_available(),
        'anthropic': AnthropicService().is_available()
    }
    return providers


def get_current_provider_info() -> dict:
    """
    Get information about the current LLM provider.

    Returns:
        Dictionary with provider info
    """
    provider = getattr(settings, 'LLM_PROVIDER', 'ollama').lower()
    service = get_llm_service()

    return {
        'provider': provider,
        'model': service.model,
        'available': service.is_available()
    }
