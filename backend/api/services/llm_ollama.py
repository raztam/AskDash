"""
Ollama LLM Service

Adapter for local Ollama LLM models.
"""

import requests
import json
from django.conf import settings
from .llm_base import BaseLLMService
import logging

logger = logging.getLogger(__name__)


class OllamaService(BaseLLMService):
    """LLM service using local Ollama."""

    def __init__(self, model: str = None, base_url: str = None):
        self.base_url = base_url or getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = model or getattr(settings, 'OLLAMA_MODEL', 'llama3.2')
        super().__init__(self.model)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a response using Ollama.

        Args:
            system_prompt: System/context prompt
            user_prompt: User's question

        Returns:
            Raw string response from Ollama
        """
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for more deterministic SQL
                "num_predict": 2048
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()

            data = response.json()
            return data.get('message', {}).get('content', '')

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama. Is it running?")
            raise ConnectionError(
                "Cannot connect to Ollama. Please ensure Ollama is running at "
                f"{self.base_url}"
            )

        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            raise TimeoutError("Ollama request timed out. Try a simpler query.")

        except Exception as e:
            logger.error(f"Ollama error: {str(e)}")
            raise

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> list:
        """List available Ollama models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except:
            return []
