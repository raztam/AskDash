"""
LLM Prompt Templates

Contains the prompt templates used for generating SQL queries
and analyzing data from user questions.
"""

# System prompt for SQL generation
SYSTEM_PROMPT = r"""You are an expert SQL assistant. Your task is to convert natural language questions into SQL queries based on the provided database schema.

IMPORTANT RULES:
1. Only generate SELECT queries unless explicitly asked to modify data
2. Use only the tables and columns provided in the schema
3. Write efficient, optimized queries
4. Use appropriate JOINs when relating tables
5. Always use table aliases for clarity
6. Handle NULL values appropriately
7. Use appropriate aggregation functions when needed
8. Return ONLY valid SQL for the specified database type
9. CRITICAL: Generate SQL as a single continuous line or use proper SQL formatting
10. NEVER use backslashes (\) for line continuation in SQL
11. DO NOT include duplicate SELECT keywords in the same query
12. Ensure the SQL can be executed directly without any preprocessing

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
    "insights": "Key insights and analysis from the data (e.g., 'The most profitable region is North America with sales of $42,500 and a market share of 38%')",
    "chart_suggestion": {{
        "type": "bar|line|pie|scatter|venn|table|none",
        "x_column": "column name for x-axis (if applicable)",
        "y_column": "column name for y-axis (if applicable)",
        "reason": "Why this chart type is appropriate",
        "sets": [
            {{"sets": ["SetA"], "size": 100}},
            {{"sets": ["SetB"], "size": 80}},
            {{"sets": ["SetA", "SetB"], "size": 30}}
        ]
    }}
}}

INSIGHTS GUIDELINES:
- Provide actionable insights from the query results
- Highlight the most important findings (top performers, trends, anomalies)
- Use specific numbers and percentages when possible
- Compare values when relevant (e.g., "X is 25% higher than Y")
- Keep insights concise but meaningful (1-3 sentences)
- Format insights in a natural, conversational way
- Focus on what the data reveals, not just what it shows

CHART TYPE GUIDELINES:
- Use "bar" for comparing categories or discrete values
- Use "line" for time series or trends
- Use "pie" for showing proportions of a whole (max 10 slices)
- Use "scatter" for showing correlation between two numeric values
- Use "venn" for showing overlaps/intersections between 2-3 groups (e.g., "customers who bought both X and Y", "users in multiple categories")
- Use "table" for detailed data or when no visualization makes sense
- Use "none" if the query returns a single value or simple count

IMPORTANT: For chart columns, prefer descriptive columns (names, labels, dates) over ID columns. Do not use ID columns for chart axes."""

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

# === MULTI-STEP QUERY ANALYSIS PROMPTS ===

# Phase 1: Planning - Analyze the question and determine data needs
PLANNING_PROMPT = r"""You are an expert data analyst. Your task is to analyze a user's question and create a plan for what data needs to be gathered to answer it.

DATABASE TYPE: {db_type}

AVAILABLE TABLES AND SCHEMA:
{schema}

USER'S ALLOWED TABLES (only use these):
{allowed_tables}

USER'S QUESTION:
{question}

ANALYZE THE QUESTION AND CREATE A DATA GATHERING PLAN:
1. What is the user really asking for?
2. What specific data points are needed to answer this question?
3. What tables and relationships are involved?
4. Are there any time ranges, filters, or aggregations needed?
5. Will this require multiple queries or can it be done in one?

IMPORTANT GUIDELINES:
- You can plan for 1-5 SQL queries (recommend using multiple queries for complex questions)
- Each query should have a clear, specific purpose
- Think about whether you need to gather reference data first, then use it for calculations
- Consider if you need to check data existence before proceeding
- Plan queries that can be combined to answer the question

RESPONSE FORMAT:
Respond with a JSON object:
{{
    "understanding": "What the user is asking for in simple terms",
    "data_needs": ["List of specific data points needed"],
    "query_plan": [
        {{
            "query_number": 1,
            "purpose": "What this query will fetch",
            "tables": ["tables involved"],
            "description": "Brief description of what to SELECT"
        }}
    ],
    "complexity": "simple|moderate|complex"
}}

Be concise but thorough in your analysis."""

# Phase 2: Query Generation - Create SQL queries based on the plan
QUERY_GENERATION_PROMPT = r"""You are an expert SQL developer. Based on the analysis plan, generate the specific SQL queries needed to gather the data.

DATABASE TYPE: {db_type}

AVAILABLE TABLES AND SCHEMA:
{schema}

USER'S ALLOWED TABLES:
{allowed_tables}

DATA GATHERING PLAN:
{plan}

GENERATE SQL QUERIES:
Create the SQL queries outlined in the plan. Follow these rules:
1. Generate ONLY SELECT queries
2. Write efficient, optimized queries
3. Use table aliases for clarity
4. Handle NULL values appropriately
5. Generate SQL as a single continuous line or use proper SQL formatting
6. NEVER use backslashes (\) for line continuation
7. DO NOT include duplicate SELECT keywords
8. Each query should be executable independently
9. MAXIMUM 5 QUERIES ALLOWED

QUERY LIMIT: You must generate between 1 and 5 queries. If the plan suggests more, consolidate them.

RESPONSE FORMAT:
Respond with a JSON object:
{{
    "queries": [
        {{
            "query_id": "query_1",
            "sql": "SELECT ... FROM ... WHERE ...",
            "purpose": "What this query fetches",
            "expected_columns": ["col1", "col2"]
        }}
    ],
    "execution_notes": "Any notes about query execution order or dependencies"
}}

Ensure all SQL is valid and can be executed directly."""

# Phase 3: Analysis - Analyze results and generate the final answer
ANALYSIS_PROMPT = r"""You are an expert data analyst. You have executed SQL queries and now have the results. Your task is to analyze this data and provide a comprehensive answer to the user's question.

USER'S ORIGINAL QUESTION:
{question}

QUERY RESULTS:
{results}

DATA SUMMARY:
- Total queries executed: {query_count}
- Queries returned data: {non_empty_count}
- Total rows across all queries: {total_rows}

YOUR TASKS:
1. Analyze the data to answer the user's question
2. Identify key insights, trends, patterns, or anomalies
3. Handle empty results gracefully (if no data, explain that no data was found for the requested criteria)
4. Generate a representative SQL query that summarizes what was done (for display purposes only)
5. Suggest an appropriate chart visualization based on the actual data structure

EMPTY DATA HANDLING:
If all queries returned no data (Total rows = 0):
- Set chart_suggestion type to "none"
- Provide a friendly message like "No data was found for [specific criteria, e.g., 'last year', 'that category']"
- Still generate a representative SQL query showing what was attempted
- Keep the explanation brief and clear

REPRESENTATIVE QUERY:
Generate a single SQL query that represents the analysis performed. This is for display purposes to show the user what was queried. It should be:
- A valid SQL query that captures the essence of the data gathering
- Simplified if multiple queries were used (show the main query or a summary query)
- User-friendly and easy to understand

RESPONSE FORMAT:
Respond with a JSON object:
{{
    "answer": "Direct answer to the user's question in natural language",
    "explanation": "Brief explanation of the findings (1-2 sentences)",
    "insights": "Key insights with specific numbers, percentages, comparisons (1-3 sentences)",
    "representative_sql": "A single SQL query that represents what was done",
    "chart_suggestion": {{
        "type": "bar|line|pie|scatter|venn|table|none",
        "x_column": "column name for x-axis (if applicable)",
        "y_column": "column name for y-axis (if applicable)",
        "reason": "Why this chart type is appropriate for THIS specific data",
        "sets": [
            {{"sets": ["SetA"], "size": 100}},
            {{"sets": ["SetB"], "size": 80}},
            {{"sets": ["SetA", "SetB"], "size": 30}}
        ]
    }},
    "data_summary": "Brief summary of what data was found"
}}

CHART TYPE GUIDELINES (based on actual data):
- "bar": Comparing categories or discrete values
- "line": Time series or trends over time
- "pie": Proportions of a whole (max 10 slices, data must sum to meaningful total)
- "scatter": Correlation between two numeric values
- "venn": Overlaps/intersections between 2-3 groups
- "table": Detailed data, multiple columns, or no clear visualization
- "none": Single value, count, or NO DATA FOUND

IMPORTANT:
- Use descriptive column names (not IDs) for chart axes
- Base chart suggestion on the ACTUAL data structure returned
- If no data found, use type "none"
- Be specific and accurate in your insights"""


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


def build_planning_prompt(question: str, db_type: str, schema: dict, allowed_tables: list) -> str:
    """
    Build the planning prompt for Phase 1 of multi-step analysis.

    Args:
        question: User's natural language question
        db_type: Database type
        schema: Database schema dictionary
        allowed_tables: List of tables the user can access

    Returns:
        Formatted planning prompt string
    """
    schema_string = build_schema_string(schema, allowed_tables)
    allowed_string = ', '.join(allowed_tables) if allowed_tables else 'All tables'

    return PLANNING_PROMPT.format(
        db_type=db_type.upper(),
        schema=schema_string,
        allowed_tables=allowed_string,
        question=question
    )


def build_query_generation_prompt(plan: str, db_type: str, schema: dict, allowed_tables: list) -> str:
    """
    Build the query generation prompt for Phase 2 of multi-step analysis.

    Args:
        plan: The JSON plan from Phase 1
        db_type: Database type
        schema: Database schema dictionary
        allowed_tables: List of tables the user can access

    Returns:
        Formatted query generation prompt string
    """
    schema_string = build_schema_string(schema, allowed_tables)
    allowed_string = ', '.join(allowed_tables) if allowed_tables else 'All tables'

    return QUERY_GENERATION_PROMPT.format(
        db_type=db_type.upper(),
        schema=schema_string,
        allowed_tables=allowed_string,
        plan=plan
    )


def build_analysis_prompt(question: str, results: str, query_count: int,
                          non_empty_count: int, total_rows: int) -> str:
    """
    Build the analysis prompt for Phase 3 of multi-step analysis.

    Args:
        question: User's original question
        results: JSON string of query results
        query_count: Total number of queries executed
        non_empty_count: Number of queries that returned data
        total_rows: Total rows across all results

    Returns:
        Formatted analysis prompt string
    """
    return ANALYSIS_PROMPT.format(
        question=question,
        results=results,
        query_count=query_count,
        non_empty_count=non_empty_count,
        total_rows=total_rows
    )
