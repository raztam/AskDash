from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    NaturalLanguageQuery, 
    QueryResult, 
    QueryHistory,
    ErrorResponse
)
from app.core.database import connection_manager
from app.services.ai_service import ai_service
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for query history (in production, use a proper database)
query_history: Dict[str, QueryHistory] = {}

@router.get("/ai/status")
async def get_ai_status():
    """Get AI service status and test connectivity"""
    try:
        status_info = ai_service.test_connection()
        return status_info
    except Exception as e:
        logger.error(f"AI status check failed: {e}")
        return {
            "status": "error",
            "provider": "unknown",
            "model": "unknown",
            "error": str(e),
            "message": f"Failed to get AI service status: {str(e)}"
        }

@router.post("/", response_model=QueryResult)
async def execute_natural_language_query(request: NaturalLanguageQuery):
    """Execute a natural language query"""
    try:
        # Get database connection
        connection = connection_manager.get_connection(request.connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Test connection
        if not connection.test_connection():
            raise HTTPException(status_code=400, detail="Database connection is not available")
        
        # Get schema information
        schema_info = connection.get_schema_info()
        
        # Generate SQL using AI
        ai_result = ai_service.generate_sql(request.query, schema_info)
        generated_sql = ai_result["sql"]
        
        # Execute the query
        start_time = time.time()
        data = connection.execute_query(generated_sql)
        execution_time = time.time() - start_time
        
        # Extract columns
        columns = list(data[0].keys()) if data else []
        
        # Suggest visualization type
        visualization_type = ai_result.get("visualization_hint", "table")
        if not visualization_type or visualization_type not in ["table", "bar_chart", "line_chart", "pie_chart", "kpi"]:
            visualization_type = ai_service.suggest_visualization(data, columns)
        
        # Generate query ID
        query_id = str(uuid.uuid4())
        
        # Create result
        result = QueryResult(
            query_id=query_id,
            original_query=request.query,
            generated_sql=generated_sql,
            data=data,
            columns=columns,
            row_count=len(data),
            execution_time=execution_time,
            visualization_type=visualization_type,
            timestamp=datetime.now()
        )
        
        # Store in history
        history_entry = QueryHistory(
            query_id=query_id,
            original_query=request.query,
            generated_sql=generated_sql,
            connection_id=request.connection_id,
            timestamp=datetime.now(),
            execution_time=execution_time,
            row_count=len(data),
            visualization_type=visualization_type
        )
        query_history[query_id] = history_entry
        
        return result
        
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history", response_model=List[QueryHistory])
async def get_query_history(connection_id: str = None, limit: int = 50):
    """Get query history"""
    history_list = list(query_history.values())
    
    # Filter by connection_id if provided
    if connection_id:
        history_list = [h for h in history_list if h.connection_id == connection_id]
    
    # Sort by timestamp (most recent first)
    history_list.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Apply limit
    return history_list[:limit]

@router.get("/{query_id}", response_model=QueryHistory)
async def get_query_by_id(query_id: str):
    """Get a specific query from history"""
    if query_id not in query_history:
        raise HTTPException(status_code=404, detail="Query not found")
    
    return query_history[query_id]

@router.post("/{query_id}/rerun", response_model=QueryResult)
async def rerun_query(query_id: str):
    """Rerun a query from history"""
    if query_id not in query_history:
        raise HTTPException(status_code=404, detail="Query not found")
    
    history_entry = query_history[query_id]
    
    # Get database connection
    connection = connection_manager.get_connection(history_entry.connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Test connection
    if not connection.test_connection():
        raise HTTPException(status_code=400, detail="Database connection is not available")
    
    try:
        # Execute the stored SQL query
        start_time = time.time()
        data = connection.execute_query(history_entry.generated_sql)
        execution_time = time.time() - start_time
        
        # Extract columns
        columns = list(data[0].keys()) if data else []
        
        # Generate new query ID for the rerun
        new_query_id = str(uuid.uuid4())
        
        # Create result
        result = QueryResult(
            query_id=new_query_id,
            original_query=history_entry.original_query,
            generated_sql=history_entry.generated_sql,
            data=data,
            columns=columns,
            row_count=len(data),
            execution_time=execution_time,
            visualization_type=history_entry.visualization_type,
            timestamp=datetime.now()
        )
        
        # Store new entry in history
        new_history_entry = QueryHistory(
            query_id=new_query_id,
            original_query=history_entry.original_query,
            generated_sql=history_entry.generated_sql,
            connection_id=history_entry.connection_id,
            timestamp=datetime.now(),
            execution_time=execution_time,
            row_count=len(data),
            visualization_type=history_entry.visualization_type
        )
        query_history[new_query_id] = new_history_entry
        
        return result
        
    except Exception as e:
        logger.error(f"Query rerun failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{query_id}")
async def delete_query_from_history(query_id: str):
    """Delete a query from history"""
    if query_id not in query_history:
        raise HTTPException(status_code=404, detail="Query not found")
    
    del query_history[query_id]
    return {"message": f"Query {query_id} deleted from history"}

@router.post("/sql", response_model=QueryResult)
async def execute_raw_sql(connection_id: str, sql: str):
    """Execute raw SQL query (for advanced users)"""
    try:
        # Get database connection
        connection = connection_manager.get_connection(connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Test connection
        if not connection.test_connection():
            raise HTTPException(status_code=400, detail="Database connection is not available")
        
        # Execute the query
        start_time = time.time()
        data = connection.execute_query(sql)
        execution_time = time.time() - start_time
        
        # Extract columns
        columns = list(data[0].keys()) if data else []
        
        # Suggest visualization type
        visualization_type = ai_service.suggest_visualization(data, columns)
        
        # Generate query ID
        query_id = str(uuid.uuid4())
        
        # Create result
        result = QueryResult(
            query_id=query_id,
            original_query="Raw SQL Query",
            generated_sql=sql,
            data=data,
            columns=columns,
            row_count=len(data),
            execution_time=execution_time,
            visualization_type=visualization_type,
            timestamp=datetime.now()
        )
        
        # Store in history
        history_entry = QueryHistory(
            query_id=query_id,
            original_query="Raw SQL Query",
            generated_sql=sql,
            connection_id=connection_id,
            timestamp=datetime.now(),
            execution_time=execution_time,
            row_count=len(data),
            visualization_type=visualization_type
        )
        query_history[query_id] = history_entry
        
        return result
        
    except Exception as e:
        logger.error(f"Raw SQL execution failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))