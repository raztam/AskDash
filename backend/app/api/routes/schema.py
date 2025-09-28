from fastapi import APIRouter, HTTPException
from app.models.schemas import SchemaInfo
from app.core.database import connection_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{connection_id}", response_model=SchemaInfo)
async def get_schema(connection_id: str):
    """Get database schema information"""
    try:
        connection = connection_manager.get_connection(connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        schema_info = connection.get_schema_info()
        
        return SchemaInfo(
            tables=schema_info["tables"],
            database_type=schema_info["database_type"]
        )
        
    except Exception as e:
        logger.error(f"Schema retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{connection_id}/tables")
async def list_tables(connection_id: str):
    """List all tables in the database"""
    try:
        connection = connection_manager.get_connection(connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        schema_info = connection.get_schema_info()
        
        return {
            "tables": list(schema_info["tables"].keys()),
            "count": len(schema_info["tables"])
        }
        
    except Exception as e:
        logger.error(f"Table listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{connection_id}/tables/{table_name}")
async def get_table_info(connection_id: str, table_name: str):
    """Get detailed information about a specific table"""
    try:
        connection = connection_manager.get_connection(connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        schema_info = connection.get_schema_info()
        
        if table_name not in schema_info["tables"]:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        return {
            "table_name": table_name,
            "table_info": schema_info["tables"][table_name]
        }
        
    except Exception as e:
        logger.error(f"Table info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))