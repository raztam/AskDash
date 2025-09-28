from fastapi import APIRouter, HTTPException, Response
from app.models.schemas import ExportRequest
from app.core.database import connection_manager
from app.api.routes.queries import query_history
import csv
import io
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/csv/{query_id}")
async def export_to_csv(query_id: str):
    """Export query results to CSV format"""
    try:
        if query_id not in query_history:
            raise HTTPException(status_code=404, detail="Query not found")
        
        history_entry = query_history[query_id]
        
        # Get database connection
        connection = connection_manager.get_connection(history_entry.connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Re-execute query to get fresh data
        data = connection.execute_query(history_entry.generated_sql)
        
        if not data:
            raise HTTPException(status_code=400, detail="No data to export")
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        # Get CSV content
        csv_content = output.getvalue()
        output.close()
        
        # Return CSV response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=query_{query_id[:8]}.csv"
            }
        )
        
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/json/{query_id}")
async def export_to_json(query_id: str):
    """Export query results to JSON format"""
    try:
        if query_id not in query_history:
            raise HTTPException(status_code=404, detail="Query not found")
        
        history_entry = query_history[query_id]
        
        # Get database connection
        connection = connection_manager.get_connection(history_entry.connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Re-execute query to get fresh data
        data = connection.execute_query(history_entry.generated_sql)
        
        # Create export data structure
        export_data = {
            "query_info": {
                "query_id": query_id,
                "original_query": history_entry.original_query,
                "generated_sql": history_entry.generated_sql,
                "connection_id": history_entry.connection_id,
                "timestamp": history_entry.timestamp.isoformat(),
                "execution_time": history_entry.execution_time,
                "row_count": len(data),
                "visualization_type": history_entry.visualization_type
            },
            "data": data
        }
        
        # Return JSON response
        return Response(
            content=json.dumps(export_data, indent=2, default=str),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=query_{query_id[:8]}.json"
            }
        )
        
    except Exception as e:
        logger.error(f"JSON export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_query_templates():
    """Get preset query templates for common analytics"""
    templates = [
        {
            "id": "sales_by_month",
            "name": "Sales by Month",
            "description": "Show total sales grouped by month",
            "template": "Show total sales by month for the last 12 months",
            "category": "Sales Analytics",
            "visualization_hint": "line_chart"
        },
        {
            "id": "top_products",
            "name": "Top Products by Revenue",
            "description": "Find the best performing products",
            "template": "What are the top 10 products by revenue?",
            "category": "Product Analytics",
            "visualization_hint": "bar_chart"
        },
        {
            "id": "customer_segments",
            "name": "Customer Segments",
            "description": "Analyze customer distribution",
            "template": "How many customers do we have by region?",
            "category": "Customer Analytics",
            "visualization_hint": "pie_chart"
        },
        {
            "id": "average_order_value",
            "name": "Average Order Value",
            "description": "Calculate average order value by segment",
            "template": "Show average order value by customer segment",
            "category": "Sales Analytics",
            "visualization_hint": "bar_chart"
        },
        {
            "id": "total_revenue",
            "name": "Total Revenue",
            "description": "Show total revenue for a period",
            "template": "What is the total revenue for this year?",
            "category": "KPIs",
            "visualization_hint": "kpi"
        },
        {
            "id": "customer_growth",
            "name": "Customer Growth",
            "description": "Track new customer acquisitions",
            "template": "Show new customer registrations by month",
            "category": "Growth Analytics",
            "visualization_hint": "line_chart"
        },
        {
            "id": "product_categories",
            "name": "Sales by Category",
            "description": "Compare sales across product categories",
            "template": "Show total sales by product category",
            "category": "Product Analytics",
            "visualization_hint": "pie_chart"
        },
        {
            "id": "weekly_orders",
            "name": "Weekly Order Trends",
            "description": "Analyze order patterns by day of week",
            "template": "How many orders were placed each day this week?",
            "category": "Order Analytics",
            "visualization_hint": "bar_chart"
        },
        {
            "id": "inventory_levels",
            "name": "Inventory Status",
            "description": "Check current inventory levels",
            "template": "Show current inventory levels by product",
            "category": "Inventory Analytics",
            "visualization_hint": "table"
        },
        {
            "id": "user_activity",
            "name": "User Activity",
            "description": "Track user engagement metrics",
            "template": "Show user login activity by month",
            "category": "User Analytics",
            "visualization_hint": "line_chart"
        }
    ]
    
    return {
        "templates": templates,
        "categories": list(set(t["category"] for t in templates))
    }