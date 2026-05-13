#!/usr/bin/env python3
"""
Quick test for SQL Auto-Fix Service
Run this to verify the auto-fix functionality works
"""

import asyncio
from app.services.sql_autofix_service import sql_autofix

async def test_autofix():
    """Test the auto-fix service with common SQL errors"""
    
    # Test schema
    test_schema = {
        "tables": {
            "users": {
                "columns": [
                    {"name": "id", "type": "UUID", "primary_key": True},
                    {"name": "name", "type": "TEXT"},
                    {"name": "email", "type": "TEXT"},
                    {"name": "created_at", "type": "TIMESTAMP"}
                ]
            },
            "posts": {
                "columns": [
                    {"name": "id", "type": "UUID", "primary_key": True},
                    {"name": "title", "type": "TEXT"},
                    {"name": "content", "type": "TEXT"},
                    {"name": "user_id", "type": "UUID"}
                ]
            }
        }
    }
    
    # Test cases
    test_cases = [
        {
            "name": "Table name typo",
            "sql": "SELECT name FROM user WHERE id = 1;",
            "error": 'relation "user" does not exist',
            "expected_fix": "users"
        },
        {
            "name": "Column name typo", 
            "sql": "SELECT nam FROM users WHERE id = 1;",
            "error": 'column "nam" does not exist',
            "expected_fix": "name"
        },
        {
            "name": "Multiple typos",
            "sql": "SELECT nam FROM user WHERE idd = 1;", 
            "error": 'relation "user" does not exist',
            "expected_fix": "users"
        }
    ]
    
    print("🔧 Testing SQL Auto-Fix Service")
    print("=" * 50)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"Original SQL: {test['sql']}")
        print(f"Error: {test['error']}")
        
        try:
            fixed_sql = await sql_autofix.auto_fix_sql(
                sql=test['sql'],
                error_message=test['error'],
                schema=test_schema
            )
            
            if fixed_sql and fixed_sql != test['sql']:
                print(f"✅ Fixed SQL: {fixed_sql}")
                if test['expected_fix'] in fixed_sql:
                    print("✅ Fix contains expected correction!")
                else:
                    print("⚠️  Fix doesn't contain expected correction")
            else:
                print("❌ No fix generated")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Auto-fix testing complete!")

if __name__ == "__main__":
    asyncio.run(test_autofix())