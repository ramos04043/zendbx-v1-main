#!/usr/bin/env python3
"""
Debug the real scenario - simulate exactly what happens in the API
"""

import asyncio
import sys
import os
import traceback

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.sql_autofix_service import sql_autofix
from app.api.queries import get_project_schema
from uuid import uuid4, UUID

async def debug_real_scenario():
    """Debug the real scenario with actual API flow"""
    
    print("🔍 Debugging Real Auto-Fix Scenario...")
    print("=" * 60)
    
    # The exact query you're testing
    test_sql = "SELECT * FROM user WHERE status == 'active';"
    print(f"Testing SQL: {test_sql}")
    
    # Simulate the error that PostgreSQL would return
    postgres_errors = [
        'relation "user" does not exist',
        "syntax error at or near \"=\"",
        "operator does not exist: text == unknown"
    ]
    
    for error_msg in postgres_errors:
        print(f"\n🔍 Testing with error: {error_msg}")
        
        # Test with empty schema (new project scenario)
        empty_schema = {"tables": {}}
        
        try:
            print("   📋 Attempting auto-fix with empty schema...")
            fixed_sql = await sql_autofix.auto_fix_sql(
                sql=test_sql,
                error_message=error_msg,
                schema=empty_schema
            )
            
            if fixed_sql and fixed_sql != test_sql:
                print(f"   ✅ Auto-fix successful!")
                print(f"      Original: {test_sql}")
                print(f"      Fixed:    {fixed_sql}")
                
                # Analyze what was fixed
                changes = []
                if "user " in test_sql and "users " in fixed_sql:
                    changes.append("Table: user → users")
                if "==" in test_sql and "==" not in fixed_sql:
                    changes.append("Operator: == → =")
                
                if changes:
                    print(f"      Changes:  {', '.join(changes)}")
                
            else:
                print(f"   ❌ Auto-fix failed - no changes made")
                
        except Exception as e:
            print(f"   ❌ Error during auto-fix: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    
    # Test the complete flow step by step
    print("🔧 Testing Complete Auto-Fix Flow...")
    
    # Step 1: Validate SQL (should pass)
    from app.api.queries import validate_sql_query
    is_valid, error_msg = validate_sql_query(test_sql)
    print(f"1. SQL Validation: {'✅ PASS' if is_valid else '❌ FAIL'} - {error_msg}")
    
    # Step 2: Schema retrieval (will fail with fake UUID, but that's OK)
    fake_project_id = uuid4()
    print(f"2. Schema Retrieval: Testing with fake project ID {fake_project_id}")
    try:
        schema = await get_project_schema(fake_project_id)
        print(f"   ✅ Schema retrieved: {len(schema.get('tables', {}))} tables")
    except Exception as e:
        print(f"   ⚠️  Schema retrieval failed (expected): {e}")
        schema = {"tables": {}}  # Use empty schema
    
    # Step 3: Auto-fix attempt
    print("3. Auto-Fix Attempt:")
    try:
        fixed_sql = await sql_autofix.auto_fix_sql(
            sql=test_sql,
            error_message="syntax error at or near \"=\"",
            schema=schema
        )
        
        if fixed_sql and fixed_sql != test_sql:
            print(f"   ✅ Auto-fix successful: {fixed_sql}")
        else:
            print(f"   ❌ Auto-fix failed")
            
    except Exception as e:
        print(f"   ❌ Auto-fix error: {e}")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Debug Complete!")
    print("\n💡 If auto-fix is working here but not in your frontend:")
    print("   1. Check if your project has the correct project ID")
    print("   2. Verify your JWT token is valid")
    print("   3. Make sure the backend is running on the correct port")
    print("   4. Check browser console for any JavaScript errors")
    print("   5. Try the test_backend_autofix.html file to test directly")

if __name__ == "__main__":
    asyncio.run(debug_real_scenario())