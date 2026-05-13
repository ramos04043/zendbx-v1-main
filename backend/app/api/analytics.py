from fastapi import APIRouter, HTTPException, Depends, status
from app.api.auth import get_current_user
from app.core.database import execute_on_main_db, execute_on_project_db
from uuid import UUID
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncpg

router = APIRouter()

# ============================================
# HELPER: Verify Project Access
# ============================================

async def verify_project_access(project_id: UUID, user_id: UUID) -> dict:
    """Verify user has access to project"""
    result = await execute_on_main_db(
        "SELECT * FROM projects WHERE id = $1 AND user_id = $2",
        project_id,
        user_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return dict(result[0])

# ============================================
# GET PERFORMANCE METRICS
# ============================================

@router.get("/projects/{project_id}/analytics/performance")
async def get_performance_metrics(
    project_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get real-time performance metrics for project"""
    
    project = await verify_project_access(project_id, current_user["id"])
    
    # Calculate time ranges
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_minute = now - timedelta(minutes=1)
    
    # Get queries per second (last minute)
    queries_last_minute = await execute_on_main_db(
        """
        SELECT COUNT(*) as count
        FROM query_history
        WHERE project_id = $1 AND created_at >= $2
        """,
        project_id,
        last_minute
    )
    queries_per_sec = round(queries_last_minute[0]["count"] / 60, 2) if queries_last_minute else 0
    
    # Get average response time (last hour)
    last_hour = now - timedelta(hours=1)
    avg_response = await execute_on_main_db(
        """
        SELECT AVG(execution_time_ms) as avg_time
        FROM query_history
        WHERE project_id = $1 AND created_at >= $2 AND status = 'success'
        """,
        project_id,
        last_hour
    )
    avg_response_time = int(avg_response[0]["avg_time"]) if avg_response and avg_response[0]["avg_time"] else 0
    
    # Get total queries today
    total_today = await execute_on_main_db(
        """
        SELECT COUNT(*) as count
        FROM query_history
        WHERE project_id = $1 AND created_at >= $2
        """,
        project_id,
        today_start
    )
    total_queries_today = total_today[0]["count"] if total_today else 0
    
    # Get slow queries count (>500ms, today)
    slow_queries = await execute_on_main_db(
        """
        SELECT COUNT(*) as count
        FROM query_history
        WHERE project_id = $1 
        AND created_at >= $2 
        AND execution_time_ms > 500
        AND status = 'success'
        """,
        project_id,
        today_start
    )
    slow_queries_count = slow_queries[0]["count"] if slow_queries else 0
    
    # Get REAL-TIME database resource usage from PostgreSQL
    try:
        # Get actual PostgreSQL stats
        db_stats = await execute_on_project_db(
            project["database_name"],
            """
            SELECT 
                (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND state = 'active') as active_connections,
                (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) as total_connections,
                pg_database_size(current_database()) as db_size_bytes,
                (SELECT sum(numbackends) FROM pg_stat_database WHERE datname = current_database()) as backends,
                (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND wait_event_type IS NOT NULL) as waiting_queries
            """
        )
        
        active_connections = db_stats[0]["active_connections"] if db_stats else 0
        total_connections = db_stats[0]["total_connections"] if db_stats else 0
        db_size_bytes = db_stats[0]["db_size_bytes"] if db_stats else 0
        waiting_queries = db_stats[0]["waiting_queries"] if db_stats else 0
        
        # Calculate CPU usage based on active queries and waiting queries
        cpu_usage = min(100, int((active_connections + waiting_queries) * 15))
        
        # Calculate memory usage based on DB size (rough estimate)
        # Assume 1GB = 10% memory usage
        memory_usage = min(100, int((db_size_bytes / (1024 * 1024 * 1024)) * 10))
        
    except Exception as e:
        print(f"Error getting DB stats: {e}")
        active_connections = 0
        total_connections = 0
        cpu_usage = 0
        memory_usage = 0
    
    return {
        "queries_per_sec": queries_per_sec,
        "avg_response_time_ms": avg_response_time,
        "total_queries_today": total_queries_today,
        "slow_queries_count": slow_queries_count,
        "cpu_usage_percent": cpu_usage,
        "memory_usage_percent": memory_usage,
        "active_connections": active_connections,
        "total_connections": total_connections,
        "timestamp": now.isoformat()
    }

# ============================================
# GET SLOW QUERY LOG
# ============================================

@router.get("/projects/{project_id}/analytics/slow-queries")
async def get_slow_queries(
    project_id: UUID,
    limit: int = 50,
    threshold_ms: int = 500,
    current_user: dict = Depends(get_current_user)
):
    """Get slow queries log (queries taking longer than threshold)"""
    
    await verify_project_access(project_id, current_user["id"])
    
    # Get slow queries from last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    result = await execute_on_main_db(
        """
        SELECT 
            id,
            sql_query,
            execution_time_ms,
            rows_returned,
            created_at,
            status
        FROM query_history
        WHERE project_id = $1 
        AND created_at >= $2
        AND execution_time_ms > $3
        AND status = 'success'
        ORDER BY execution_time_ms DESC
        LIMIT $4
        """,
        project_id,
        yesterday,
        threshold_ms,
        limit
    )
    
    slow_queries = []
    for row in result:
        slow_queries.append({
            "id": str(row["id"]),
            "query": row["sql_query"][:200] + "..." if len(row["sql_query"]) > 200 else row["sql_query"],
            "execution_time_ms": row["execution_time_ms"],
            "rows_examined": row["rows_returned"] or 0,
            "timestamp": row["created_at"].isoformat()
        })
    
    return {
        "slow_queries": slow_queries,
        "count": len(slow_queries),
        "threshold_ms": threshold_ms
    }

# ============================================
# GET QUERY TRENDS (for charts)
# ============================================

@router.get("/projects/{project_id}/analytics/trends")
async def get_query_trends(
    project_id: UUID,
    hours: int = 24,
    current_user: dict = Depends(get_current_user)
):
    """Get query trends over time (for charts)"""
    
    await verify_project_access(project_id, current_user["id"])
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get queries grouped by hour
    result = await execute_on_main_db(
        """
        SELECT 
            date_trunc('hour', created_at) as hour,
            COUNT(*) as query_count,
            AVG(execution_time_ms) as avg_time,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as error_count
        FROM query_history
        WHERE project_id = $1 AND created_at >= $2
        GROUP BY hour
        ORDER BY hour
        """,
        project_id,
        start_time
    )
    
    trends = []
    for row in result:
        trends.append({
            "timestamp": row["hour"].isoformat(),
            "query_count": row["query_count"],
            "avg_response_time_ms": int(row["avg_time"]) if row["avg_time"] else 0,
            "error_count": row["error_count"]
        })
    
    return {
        "trends": trends,
        "period_hours": hours
    }
