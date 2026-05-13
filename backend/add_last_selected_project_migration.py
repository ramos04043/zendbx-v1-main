"""
Migration: Add last_selected_project_id to users table
"""
import asyncio
import asyncpg

async def run_migration():
    """Add last_selected_project_id column to users table"""
    
    # Connect to main database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='Pawan@121',
        database='nexora_main'
    )
    
    try:
        print("Running migration: add_last_selected_project_id...")
        
        # Read and execute SQL file
        with open('database/add_last_selected_project.sql', 'r') as f:
            sql = f.read()
        
        await conn.execute(sql)
        
        print("✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
