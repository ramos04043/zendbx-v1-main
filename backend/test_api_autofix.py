#!/usr/bin/env python3
"""
Test the complete API flow for auto-fix
"""

import asyncio
import sys
import os
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api.queries import execute_query, get_project_schema
from app.models.schemas import QueryExecute
from uuid import uuid4

async def test_api_flow():
    """Test the complete API flow"""
    
    print("🧪 Testing Complete Auto-Fix API Flow...")
    print("=" * 60)
    
    # Mock project schema
    mock_schema = {
        "tables": {
            "users": {
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "name", "type": "text"},
                    {"name": "email", "type": "text"},
                    {"name": "created_at", "type": "timestamp"}
                ]
            },
            "posts": {
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "title", "type": "text"},
                    {"name": "content", "type": "text"},
                    {"name": "user_id", "type": "integer"}
                ]
            }
        }
    }
    
    print("Mock Schema Available:")
    for table, info in mock_schema["tables"].items():
        columns = [col["name"] for col in info["columns"]]
        print(f"  📋 {table}: {', '.join(columns)}")
    
    print("\n" + "=" * 60)
    
    # Test queries that should trigger auto-fix
    test_queries = [
        {
            "sql": "SELECT * FROM user WHERE id = 1;",
            "description": "Table name error (user → users)"
        },
        {
            "sql": "SELECT name, emai FROM users;",
            "description": "Column name typo (emai → email)"
        },
        {
            "sql": "SELECT u.name, p.title FROM user u JOIN post p ON u.id = p.user_id;",
            "description": "Multiple table name errors"
        },
        {
            "sql": "SELECT * FROM users WHERE status == 'active';",
            "description": "Operator error (== → =)"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {test['description']}")
        print(f"Query: {test['sql']}")
        
        # Simulate the auto-fix logic from queries.py
        from app.services.sql_autofix_service import sql_autofix
        
        # Simulate a database error
        mock_error = f"relation \"user\" does not exist" if "user" in test['sql'] else f"column \"emai\" does not exist"
        
        try:
            fixed_sql = await sql_autofix.auto_fix_sql(
                sql=test['sql'],
                error_message=mock_error,
                schema=mock_schema
            )
            
            if fixed_sql and fixed_sql != test['sql']:
                print(f"✅ Auto-Fix Success!")
                print(f"   Original: {test['sql']}")
                print(f"   Fixed:    {fixed_sql}")
            else:
                print(f"❌ Auto-Fix Failed - No changes made")
                
        except Exception as e:
            print(f"❌ Auto-Fix Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Auto-Fix Service Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_api_flow())