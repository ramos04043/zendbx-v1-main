"""
Test V2 autofix
"""

import asyncio
from app.services.sql_autofix_service_v2 import sql_autofix_v2

async def test():
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
    print(f"\nLines: {sql.count(chr(10))}")
    
    print("\n" + "="*80)
    
    fixed = await sql_autofix_v2.auto_fix_sql(sql, error, schema)
    
    if fixed:
        print("\nFIXED SQL:")
        print(fixed)
        print(f"\nLines: {fixed.count(chr(10))}")
    else:
        print("\nNO FIX")

if __name__ == "__main__":
    asyncio.run(test())
