"""
Test script to verify backup system is working correctly
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.backup_service import BackupService
from app.core.database import get_main_db_pool, get_project_db_pool
import uuid


async def test_database_connection(db_name: str):
    """Test if we can connect to a database"""
    print(f"\n{'='*60}")
    print(f"Testing connection to: {db_name}")
    print(f"{'='*60}")
    
    try:
        pool = await get_project_db_pool(db_name)
        async with pool.acquire() as conn:
            # Get current database
            current_db = await conn.fetchval("SELECT current_database()")
            print(f"✓ Connected to database: {current_db}")
            
            # Get table count
            table_count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
            print(f"✓ Tables found: {table_count}")
            
            # List tables
            if table_count > 0:
                tables = await conn.fetch(
                    """
                    SELECT tablename, 
                           (SELECT COUNT(*) FROM information_schema.columns 
                            WHERE table_name = tablename AND table_schema = 'public') as column_count
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                    """
                )
                print(f"\nTables:")
                for table in tables:
                    print(f"  - {table['tablename']} ({table['column_count']} columns)")
                
                # Get row counts
                print(f"\nRow counts:")
                for table in tables:
                    try:
                        row_count = await conn.fetchval(
                            f"SELECT COUNT(*) FROM {table['tablename']}"
                        )
                        print(f"  - {table['tablename']}: {row_count} rows")
                    except Exception as e:
                        print(f"  - {table['tablename']}: Error - {e}")
            
            # Get database size
            db_size = await conn.fetchval("SELECT pg_database_size(current_database())")
            print(f"\n✓ Database size: {db_size:,} bytes ({db_size / 1024 / 1024:.2f} MB)")
            
            return True
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


async def test_backup_creation(project_id: str, db_name: str):
    """Test creating a backup"""
    print(f"\n{'='*60}")
    print(f"Testing backup creation")
    print(f"{'='*60}")
    
    try:
        backup_service = BackupService()
        
        print(f"Project ID: {project_id}")
        print(f"Database: {db_name}")
        print(f"Backup directory: {backup_service.backup_dir}")
        print(f"pg_dump path: {backup_service.pg_dump_path}")
        
        # Create backup
        print(f"\nCreating backup...")
        backup = await backup_service.create_backup(
            project_id=project_id,
            db_name=db_name,
            backup_name=f"test_backup_{uuid.uuid4().hex[:8]}",
            backup_type="manual",
            user_id=None
        )
        
        print(f"\n✓ Backup created successfully!")
        print(f"  - ID: {backup['id']}")
        print(f"  - Name: {backup['name']}")
        print(f"  - Status: {backup['status']}")
        print(f"  - File: {backup['file_path']}")
        print(f"  - Size: {backup['file_size']:,} bytes ({backup['file_size'] / 1024 / 1024:.2f} MB)")
        
        if backup.get('metadata'):
            print(f"\n  Metadata:")
            print(f"    - Tables: {backup['metadata'].get('table_count', 0)}")
            print(f"    - Rows: {backup['metadata'].get('row_count', 0)}")
            print(f"    - DB Size: {backup['metadata'].get('database_size', 0):,} bytes")
        
        # Verify file exists
        file_path = Path(backup['file_path'])
        if file_path.exists():
            print(f"\n✓ Backup file exists on disk")
            print(f"  - Path: {file_path}")
            print(f"  - Size: {file_path.stat().st_size:,} bytes")
        else:
            print(f"\n✗ Backup file NOT found on disk!")
        
        return backup
        
    except Exception as e:
        print(f"\n✗ Backup creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def list_projects():
    """List all projects"""
    print(f"\n{'='*60}")
    print(f"Available Projects")
    print(f"{'='*60}")
    
    try:
        pool = await get_main_db_pool()
        async with pool.acquire() as conn:
            projects = await conn.fetch(
                """
                SELECT id, name, database_name, created_at
                FROM projects
                ORDER BY created_at DESC
                LIMIT 10
                """
            )
            
            if not projects:
                print("No projects found!")
                return []
            
            print(f"\nFound {len(projects)} project(s):\n")
            for i, project in enumerate(projects, 1):
                print(f"{i}. {project['name']}")
                print(f"   ID: {project['id']}")
                print(f"   Database: {project['database_name']}")
                print(f"   Created: {project['created_at']}")
                print()
            
            return projects
            
    except Exception as e:
        print(f"✗ Failed to list projects: {e}")
        return []


async def main():
    """Main test function"""
    print("\n" + "="*60)
    print("ZENDBX BACKUP SYSTEM TEST")
    print("="*60)
    
    # List projects
    projects = await list_projects()
    
    if not projects:
        print("\n⚠️  No projects found. Please create a project first.")
        return
    
    # Use first project for testing
    project = projects[0]
    project_id = str(project['id'])
    db_name = project['database_name']
    
    print(f"\n📋 Testing with project: {project['name']}")
    
    # Test database connection
    connection_ok = await test_database_connection(db_name)
    
    if not connection_ok:
        print("\n⚠️  Cannot connect to database. Backup test skipped.")
        return
    
    # Test backup creation
    backup = await test_backup_creation(project_id, db_name)
    
    if backup:
        print(f"\n{'='*60}")
        print(f"✓ ALL TESTS PASSED!")
        print(f"{'='*60}")
        print(f"\nBackup file created: {backup['file_path']}")
        print(f"You can verify the backup content by decompressing it:")
        print(f"  gunzip -c {backup['file_path']} | head -n 50")
    else:
        print(f"\n{'='*60}")
        print(f"✗ TESTS FAILED")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
