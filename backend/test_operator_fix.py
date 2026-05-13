#!/usr/bin/env python3
"""
Test the == operator fix specifically
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.sql_autofix_service import sql_autofix

async def test_operator_fixes():
    """Test operator-specific fixes"""
    
    print("🧪 Testing Operator Auto-Fix...")
    print("=" * 50)
    
    # Test schema
    test_schema = {
        "tables": {
            "users": {
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "name", "type": "text"},
                    {"name": "email", "type": "text"},
                    {"name": "status", "type": "text"}
                ]
            }
        }
    }
    
    # Test cases for operator errors
    test_cases = [
        {
            "sql": "SELECT * FROM users WHERE status == 'active';",
            "error": "syntax error at or near \"=\"",
            "description": "Double equals operator"
        },
        {
            "sql": "SELECT * FROM user WHERE id == 1;",
            "error": 'relation "user" does not exist',
            "description": "Table name + operator error"
        },
        {
            "sql": "SELECT * FROM users WHERE name != 'test';",
            "error": "syntax error at or near \"!\"",
            "description": "Not equals operator"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test['description']}")
        print(f"Original: {test['sql']}")
        print(f"Error: {test['error']}")
        
        try:
            fixed_sql = await sql_autofix.auto_fix_sql(
                sql=test['sql'],
                error_message=test['error'],
                schema=test_schema
            )
            
            if fixed_sql and fixed_sql != test['sql']:
                print(f"✅ Fixed: {fixed_sql}")
                print(f"🔧 Changes: {test['sql']} → {fixed_sql}")
            else:
                print(f"❌ No fix applied")
                
        except Exception as e:
            print(f"❌ Error during fix: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Operator Fix Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_operator_fixes())