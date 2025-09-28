import openai
from typing import Dict, Any, List
from app.core.config import settings
import json
import logging
import re

logger = logging.getLogger(__name__)

class AIQueryService:
    def __init__(self):
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client based on AI provider configuration"""
        try:
            if settings.ai_provider == "lmstudio":
                # Configure for LM Studio
                client = openai.OpenAI(
                    base_url=settings.lm_studio_base_url,
                    api_key=settings.lm_studio_api_key  # LM Studio doesn't validate this
                )
                logger.info(f"Initialized LM Studio client with base URL: {settings.lm_studio_base_url}")
                return client
            
            elif settings.ai_provider == "openai-compatible":
                # Configure for other OpenAI-compatible APIs
                if not settings.openai_base_url:
                    raise ValueError("openai_base_url must be set when using openai-compatible provider")
                
                client = openai.OpenAI(
                    base_url=settings.openai_base_url,
                    api_key=settings.openai_api_key or "not-needed"
                )
                logger.info(f"Initialized OpenAI-compatible client with base URL: {settings.openai_base_url}")
                return client
            
            else:  # Default to OpenAI
                if not settings.openai_api_key:
                    raise ValueError("OpenAI API key is required when using openai provider")
                
                client = openai.OpenAI(api_key=settings.openai_api_key)
                logger.info("Initialized OpenAI client")
                return client
                
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            raise
    
    def _get_model_name(self) -> str:
        """Get the appropriate model name based on provider"""
        if settings.ai_provider == "lmstudio":
            return settings.lm_studio_model
        elif settings.ai_provider == "openai-compatible":
            return settings.ai_model
        else:
            return "gpt-3.5-turbo"
    
    def generate_sql(self, natural_query: str, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Convert natural language query to SQL"""
        try:
            # Create a detailed schema description
            schema_description = self._create_schema_description(schema_info)
            
            # Create the prompt
            prompt = f"""
You are an expert SQL query generator. Convert the following natural language query into a SQL SELECT statement.

Database Schema:
{schema_description}

Natural Language Query: "{natural_query}"

Rules:
1. Only generate SELECT statements
2. Use proper SQL syntax for {schema_info.get('database_type', 'generic')} database
3. Include appropriate JOINs when needed
4. Use aggregate functions when appropriate
5. Add proper WHERE clauses for filtering - be very careful to match the user's intent
6. Order results logically
7. Limit results to reasonable amounts (use LIMIT/TOP)
8. Pay close attention to the exact filtering requirements in the natural language query

Return ONLY a JSON object with these fields:
{{
    "sql": "the generated SQL query",
    "explanation": "brief explanation of what the query does",
    "visualization_hint": "suggest the best visualization type (table, bar_chart, line_chart, pie_chart, kpi)",
    "confidence": 0.95
}}

Do not include any text before or after the JSON object.
"""

            # Get the appropriate model name
            model_name = self._get_model_name()
            
            # Call the AI API using the configured client
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are an expert SQL query generator. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.ai_temperature,
                max_tokens=settings.ai_max_tokens
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Remove code block markers if present
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                
                # Try to find JSON object in the response
                import re
                # Use DOTALL flag to match across newlines
                json_match = re.search(r'\{.*?\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                else:
                    # Fallback: try parsing the whole content
                    result = json.loads(content.strip())
                
                # Validate required fields
                if not all(key in result for key in ['sql', 'explanation', 'visualization_hint']):
                    raise ValueError("Missing required fields in AI response")
                
                # Add confidence if not present (some local models might not include it)
                if 'confidence' not in result:
                    result['confidence'] = 0.8
                
                logger.info(f"Successfully generated SQL using {settings.ai_provider} provider")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {content}")
                # Fallback: extract SQL from response
                sql_lines = [line for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
                sql = ' '.join(sql_lines)
                
                return {
                    "sql": sql,
                    "explanation": "Generated SQL query from natural language",
                    "visualization_hint": "table",
                    "confidence": 0.7
                }
                
        except Exception as e:
            logger.error(f"AI query generation failed with {settings.ai_provider} provider: {e}")
            
            # Provide helpful error messages for common local AI issues
            error_msg = str(e)
            if "Connection" in error_msg or "timeout" in error_msg.lower():
                raise Exception(f"Failed to connect to {settings.ai_provider}. Make sure your AI server is running at {getattr(settings, f'{settings.ai_provider}_base_url', 'the configured URL')}")
            elif "model" in error_msg.lower() and settings.ai_provider == "lmstudio":
                raise Exception(f"Model '{settings.lm_studio_model}' not found in LM Studio. Please load a model in LM Studio first.")
            else:
                raise Exception(f"Failed to generate SQL using {settings.ai_provider}: {str(e)}")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the AI service"""
        try:
            model_name = self._get_model_name()
            
            # Simple test prompt
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello' if you can understand this."}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            content = response.choices[0].message.content.strip()
            
            return {
                "status": "success",
                "provider": settings.ai_provider,
                "model": model_name,
                "base_url": getattr(settings, f'{settings.ai_provider}_base_url', 'default'),
                "response": content,
                "message": f"Successfully connected to {settings.ai_provider}"
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # Provide specific error messages for common issues
            if "Connection" in error_msg or "timeout" in error_msg.lower():
                message = f"Cannot connect to {settings.ai_provider} at {getattr(settings, f'{settings.ai_provider}_base_url', 'configured URL')}. Make sure the server is running."
            elif "model" in error_msg.lower() and settings.ai_provider == "lmstudio":
                message = f"Model '{settings.lm_studio_model}' not found. Please load a compatible model in LM Studio."
            elif "api" in error_msg.lower() and "key" in error_msg.lower():
                message = f"API key issue with {settings.ai_provider}. Check your configuration."
            else:
                message = f"Failed to connect to {settings.ai_provider}: {error_msg}"
            
            return {
                "status": "error",
                "provider": settings.ai_provider,
                "model": self._get_model_name(),
                "error": error_msg,
                "message": message
            }

    def _create_schema_description(self, schema_info: Dict[str, Any]) -> str:
        """Create a human-readable schema description"""
        description_parts = []
        
        for table_name, table_info in schema_info.get("tables", {}).items():
            columns_desc = []
            for col in table_info.get("columns", []):
                col_desc = f"{col['name']} ({col['type']}"
                if col.get('primary_key'):
                    col_desc += ", PRIMARY KEY"
                if not col.get('nullable', True):
                    col_desc += ", NOT NULL"
                col_desc += ")"
                columns_desc.append(col_desc)
            
            table_desc = f"Table: {table_name}\nColumns: {', '.join(columns_desc)}"
            
            # Add foreign key information
            fks = table_info.get("foreign_keys", [])
            if fks:
                fk_descs = []
                for fk in fks:
                    fk_desc = f"{fk.get('constrained_columns', [])} -> {fk.get('referred_table', '')}.{fk.get('referred_columns', [])}"
                    fk_descs.append(fk_desc)
                table_desc += f"\nForeign Keys: {', '.join(fk_descs)}"
            
            description_parts.append(table_desc)
        
        return "\n\n".join(description_parts)
    
    def suggest_visualization(self, data: List[Dict[str, Any]], columns: List[str]) -> str:
        """Suggest the best visualization type based on data"""
        if not data or not columns:
            return "table"
        
        # Single value - KPI
        if len(data) == 1 and len(columns) == 1:
            return "kpi"
        
        # Time series detection
        time_columns = [col for col in columns if any(time_word in col.lower() for time_word in ['date', 'time', 'created', 'updated'])]
        if time_columns and len(data) > 1:
            return "line_chart"
        
        # Categorical data with counts
        if len(columns) == 2 and len(data) <= 20:
            # Check if one column looks like a count/sum
            numeric_cols = []
            for row in data[:3]:  # Check first few rows
                for col, value in row.items():
                    if isinstance(value, (int, float)) and col not in numeric_cols:
                        numeric_cols.append(col)
            
            if numeric_cols:
                return "bar_chart" if len(data) > 5 else "pie_chart"
        
        # Default to table for complex data
        return "table"

# Global instance
ai_service = AIQueryService()