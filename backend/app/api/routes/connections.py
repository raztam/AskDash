from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    DatabaseConnectionRequest, 
    DatabaseConnectionResponse, 
    ErrorResponse
)
from app.core.database import connection_manager, DatabaseConnection, DatabaseType
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def build_connection_string(request: DatabaseConnectionRequest) -> str:
    """Build connection string from request parameters"""
    if request.connection_string:
        return request.connection_string
    
    if request.db_type.lower() == "sqlite":
        return f"sqlite:///{request.database}"
    
    # Use proper SQLAlchemy dialect+driver format
    db_type_mapping = {
        "mysql": "mysql+pymysql",
        "mariadb": "mysql+pymysql",  # MariaDB uses MySQL protocol with PyMySQL driver
        "postgresql": "postgresql+psycopg2"
    }
    
    dialect = db_type_mapping.get(request.db_type.lower(), request.db_type.lower())
    base_url = f"{dialect}://"
    
    if request.username and request.password:
        base_url += f"{request.username}:{request.password}@"
    elif request.username:
        base_url += f"{request.username}@"
    
    if request.host:
        base_url += request.host
        if request.port:
            base_url += f":{request.port}"
    
    base_url += f"/{request.database}"
    
    return base_url

@router.post("/", response_model=DatabaseConnectionResponse)
async def create_connection(request: DatabaseConnectionRequest):
    """Create a new database connection"""
    try:
        # Validate database type
        try:
            db_type = DatabaseType(request.db_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported database type: {request.db_type}"
            )
        
        # Build connection string
        connection_string = build_connection_string(request)
        
        # Create database connection
        db_connection = DatabaseConnection(connection_string, db_type)
        
        # Add to connection manager
        success = connection_manager.add_connection(request.connection_id, db_connection)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to establish database connection"
            )
        
        return DatabaseConnectionResponse(
            connection_id=request.connection_id,
            db_type=request.db_type,
            database=request.database,
            status="connected"
        )
        
    except Exception as e:
        logger.error(f"Connection creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[DatabaseConnectionResponse])
async def list_connections():
    """List all database connections"""
    connections = []
    for connection_id in connection_manager.list_connections():
        connection = connection_manager.get_connection(connection_id)
        if connection:
            connections.append(DatabaseConnectionResponse(
                connection_id=connection_id,
                db_type=connection.db_type.value,
                database="",  # We don't store this info separately
                status="connected" if connection.test_connection() else "disconnected"
            ))
    
    return connections

@router.delete("/{connection_id}")
async def delete_connection(connection_id: str):
    """Delete a database connection"""
    connection = connection_manager.get_connection(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    connection_manager.remove_connection(connection_id)
    return {"message": f"Connection {connection_id} deleted successfully"}

@router.get("/{connection_id}/test")
async def test_connection(connection_id: str):
    """Test a database connection"""
    connection = connection_manager.get_connection(connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    is_connected = connection.test_connection()
    return {
        "connection_id": connection_id,
        "status": "connected" if is_connected else "disconnected"
    }