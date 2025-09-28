from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class QueryType(str, Enum):
    SELECT = "select"
    ANALYTICS = "analytics"
    KPI = "kpi"

class DatabaseConnectionRequest(BaseModel):
    connection_id: str = Field(..., description="Unique identifier for the connection")
    db_type: str = Field(..., description="Database type (mysql, postgresql, mariadb, sqlite)")
    host: Optional[str] = Field(None, description="Database host")
    port: Optional[int] = Field(None, description="Database port")
    database: str = Field(..., description="Database name")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password")
    connection_string: Optional[str] = Field(None, description="Full connection string")

class DatabaseConnectionResponse(BaseModel):
    connection_id: str
    db_type: str
    database: str
    status: str
    connected_at: Optional[datetime] = None

class NaturalLanguageQuery(BaseModel):
    query: str = Field(..., description="Natural language query")
    connection_id: str = Field(..., description="Database connection ID")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the query")

class QueryResult(BaseModel):
    query_id: str
    original_query: str
    generated_sql: str
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time: float
    visualization_type: str
    timestamp: datetime

class QueryHistory(BaseModel):
    query_id: str
    original_query: str
    generated_sql: str
    connection_id: str
    timestamp: datetime
    execution_time: float
    row_count: int
    visualization_type: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class SchemaInfo(BaseModel):
    tables: Dict[str, Any]
    database_type: str
    last_updated: datetime = Field(default_factory=datetime.now)

class ExportRequest(BaseModel):
    query_id: str
    format: str = Field(..., description="Export format (pdf, csv)")
    include_chart: bool = Field(True, description="Include chart in export")