"""
OpenAI LLM Service

Adapter for OpenAI API (GPT-4, etc.).
"""

from django.conf import settings
from .llm_base import BaseLLMService
import logging

logger = logging.getLogger(__name__)


class OpenAIService(BaseLLMService):
    """LLM service using OpenAI API."""

    def __init__(self, model: str = None, api_key: str = None):
        self.api_key = api_key or getattr(settings, 'OPENAI_API_KEY', '')
        self.model = model or getattr(settings, 'OPENAI_MODEL', 'gpt-4')
        super().__init__(self.model)

        if not self.api_key:
            logger.warning("OpenAI API key not configured")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a response using OpenAI.

        Args:
            system_prompt: System/context prompt
            user_prompt: User's question

        Returns:
            Raw string response from OpenAI
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            )

        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        client = OpenAI(api_key=self.api_key)

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2048
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI error: {str(e)}")
            raise

    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        if not self.api_key:
            return False

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            # Simple test request
            client.models.list()
            return True
        except:
            return False
