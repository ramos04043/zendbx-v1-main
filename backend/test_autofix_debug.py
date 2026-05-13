"""
Debug autofix formatting issue
"""

import asyncio
from app.services.sql_autofix_service import sql_autofix

async def test_single():
    sql = """-- Create drivers table
CREATE TABLE drivers (
    driver_id SERIAL PRIMARY KEY
    name VARCHAR(100) NOT NULL,
    nationality VARCHAR(50),
    date_of_birth DATE,
    team_id INTEGER REFERENCES teams(team_id)
);"""
    
    error = 'syntax error at or near "name"'
    schema = {
        "tables": {
            "teams": {
                "columns": [{"name": "team_id"}, {"name": "name"}]
            }
        }
    }
    
    print("ORIGINAL SQL:")
    print(sql)
    print(f"\nOriginal has {sql.count(chr(10))} line breaks")
    print(f"Original length: {len(sql)}")
    
    print("\n" + "="*80)
    print("ATTEMPTING FIX...")
    print("="*80 + "\n")
    
    fixed = await sql_autofix.auto_fix_sql(sql, error, schema)
    
    if fixed:
        print("\nFIXED SQL:")
        print(fixed)
        print(f"\nFixed has {fixed.count(chr(10))} line breaks")
        print(f"Fixed length: {len(fixed)}")
    else:
        print("\nNO FIX FOUND")

if __name__ == "__main__":
    asyncio.run(test_single())
