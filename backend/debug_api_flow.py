#!/usr/bin/env python3
"""
Debug the complete API flow for auto-fix
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import execute_on_project_db
from app.services.sql_autofix_service import sql_autofix
from uuid import uuid4

async def debug_api_flow():
    """Debug the complete API flow"""
    
    print("🔍 Debugging Auto-Fix API Flow...")
    print("=" * 60)
    
    # Test query that should fail
    test_sql = "SELECT * FROM users WHERE status == 'active';"
    
    print(f"Testing SQL: {test_sql}")
    
    # Step 1: Try to execute the query (should fail)
    print("\n📋 Step 1: Execute original query...")
    try:
        # This should fail - we don't have a real project database
        # But we can simulate the error
        error_message = "syntax error at or near \"=\""
        print(f"❌ Query failed with error: {error_message}")
        
        # Step 2: Try auto-fix
        print("\n🔧 Step 2: Attempting auto-fix...")
        
        # Mock schema
        mock_schema = {
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
        
        fixed_sql = await sql_autofix.auto_fix_sql(
            sql=test_sql,
            error_message=error_message,
            schema=mock_schema
        )
        
        if fixed_sql and fixed_sql != test_sql:
            print(f"✅ Auto-fix successful!")
            print(f"   Original: {test_sql}")
            print(f"   Fixed:    {fixed_sql}")
            
            # Step 3: Verify the fix
            print(f"\n✨ Step 3: Verifying fix...")
            if "==" not in fixed_sql and "=" in fixed_sql:
                print("✅ Operator fix verified: == → =")
            else:
                print("❌ Operator fix not applied correctly")
                
        else:
            print("❌ Auto-fix failed - no changes made")
            
    except Exception as e:
        print(f"❌ Error in debug flow: {e}")
    
    print("\n" + "=" * 60)
    
    # Test the specific error patterns
    print("🧪 Testing Error Pattern Matching...")
    
    error_patterns = [
        "syntax error at or near \"=\"",
        'relation "user" does not exist',
        'column "emai" does not exist',
        "syntax error at or near \"!\"",
    ]
    
    for error in error_patterns:
        print(f"\n🔍 Testing error: {error}")
        try:
            fixed = await sql_autofix.auto_fix_sql(
                sql=test_sql,
                error_message=error,
                schema=mock_schema
            )
            if fixed and fixed != test_sql:
                print(f"   ✅ Fixed: {fixed}")
            else:
                print(f"   ❌ No fix applied")
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_api_flow())