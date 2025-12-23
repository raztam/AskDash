"""
Safe SQL Executor

Executes SQL queries with safety checks:
- Validates query type (SELECT only for read permissions)
- Limits result set size
- Timeout handling
- Sanitization checks
"""

import re
from typing import Tuple, List, Dict, Any, Optional
from .db_connector import DatabaseConnector, get_connector_from_model
import logging

logger = logging.getLogger(__name__)

# Maximum number of rows to return
MAX_ROWS = 1000

# Dangerous keywords that should be blocked for read-only users
WRITE_KEYWORDS = [
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
    'TRUNCATE', 'EXEC', 'EXECUTE', 'GRANT', 'REVOKE'
]

# Keywords that indicate a SELECT statement
SELECT_KEYWORDS = ['SELECT', 'WITH']


class SafeSQLExecutor:
    """
    Executes SQL queries with safety validations.
    """

    def __init__(self, connector: DatabaseConnector, permission_level: str = 'read'):
        self.connector = connector
        self.permission_level = permission_level

    def validate_query(self, query: str) -> Tuple[bool, str]:
        """
        Validate the SQL query for safety.
        Returns: (is_valid, error_message)
        """
        # Remove comments and normalize whitespace
        cleaned_query = self._clean_query(query)

        # Check for empty query
        if not cleaned_query.strip():
            return False, "Empty query"

        # Get the first keyword
        first_keyword = cleaned_query.split()[0].upper()

        # For read-only permission, only allow SELECT statements
        if self.permission_level == 'read':
            if first_keyword not in SELECT_KEYWORDS:
                return False, "Read-only permission: Only SELECT queries are allowed"

            # Check for write keywords anywhere in the query
            for keyword in WRITE_KEYWORDS:
                if re.search(rf'\b{keyword}\b', cleaned_query, re.IGNORECASE):
                    return False, f"Read-only permission: {keyword} operations are not allowed"

        # For write permission, block dangerous operations
        elif self.permission_level == 'write':
            dangerous_ops = ['DROP', 'TRUNCATE', 'GRANT', 'REVOKE', 'ALTER']
            for keyword in dangerous_ops:
                if re.search(rf'\b{keyword}\b', cleaned_query, re.IGNORECASE):
                    return False, f"Write permission: {keyword} operations are not allowed"

        # Check for multiple statements (prevent SQL injection via multiple queries)
        statements = self._split_statements(cleaned_query)
        if len(statements) > 1:
            return False, "Multiple SQL statements are not allowed"

        return True, ""

    def _clean_query(self, query: str) -> str:
        """Remove comments and normalize whitespace."""
        # Remove single-line comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        # Remove multi-line comments
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        # Normalize whitespace
        query = ' '.join(query.split())
        return query.strip()

    def _split_statements(self, query: str) -> List[str]:
        """Split query into individual statements."""
        # Simple split by semicolon (not inside quotes)
        statements = []
        current = []
        in_string = False
        string_char = None

        for char in query:
            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
                string_char = None
            elif char == ';' and not in_string:
                stmt = ''.join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
                continue
            current.append(char)

        # Add the last statement
        stmt = ''.join(current).strip()
        if stmt:
            statements.append(stmt)

        return statements

    def add_limit(self, query: str) -> str:
        """Add LIMIT clause if not present."""
        cleaned = self._clean_query(query)
        upper_query = cleaned.upper()

        # Check if LIMIT already exists
        if 'LIMIT' in upper_query:
            return query

        # Check if it's a SELECT query
        if not upper_query.startswith('SELECT') and not upper_query.startswith('WITH'):
            return query

        # Add LIMIT based on database type
        db_type = self.connector.db_type

        if db_type in ('postgresql', 'mysql', 'mariadb', 'sqlite'):
            return f"{query.rstrip(';')} LIMIT {MAX_ROWS}"
        elif db_type == 'mssql':
            # For SQL Server, use TOP
            if 'TOP' not in upper_query:
                # Insert TOP after SELECT
                return re.sub(
                    r'\bSELECT\b',
                    f'SELECT TOP {MAX_ROWS}',
                    query,
                    count=1,
                    flags=re.IGNORECASE
                )

        return query

    def execute(
        self,
        query: str,
        add_limit: bool = True
    ) -> Tuple[bool, Optional[List[Dict[str, Any]]], str]:
        """
        Execute a SQL query safely.

        Args:
            query: The SQL query to execute
            add_limit: Whether to add a LIMIT clause

        Returns:
            (success, results, message)
        """
        # Validate the query
        is_valid, error_msg = self.validate_query(query)
        if not is_valid:
            return False, None, error_msg

        # Add limit if needed
        if add_limit:
            query = self.add_limit(query)

        try:
            # Execute the query
            success, results, message = self.connector.execute_query(query)

            if success and results is not None:
                # Convert any non-serializable types
                results = self._serialize_results(results)

            return success, results, message

        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            return False, None, f"Execution error: {str(e)}"

    def execute_multiple_queries(
        self,
        queries: List[Dict[str, Any]],
        max_queries: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple SQL queries with safety checks.

        Args:
            queries: List of query dicts with 'query_id', 'sql', 'purpose'
            max_queries: Maximum number of queries allowed (default 5)

        Returns:
            List of result dicts with query_id, results, success, error
        """
        if len(queries) > max_queries:
            raise ValueError(f"Too many queries: {len(queries)} exceeds maximum of {max_queries}")

        results = []

        for query_info in queries:
            query_id = query_info.get('query_id', f"query_{len(results) + 1}")
            sql = query_info.get('sql', '')
            purpose = query_info.get('purpose', '')

            if not sql:
                results.append({
                    'query_id': query_id,
                    'sql': '',
                    'purpose': purpose,
                    'results': [],
                    'row_count': 0,
                    'success': False,
                    'error': 'Empty SQL query'
                })
                continue

            # Execute the query
            success, query_results, message = self.execute(sql, add_limit=True)

            if success:
                results.append({
                    'query_id': query_id,
                    'sql': sql,
                    'purpose': purpose,
                    'results': query_results or [],
                    'row_count': len(query_results) if query_results else 0,
                    'success': True
                })
            else:
                results.append({
                    'query_id': query_id,
                    'sql': sql,
                    'purpose': purpose,
                    'results': [],
                    'row_count': 0,
                    'success': False,
                    'error': message
                })

        return results

    def _serialize_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert results to JSON-serializable format."""
        import decimal
        from datetime import datetime, date, time

        serialized = []
        for row in results:
            new_row = {}
            for key, value in row.items():
                if isinstance(value, decimal.Decimal):
                    new_row[key] = float(value)
                elif isinstance(value, datetime):
                    new_row[key] = value.isoformat()
                elif isinstance(value, date):
                    new_row[key] = value.isoformat()
                elif isinstance(value, time):
                    new_row[key] = value.isoformat()
                elif isinstance(value, bytes):
                    new_row[key] = value.decode('utf-8', errors='replace')
                else:
                    new_row[key] = value
            serialized.append(new_row)

        return serialized


def execute_query_safely(
    db_connection,
    query: str,
    permission_level: str = 'read',
    add_limit: bool = True
) -> Tuple[bool, Optional[List[Dict[str, Any]]], str]:
    """
    Execute a query safely using a DatabaseConnection model instance.

    Args:
        db_connection: DatabaseConnection model instance
        query: SQL query to execute
        permission_level: 'read', 'write', or 'admin'
        add_limit: Whether to add LIMIT clause

    Returns:
        (success, results, message)
    """
    connector = get_connector_from_model(db_connection)

    try:
        executor = SafeSQLExecutor(connector, permission_level)
        return executor.execute(query, add_limit)
    finally:
        connector.disconnect()
