#!/usr/bin/env python3
"""
Test auto-fix with valid SQL to ensure it doesn't trigger incorrectly
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.sql_autofix_service import sql_autofix

async def test_valid_sql():
    """Test that auto-fix doesn't trigger on valid SQL"""
    
    print("🧪 Testing Auto-Fix with Valid SQL...")
    print("=" * 50)
    
    # Your valid SQL
    valid_sql = """-- Teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    base_country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drivers table
CREATE TABLE drivers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    nationality VARCHAR(100),
    date_of_birth DATE,
    team_id INT REFERENCES teams(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""
    
    # Test with various "error" messages that shouldn't trigger auto-fix
    test_cases = [
        {
            "error": "",
            "description": "Empty error message"
        },
        {
            "error": "Query executed successfully",
            "description": "Success message"
        },
        {
            "error": "Tables created successfully",
            "description": "Success with 'successfully'"
        },
        {
            "error": "Command completed successfully",
            "description": "Completion message"
        }
    ]
    
    schema = {"tables": {}}
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test['description']}")
        print(f"Error message: '{test['error']}'")
        
        try:
            fixed_sql = await sql_autofix.auto_fix_sql(
                sql=valid_sql,
                error_message=test['error'],
                schema=schema
            )
            
            if fixed_sql and fixed_sql != valid_sql:
                print(f"❌ PROBLEM: Auto-fix incorrectly triggered!")
                print(f"   Original length: {len(valid_sql)}")
                print(f"   Fixed length: {len(fixed_sql)}")
            else:
                print(f"✅ CORRECT: Auto-fix did not trigger (as expected)")
                
        except Exception as e:
            print(f"❌ Error during test: {e}")
    
    print("\n" + "=" * 50)
    
    # Test with actual error that SHOULD trigger auto-fix
    print("🔍 Testing with real error (should trigger auto-fix):")
    
    error_sql = "SELECT * FROM user WHERE id == 1;"
    real_error = 'relation "user" does not exist'
    
    try:
        fixed_sql = await sql_autofix.auto_fix_sql(
            sql=error_sql,
            error_message=real_error,
            schema=schema
        )
        
        if fixed_sql and fixed_sql != error_sql:
            print(f"✅ CORRECT: Auto-fix triggered for real error")
            print(f"   Fixed: {fixed_sql}")
        else:
            print(f"❌ PROBLEM: Auto-fix should have triggered but didn't")
            
    except Exception as e:
        print(f"❌ Error during real error test: {e}")
    
    print("\n✅ Valid SQL Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_valid_sql())