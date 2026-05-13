"""
Test improved SQL autofix with proper formatting preservation
"""

import asyncio
from app.services.sql_autofix_service import sql_autofix

# Test cases with various SQL errors
test_cases = [
    {
        "name": "Simple table name typo",
        "sql": "SELECT * FROM user WHERE id = 1;",
        "error": 'relation "user" does not exist',
        "schema": {
            "tables": {
                "users": {
                    "columns": [
                        {"name": "id"},
                        {"name": "name"},
                        {"name": "email"}
                    ]
                }
            }
        }
    },
    {
        "name": "CREATE TABLE with formatting",
        "sql": """-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);""",
        "error": 'syntax error at or near "name"',
        "schema": {"tables": {}}
    },
    {
        "name": "Multi-line CREATE TABLE",
        "sql": """-- Create drivers table
CREATE TABLE drivers (
    driver_id SERIAL PRIMARY KEY
    name VARCHAR(100) NOT NULL,
    nationality VARCHAR(50),
    date_of_birth DATE,
    team_id INTEGER REFERENCES teams(team_id)
);""",
        "error": 'syntax error at or near "name"',
        "schema": {
            "tables": {
                "teams": {
                    "columns": [{"name": "team_id"}, {"name": "name"}]
                }
            }
        }
    },
    {
        "name": "Column name typo",
        "sql": "SELECT nam, emai FROM users;",
        "error": 'column "nam" does not exist',
        "schema": {
            "tables": {
                "users": {
                    "columns": [
                        {"name": "id"},
                        {"name": "name"},
                        {"name": "email"}
                    ]
                }
            }
        }
    },
    {
        "name": "REFERENCES typo",
        "sql": """CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    user_id INTEGER REFERENCES user(id)
);""",
        "error": 'relation "user" does not exist',
        "schema": {
            "tables": {
                "users": {
                    "columns": [{"name": "id"}, {"name": "name"}]
                }
            }
        }
    }
]

async def test_autofix():
    print("=" * 80)
    print("TESTING IMPROVED SQL AUTO-FIX SERVICE")
    print("=" * 80)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'=' * 80}")
        
        print(f"\n📝 ORIGINAL SQL:")
        print("-" * 80)
        print(test['sql'])
        
        print(f"\n❌ ERROR MESSAGE:")
        print("-" * 80)
        print(test['error'])
        
        print(f"\n🔧 ATTEMPTING AUTO-FIX...")
        print("-" * 80)
        
        try:
            fixed_sql = await sql_autofix.auto_fix_sql(
                sql=test['sql'],
                error_message=test['error'],
                schema=test['schema']
            )
            
            if fixed_sql:
                print(f"✅ AUTO-FIX SUCCESSFUL!")
                print(f"\n📝 FIXED SQL:")
                print("-" * 80)
                print(fixed_sql)
                
                # Check if formatting is preserved
                original_lines = test['sql'].count('\n')
                fixed_lines = fixed_sql.count('\n')
                
                print(f"\n📊 FORMATTING CHECK:")
                print(f"  Original lines: {original_lines}")
                print(f"  Fixed lines: {fixed_lines}")
                print(f"  Line difference: {abs(original_lines - fixed_lines)}")
                
                # Check if comments are preserved
                original_comments = test['sql'].count('--')
                fixed_comments = fixed_sql.count('--')
                print(f"  Original comments: {original_comments}")
                print(f"  Fixed comments: {fixed_comments}")
                
                if original_comments == fixed_comments:
                    print(f"  ✅ Comments preserved!")
                else:
                    print(f"  ⚠️  Comments may have been lost")
                
                # Check if it's different from original
                if fixed_sql != test['sql']:
                    print(f"  ✅ SQL was modified (fix applied)")
                else:
                    print(f"  ⚠️  SQL unchanged (no fix applied)")
                
            else:
                print(f"❌ AUTO-FIX FAILED - No fix found")
                
        except Exception as e:
            print(f"❌ AUTO-FIX ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 80}")
    print("ALL TESTS COMPLETED")
    print(f"{'=' * 80}\n")

if __name__ == "__main__":
    asyncio.run(test_autofix())
