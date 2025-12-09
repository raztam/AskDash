"""
LLM Service Base Class

Defines the interface for LLM providers and common functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import re
import logging

logger = logging.getLogger(__name__)


class LLMResponse:
    """Structured response from LLM."""

    def __init__(
        self,
        sql: str,
        explanation: str,
        chart_suggestion: Dict[str, Any],
        raw_response: str = ""
    ):
        self.sql = sql
        self.explanation = explanation
        self.chart_suggestion = chart_suggestion
        self.raw_response = raw_response

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sql": self.sql,
            "explanation": self.explanation,
            "chart_suggestion": self.chart_suggestion
        }


class BaseLLMService(ABC):
    """Base class for LLM service providers."""

    def __init__(self, model: str = None):
        self.model = model

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a response from the LLM.

        Args:
            system_prompt: System/context prompt
            user_prompt: User's question/request

        Returns:
            Raw string response from the LLM
        """
        pass

    def generate_sql(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """
        Generate SQL from natural language.

        Args:
            system_prompt: System prompt with schema information
            user_prompt: User's question

        Returns:
            LLMResponse object with parsed SQL and metadata
        """
        raw_response = self.generate(system_prompt, user_prompt)
        return self._parse_response(raw_response)

    def _parse_response(self, response: str) -> LLMResponse:
        """
        Parse the LLM response to extract SQL and metadata.

        Args:
            response: Raw response string from LLM

        Returns:
            LLMResponse object
        """
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)

                return LLMResponse(
                    sql=data.get('sql', ''),
                    explanation=data.get('explanation', ''),
                    chart_suggestion=data.get('chart_suggestion', {
                        'type': 'table',
                        'reason': 'Default table view'
                    }),
                    raw_response=response
                )

            # If no JSON found, try to extract SQL directly
            sql_match = re.search(
                r'```sql\s*([\s\S]*?)\s*```|SELECT[\s\S]*?(?:;|$)',
                response,
                re.IGNORECASE
            )

            sql = sql_match.group(1) if sql_match and sql_match.group(1) else (
                sql_match.group(0) if sql_match else ''
            )

            return LLMResponse(
                sql=sql.strip(),
                explanation="Generated query",
                chart_suggestion={'type': 'table', 'reason': 'Default view'},
                raw_response=response
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Fallback: try to extract SQL
            sql_match = re.search(
                r'```sql\s*([\s\S]*?)\s*```|"sql"\s*:\s*"([^"]*)"',
                response,
                re.IGNORECASE
            )
            sql = ''
            if sql_match:
                sql = sql_match.group(1) or sql_match.group(2) or ''

            return LLMResponse(
                sql=sql.strip(),
                explanation="Generated query (response parsing failed)",
                chart_suggestion={'type': 'table', 'reason': 'Default view'},
                raw_response=response
            )

        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return LLMResponse(
                sql='',
                explanation=f"Error parsing response: {str(e)}",
                chart_suggestion={'type': 'none'},
                raw_response=response
            )

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        pass
