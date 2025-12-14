"""
Database Connector Utility

Provides a unified interface for connecting to different database types:
- PostgreSQL
- MySQL
- SQLite
- MariaDB
- Microsoft SQL Server
"""

from typing import Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """
    A unified database connector that supports multiple database types.
    """

    def __init__(
        self,
        db_type: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: str = '',
        username: Optional[str] = None,
        password: Optional[str] = None,
        file_path: Optional[str] = None
    ):
        self.db_type = db_type.lower()
        self.host = host
        self.port = port or self._default_port()
        self.database = database
        self.username = username
        self.password = password
        self.file_path = file_path
        self.connection = None
        self.cursor = None

    def _default_port(self) -> int:
        """Return default port for database type."""
        ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'mariadb': 3306,
            'mssql': 1433,
            'sqlite': 0,
        }
        return ports.get(self.db_type, 0)

    def connect(self) -> Tuple[bool, str]:
        """
        Establish connection to the database.
        Returns a tuple of (success: bool, message: str)
        """
        try:
            if self.db_type == 'postgresql':
                return self._connect_postgresql()
            elif self.db_type in ('mysql', 'mariadb'):
                return self._connect_mysql()
            elif self.db_type == 'sqlite':
                return self._connect_sqlite()
            elif self.db_type == 'mssql':
                return self._connect_mssql()
            else:
                return False, f"Unsupported database type: {self.db_type}"
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            return False, str(e)

    def _connect_postgresql(self) -> Tuple[bool, str]:
        """Connect to PostgreSQL database."""
        try:
            import psycopg2
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password
            )
            self.cursor = self.connection.cursor()
            return True, "Connected to PostgreSQL successfully"
        except ImportError:
            return False, "psycopg2 package not installed. Run: pip install psycopg2-binary"
        except Exception as e:
            return False, f"PostgreSQL connection error: {str(e)}"

    def _connect_mysql(self) -> Tuple[bool, str]:
        """Connect to MySQL/MariaDB database."""
        try:
            import mysql.connector
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password
            )
            self.cursor = self.connection.cursor(dictionary=True)
            return True, f"Connected to {self.db_type.upper()} successfully"
        except ImportError:
            return False, "mysql-connector-python package not installed. Run: pip install mysql-connector-python"
        except Exception as e:
            return False, f"{self.db_type.upper()} connection error: {str(e)}"

    def _connect_sqlite(self) -> Tuple[bool, str]:
        """Connect to SQLite database."""
        try:
            import sqlite3
            if not self.file_path:
                return False, "SQLite requires a file path"
            self.connection = sqlite3.connect(self.file_path)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            return True, "Connected to SQLite successfully"
        except Exception as e:
            return False, f"SQLite connection error: {str(e)}"

    def _connect_mssql(self) -> Tuple[bool, str]:
        """Connect to Microsoft SQL Server."""
        try:
            import pyodbc
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.host},{self.port};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password}"
            )
            self.connection = pyodbc.connect(connection_string)
            self.cursor = self.connection.cursor()
            return True, "Connected to SQL Server successfully"
        except ImportError:
            return False, "pyodbc package not installed. Run: pip install pyodbc"
        except Exception as e:
            return False, f"SQL Server connection error: {str(e)}"

    def disconnect(self):
        """Close the database connection."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            self.connection = None
            self.cursor = None
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")

    def test_connection(self) -> Tuple[bool, str]:
        """Test the database connection."""
        success, message = self.connect()
        if success:
            self.disconnect()
        return success, message

    def execute_query(self, query: str, params: tuple = None) -> Tuple[bool, Any, str]:
        """
        Execute a query and return results.
        Returns: (success: bool, results: Any, message: str)
        """
        if not self.connection:
            success, msg = self.connect()
            if not success:
                return False, None, msg

        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            # Check if it's a SELECT query or CTE (WITH)
            query_upper = query.strip().upper()
            if query_upper.startswith('SELECT') or query_upper.startswith('WITH'):
                # Normalize results to list[dict] for all db types
                if self.db_type == 'sqlite':
                    rows = self.cursor.fetchall()
                    columns = [desc[0] for desc in self.cursor.description]
                    results = [dict(zip(columns, row)) for row in rows]
                elif self.db_type in ('mysql', 'mariadb'):
                    # mysql.connector with dictionary=True cursor already returns dicts
                    results = self.cursor.fetchall()
                    # If for some reason they're not dicts, convert them
                    if results and not isinstance(results[0], dict):
                        columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
                        results = [dict(zip(columns, row)) for row in results]
                elif self.db_type == 'mssql':
                    columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
                    rows = self.cursor.fetchall()
                    results = [dict(zip(columns, row)) for row in rows]
                else:  # postgresql
                    columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
                    rows = self.cursor.fetchall()
                    results = [dict(zip(columns, row)) for row in rows]
                return True, results, "Query executed successfully"
            else:
                self.connection.commit()
                return True, [], "Query executed successfully"

        except Exception as e:
            if self.connection:
                try:
                    self.connection.rollback()
                except:
                    pass
            return False, None, f"Query execution error: {str(e)}"

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


def get_connector_from_model(db_connection) -> DatabaseConnector:
    """
    Create a DatabaseConnector from a DatabaseConnection model instance.
    """
    return DatabaseConnector(
        db_type=db_connection.db_type,
        host=db_connection.host,
        port=db_connection.port,
        database=db_connection.database_name,
        username=db_connection.username,
        password=db_connection.get_password(),
        file_path=db_connection.file_path
    )
