#!/usr/bin/env python3
"""
Simple test script for auto-fix functionality
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.sql_autofix_service import sql_autofix

async def test_simple_fixes():
    """Test basic auto-fix functionality"""
    
    print("🧪 Testing SQL Auto-Fix Service...")
    print("=" * 50)
    
    # Test case 1: Table name error
    test_sql = "SELECT * FROM user WHERE id = 1;"
    test_error = 'relation "user" does not exist'
    test_schema = {
        "tables": {
            "users": {
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "name", "type": "text"},
                    {"name": "email", "type": "text"}
                ]
            }
        }
    }
    
    print(f"Original SQL: {test_sql}")
    print(f"Error: {test_error}")
    
    try:
        fixed_sql = await sql_autofix.auto_fix_sql(test_sql, test_error, test_schema)
        if fixed_sql:
            print(f"✅ Fixed SQL: {fixed_sql}")
        else:
            print("❌ No fix found")
    except Exception as e:
        print(f"❌ Error during fix: {e}")
    
    print("\n" + "=" * 50)
    
    # Test case 2: Column name error
    test_sql2 = "SELECT name, emai FROM users;"
    test_error2 = 'column "emai" does not exist'
    
    print(f"Original SQL: {test_sql2}")
    print(f"Error: {test_error2}")
    
    try:
        fixed_sql2 = await sql_autofix.auto_fix_sql(test_sql2, test_error2, test_schema)
        if fixed_sql2:
            print(f"✅ Fixed SQL: {fixed_sql2}")
        else:
            print("❌ No fix found")
    except Exception as e:
        print(f"❌ Error during fix: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_fixes())