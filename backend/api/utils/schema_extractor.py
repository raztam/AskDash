"""
Schema Extractor Utility

Extracts database schema information for different database types:
- PostgreSQL
- MySQL
- SQLite
- MariaDB
- Microsoft SQL Server

Schema format:
{
    "tables": {
        "table_name": {
            "columns": [
                {
                    "name": "column_name",
                    "type": "data_type",
                    "nullable": true/false,
                    "primary_key": true/false,
                    "foreign_key": {
                        "references_table": "table",
                        "references_column": "column"
                    } or null
                }
            ],
            "indexes": ["index_name", ...],
            "primary_key": ["column_name", ...]
        }
    }
}
"""

from typing import Dict, Any, List
from .db_connector import DatabaseConnector, get_connector_from_model
import logging

logger = logging.getLogger(__name__)


class SchemaExtractor:
    """Extract schema information from various database types."""

    def __init__(self, connector: DatabaseConnector):
        self.connector = connector
        self.db_type = connector.db_type

    def extract_schema(self) -> Dict[str, Any]:
        """
        Extract the full database schema.
        Returns a dictionary with table information.
        """
        try:
            success, msg = self.connector.connect()
            if not success:
                return {"error": msg, "tables": {}}

            if self.db_type == 'postgresql':
                schema = self._extract_postgresql_schema()
            elif self.db_type in ('mysql', 'mariadb'):
                schema = self._extract_mysql_schema()
            elif self.db_type == 'sqlite':
                schema = self._extract_sqlite_schema()
            elif self.db_type == 'mssql':
                schema = self._extract_mssql_schema()
            else:
                schema = {"error": f"Unsupported database type: {self.db_type}", "tables": {}}

            return schema

        except Exception as e:
            logger.error(f"Schema extraction error: {str(e)}")
            return {"error": str(e), "tables": {}}

        finally:
            self.connector.disconnect()

    def _extract_postgresql_schema(self) -> Dict[str, Any]:
        """Extract schema from PostgreSQL database."""
        schema = {"tables": {}}

        # Get all tables
        tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        success, tables, _ = self.connector.execute_query(tables_query)
        if not success:
            return schema

        for table_row in tables:
            table_name = table_row['table_name']
            schema["tables"][table_name] = {
                "columns": [],
                "indexes": [],
                "primary_key": [],
                "foreign_keys": []
            }

            # Get columns
            columns_query = """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """
            success, columns, _ = self.connector.execute_query(columns_query, (table_name,))
            if success:
                for col in columns:
                    schema["tables"][table_name]["columns"].append({
                        "name": col['column_name'],
                        "type": col['data_type'],
                        "nullable": col['is_nullable'] == 'YES',
                        "default": col['column_default']
                    })

            # Get primary keys
            pk_query = """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = 'public'
                    AND tc.table_name = %s
                    AND tc.constraint_type = 'PRIMARY KEY';
            """
            success, pks, _ = self.connector.execute_query(pk_query, (table_name,))
            if success:
                schema["tables"][table_name]["primary_key"] = [pk['column_name'] for pk in pks]

            # Get foreign keys
            fk_query = """
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                    AND tc.table_name = %s;
            """
            success, fks, _ = self.connector.execute_query(fk_query, (table_name,))
            if success:
                for fk in fks:
                    schema["tables"][table_name]["foreign_keys"].append({
                        "column": fk['column_name'],
                        "references_table": fk['foreign_table_name'],
                        "references_column": fk['foreign_column_name']
                    })

        return schema

    def _extract_mysql_schema(self) -> Dict[str, Any]:
        """Extract schema from MySQL/MariaDB database."""
        schema = {"tables": {}}
        database = self.connector.database

        # Get all tables
        tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        success, tables, _ = self.connector.execute_query(tables_query, (database,))
        if not success:
            return schema

        for table_row in tables:
            table_name = table_row['table_name'] if isinstance(table_row, dict) else table_row[0]
            schema["tables"][table_name] = {
                "columns": [],
                "indexes": [],
                "primary_key": [],
                "foreign_keys": []
            }

            # Get columns
            columns_query = """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_key,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
            """
            success, columns, _ = self.connector.execute_query(columns_query, (database, table_name))
            if success:
                for col in columns:
                    col_dict = col if isinstance(col, dict) else {
                        'column_name': col[0], 'data_type': col[1],
                        'is_nullable': col[2], 'column_key': col[3], 'column_default': col[4]
                    }
                    schema["tables"][table_name]["columns"].append({
                        "name": col_dict['column_name'],
                        "type": col_dict['data_type'],
                        "nullable": col_dict['is_nullable'] == 'YES',
                        "primary_key": col_dict['column_key'] == 'PRI',
                        "default": col_dict['column_default']
                    })
                    if col_dict['column_key'] == 'PRI':
                        schema["tables"][table_name]["primary_key"].append(col_dict['column_name'])

            # Get foreign keys
            fk_query = """
                SELECT
                    column_name,
                    referenced_table_name,
                    referenced_column_name
                FROM information_schema.key_column_usage
                WHERE table_schema = %s
                    AND table_name = %s
                    AND referenced_table_name IS NOT NULL;
            """
            success, fks, _ = self.connector.execute_query(fk_query, (database, table_name))
            if success:
                for fk in fks:
                    fk_dict = fk if isinstance(fk, dict) else {
                        'column_name': fk[0],
                        'referenced_table_name': fk[1],
                        'referenced_column_name': fk[2]
                    }
                    schema["tables"][table_name]["foreign_keys"].append({
                        "column": fk_dict['column_name'],
                        "references_table": fk_dict['referenced_table_name'],
                        "references_column": fk_dict['referenced_column_name']
                    })

        return schema

    def _extract_sqlite_schema(self) -> Dict[str, Any]:
        """Extract schema from SQLite database."""
        schema = {"tables": {}}

        # Get all tables
        tables_query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """
        success, tables, _ = self.connector.execute_query(tables_query)
        if not success:
            return schema

        for table_row in tables:
            table_name = table_row['name'] if isinstance(table_row, dict) else table_row[0]
            schema["tables"][table_name] = {
                "columns": [],
                "indexes": [],
                "primary_key": [],
                "foreign_keys": []
            }

            # Get columns using PRAGMA
            columns_query = f"PRAGMA table_info('{table_name}');"
            success, columns, _ = self.connector.execute_query(columns_query)
            if success:
                for col in columns:
                    col_dict = col if isinstance(col, dict) else {
                        'cid': col[0], 'name': col[1], 'type': col[2],
                        'notnull': col[3], 'dflt_value': col[4], 'pk': col[5]
                    }
                    schema["tables"][table_name]["columns"].append({
                        "name": col_dict['name'],
                        "type": col_dict['type'],
                        "nullable": not col_dict['notnull'],
                        "primary_key": bool(col_dict['pk']),
                        "default": col_dict['dflt_value']
                    })
                    if col_dict['pk']:
                        schema["tables"][table_name]["primary_key"].append(col_dict['name'])

            # Get foreign keys using PRAGMA
            fk_query = f"PRAGMA foreign_key_list('{table_name}');"
            success, fks, _ = self.connector.execute_query(fk_query)
            if success:
                for fk in fks:
                    fk_dict = fk if isinstance(fk, dict) else {
                        'id': fk[0], 'seq': fk[1], 'table': fk[2],
                        'from': fk[3], 'to': fk[4]
                    }
                    schema["tables"][table_name]["foreign_keys"].append({
                        "column": fk_dict['from'],
                        "references_table": fk_dict['table'],
                        "references_column": fk_dict['to']
                    })

            # Get indexes
            index_query = f"PRAGMA index_list('{table_name}');"
            success, indexes, _ = self.connector.execute_query(index_query)
            if success:
                for idx in indexes:
                    idx_name = idx['name'] if isinstance(idx, dict) else idx[1]
                    schema["tables"][table_name]["indexes"].append(idx_name)

        return schema

    def _extract_mssql_schema(self) -> Dict[str, Any]:
        """Extract schema from Microsoft SQL Server database."""
        schema = {"tables": {}}

        # Get all tables
        tables_query = """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME;
        """
        success, tables, _ = self.connector.execute_query(tables_query)
        if not success:
            return schema

        for table_row in tables:
            table_name = table_row['TABLE_NAME'] if isinstance(table_row, dict) else table_row[0]
            schema["tables"][table_name] = {
                "columns": [],
                "indexes": [],
                "primary_key": [],
                "foreign_keys": []
            }

            # Get columns
            columns_query = """
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION;
            """
            success, columns, _ = self.connector.execute_query(columns_query, (table_name,))
            if success:
                for col in columns:
                    col_dict = col if isinstance(col, dict) else {
                        'COLUMN_NAME': col[0], 'DATA_TYPE': col[1],
                        'IS_NULLABLE': col[2], 'COLUMN_DEFAULT': col[3]
                    }
                    schema["tables"][table_name]["columns"].append({
                        "name": col_dict['COLUMN_NAME'],
                        "type": col_dict['DATA_TYPE'],
                        "nullable": col_dict['IS_NULLABLE'] == 'YES',
                        "default": col_dict['COLUMN_DEFAULT']
                    })

            # Get primary keys
            pk_query = """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
                AND TABLE_NAME = ?;
            """
            success, pks, _ = self.connector.execute_query(pk_query, (table_name,))
            if success:
                for pk in pks:
                    pk_name = pk['COLUMN_NAME'] if isinstance(pk, dict) else pk[0]
                    schema["tables"][table_name]["primary_key"].append(pk_name)

            # Get foreign keys
            fk_query = """
                SELECT
                    COL_NAME(fc.parent_object_id, fc.parent_column_id) AS column_name,
                    OBJECT_NAME(fc.referenced_object_id) AS referenced_table,
                    COL_NAME(fc.referenced_object_id, fc.referenced_column_id) AS referenced_column
                FROM sys.foreign_key_columns fc
                WHERE OBJECT_NAME(fc.parent_object_id) = ?;
            """
            success, fks, _ = self.connector.execute_query(fk_query, (table_name,))
            if success:
                for fk in fks:
                    fk_dict = fk if isinstance(fk, dict) else {
                        'column_name': fk[0],
                        'referenced_table': fk[1],
                        'referenced_column': fk[2]
                    }
                    schema["tables"][table_name]["foreign_keys"].append({
                        "column": fk_dict['column_name'],
                        "references_table": fk_dict['referenced_table'],
                        "references_column": fk_dict['referenced_column']
                    })

        return schema


def extract_schema_from_connection(db_connection) -> Dict[str, Any]:
    """
    Extract schema from a DatabaseConnection model instance.
    """
    connector = get_connector_from_model(db_connection)
    extractor = SchemaExtractor(connector)
    return extractor.extract_schema()
