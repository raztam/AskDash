from sqlalchemy import create_engine, MetaData, Table, inspect, text
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DatabaseType(str, Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MARIADB = "mariadb"
    SQLITE = "sqlite"

class DatabaseConnection:
    def __init__(self, connection_string: str, db_type: DatabaseType):
        self.connection_string = connection_string
        self.db_type = db_type
        self.engine = None
        self.metadata = None
        self._session_factory = None
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            # Create engine with read-only configuration
            connect_args = {}
            if self.db_type == DatabaseType.SQLITE:
                connect_args = {"check_same_thread": False}
            
            self.engine = create_engine(
                self.connection_string,
                connect_args=connect_args,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections every hour
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.metadata = MetaData()
            self._session_factory = sessionmaker(bind=self.engine)
            
            logger.info(f"Successfully connected to {self.db_type} database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def get_session(self):
        """Get database session"""
        if not self._session_factory:
            raise Exception("Database not connected")
        return self._session_factory()
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a read-only SQL query"""
        try:
            # Basic security check - only allow SELECT statements
            # Remove extra whitespace and newlines, then check
            query_cleaned = ' '.join(query.strip().split()).upper()
            if not query_cleaned.startswith('SELECT'):
                raise Exception("Only SELECT queries are allowed")
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                columns = result.keys()
                rows = result.fetchall()
                
                # Convert to list of dictionaries
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise Exception(f"Query execution failed: {str(e)}")
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            inspector = inspect(self.engine)
            schema_info = {
                "tables": {},
                "database_type": self.db_type.value
            }
            
            # Get all table names
            table_names = inspector.get_table_names()
            
            for table_name in table_names:
                # Get columns for each table
                columns = inspector.get_columns(table_name)
                
                # Get foreign keys
                foreign_keys = inspector.get_foreign_keys(table_name)
                
                # Get indexes
                indexes = inspector.get_indexes(table_name)
                
                schema_info["tables"][table_name] = {
                    "columns": [
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                            "nullable": col["nullable"],
                            "default": col.get("default"),
                            "primary_key": col.get("primary_key", False)
                        }
                        for col in columns
                    ],
                    "foreign_keys": foreign_keys,
                    "indexes": indexes
                }
            
            logger.info(f"Retrieved schema for {len(table_names)} tables")
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            raise Exception(f"Failed to get schema info: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test if connection is still valid"""
        try:
            if not self.engine:
                return False
                
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.metadata = None
            self._session_factory = None

# Global connection manager
class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, DatabaseConnection] = {}
    
    def add_connection(self, connection_id: str, connection: DatabaseConnection) -> bool:
        """Add a new database connection"""
        if connection.connect():
            self.connections[connection_id] = connection
            return True
        return False
    
    def get_connection(self, connection_id: str) -> Optional[DatabaseConnection]:
        """Get a database connection"""
        return self.connections.get(connection_id)
    
    def remove_connection(self, connection_id: str):
        """Remove a database connection"""
        if connection_id in self.connections:
            self.connections[connection_id].close()
            del self.connections[connection_id]
    
    def list_connections(self) -> List[str]:
        """List all connection IDs"""
        return list(self.connections.keys())

# Global instance
connection_manager = ConnectionManager()