"""
LLM Prompt Templates

Contains the prompt templates used for generating SQL queries
and analyzing data from user questions.
"""

# System prompt for SQL generation
SYSTEM_PROMPT = """You are an expert SQL assistant. Your task is to convert natural language questions into SQL queries based on the provided database schema.

IMPORTANT RULES:
1. Only generate SELECT queries unless explicitly asked to modify data
2. Use only the tables and columns provided in the schema
3. Write efficient, optimized queries
4. Use appropriate JOINs when relating tables
5. Always use table aliases for clarity
6. Handle NULL values appropriately
7. Use appropriate aggregation functions when needed
8. Return ONLY valid SQL for the specified database type

DATABASE TYPE: {db_type}

AVAILABLE TABLES AND SCHEMA:
{schema}

USER'S ALLOWED TABLES (only use these):
{allowed_tables}

RESPONSE FORMAT:
You must respond with a JSON object containing:
{{
    "sql": "YOUR SQL QUERY HERE",
    "explanation": "Brief explanation of what the query does",
    "chart_suggestion": {{
        "type": "bar|line|pie|scatter|table|none",
        "x_column": "column name for x-axis (if applicable)",
        "y_column": "column name for y-axis (if applicable)",
        "reason": "Why this chart type is appropriate"
    }}
}}

CHART TYPE GUIDELINES:
- Use "bar" for comparing categories or discrete values
- Use "line" for time series or trends
- Use "pie" for showing proportions of a whole (max 10 slices)
- Use "scatter" for showing correlation between two numeric values
- Use "table" for detailed data or when no visualization makes sense
- Use "none" if the query returns a single value or simple count"""

# User message template
USER_PROMPT = """Question: {question}

Generate a SQL query to answer this question using the schema provided.
Remember to:
1. Only use the allowed tables
2. Return valid {db_type} SQL syntax
3. Include an explanation
4. Suggest an appropriate chart type

Respond with a JSON object as specified."""

# Error correction prompt
ERROR_CORRECTION_PROMPT = """The previous SQL query resulted in an error:
Error: {error}

Previous query:
{previous_sql}

Please fix the query and try again. Make sure to:
1. Check column names are correct
2. Check table names are correct
3. Ensure proper syntax for {db_type}
4. Handle any type mismatches

Respond with a corrected JSON object."""


def build_schema_string(schema: dict, allowed_tables: list = None) -> str:
    """
    Build a formatted string representation of the database schema.

    Args:
        schema: The schema dictionary from schema extractor
        allowed_tables: List of table names the user has access to (None = all)

    Returns:
        Formatted string describing the schema
    """
    if not schema or 'tables' not in schema:
        return "No schema available"

    lines = []
    tables = schema.get('tables', {})

    for table_name, table_info in tables.items():
        # Skip tables not in allowed list
        if allowed_tables and table_name not in allowed_tables:
            continue

        lines.append(f"\nTABLE: {table_name}")
        lines.append("-" * (len(table_name) + 7))

        # Columns
        columns = table_info.get('columns', [])
        if columns:
            lines.append("Columns:")
            for col in columns:
                nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                pk = " [PRIMARY KEY]" if col.get('primary_key') else ""
                lines.append(f"  - {col['name']}: {col['type']} ({nullable}){pk}")

        # Primary keys
        pk_cols = table_info.get('primary_key', [])
        if pk_cols:
            lines.append(f"Primary Key: {', '.join(pk_cols)}")

        # Foreign keys
        fks = table_info.get('foreign_keys', [])
        if fks:
            lines.append("Foreign Keys:")
            for fk in fks:
                lines.append(f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}")

        lines.append("")

    return '\n'.join(lines)


def build_system_prompt(db_type: str, schema: dict, allowed_tables: list) -> str:
    """
    Build the complete system prompt for the LLM.

    Args:
        db_type: Database type (postgresql, mysql, sqlite, etc.)
        schema: Database schema dictionary
        allowed_tables: List of tables the user can access

    Returns:
        Formatted system prompt string
    """
    schema_string = build_schema_string(schema, allowed_tables)
    allowed_string = ', '.join(allowed_tables) if allowed_tables else 'All tables'

    return SYSTEM_PROMPT.format(
        db_type=db_type.upper(),
        schema=schema_string,
        allowed_tables=allowed_string
    )


def build_user_prompt(question: str, db_type: str) -> str:
    """
    Build the user prompt for the LLM.

    Args:
        question: User's natural language question
        db_type: Database type

    Returns:
        Formatted user prompt string
    """
    return USER_PROMPT.format(
        question=question,
        db_type=db_type.upper()
    )


def build_error_correction_prompt(error: str, previous_sql: str, db_type: str) -> str:
    """
    Build a prompt for correcting SQL errors.

    Args:
        error: The error message from the failed query
        previous_sql: The SQL that caused the error
        db_type: Database type

    Returns:
        Formatted error correction prompt
    """
    return ERROR_CORRECTION_PROMPT.format(
        error=error,
        previous_sql=previous_sql,
        db_type=db_type.upper()
    )
