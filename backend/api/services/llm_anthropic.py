"""
Anthropic LLM Service

Adapter for Anthropic API (Claude).
"""

from django.conf import settings
from .llm_base import BaseLLMService
import logging

logger = logging.getLogger(__name__)


class AnthropicService(BaseLLMService):
    """LLM service using Anthropic API (Claude)."""

    def __init__(self, model: str = None, api_key: str = None):
        self.api_key = api_key or getattr(settings, 'ANTHROPIC_API_KEY', '')
        self.model = model or getattr(settings, 'ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        super().__init__(self.model)

        if not self.api_key:
            logger.warning("Anthropic API key not configured")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a response using Anthropic Claude.

        Args:
            system_prompt: System/context prompt
            user_prompt: User's question

        Returns:
            Raw string response from Anthropic
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )

        if not self.api_key:
            raise ValueError("Anthropic API key not configured")

        client = anthropic.Anthropic(api_key=self.api_key)

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract text from response
            if message.content and len(message.content) > 0:
                return message.content[0].text
            return ""

        except Exception as e:
            logger.error(f"Anthropic error: {str(e)}")
            raise

    def is_available(self) -> bool:
        """Check if Anthropic API is available."""
        if not self.api_key:
            return False

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            # Test with a minimal request - just check if client can be created
            return True
        except:
            return False
