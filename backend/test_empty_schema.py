#!/usr/bin/env python3
"""
Test auto-fix with empty schema (like a new project)
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.sql_autofix_service import sql_autofix

async def test_empty_schema():
    """Test auto-fix with empty schema"""
    
    print("🧪 Testing Auto-Fix with Empty Schema...")
    print("=" * 50)
    
    # Empty schema (like a new project)
    empty_schema = {"tables": {}}
    
    test_cases = [
        {
            "sql": "SELECT * FROM users WHERE status == 'active';",
            "error": "syntax error at or near \"=\"",
            "description": "Operator error with empty schema"
        },
        {
            "sql": "SELECT * FROM user WHERE id == 1;",
            "error": 'relation "user" does not exist',
            "description": "Table + operator error with empty schema"
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
                schema=empty_schema
            )
            
            if fixed_sql and fixed_sql != test['sql']:
                print(f"✅ Fixed: {fixed_sql}")
            else:
                print(f"❌ No fix applied (this might be expected with empty schema)")
                
        except Exception as e:
            print(f"❌ Error during fix: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Empty Schema Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_empty_schema())