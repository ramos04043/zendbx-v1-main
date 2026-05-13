"""Regenerate API keys for existing projects that have truncated keys"""
import asyncio
import asyncpg
import sys
sys.path.append('.')

from app.utils.jwt_keys import generate_project_keys
import hashlib

async def regenerate_keys():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='Pawan@121',
        database='nexora_main'
    )
    
    try:
        # Find all api_keys where encrypted_key is NULL
        rows = await conn.fetch("""
            SELECT DISTINCT project_id
            FROM api_keys
            WHERE encrypted_key IS NULL
            AND key_type IN ('anon', 'service_role')
        """)
        
        print(f"\nFound {len(rows)} projects with missing encrypted keys\n")
        
        for row in rows:
            project_id = row['project_id']
            print(f"Regenerating keys for project: {project_id}")
            
            # Generate new JWT keys
            jwt_secret, anon_key, service_role_key = generate_project_keys(str(project_id))
            
            # Update anon key
            anon_hash = hashlib.sha256(anon_key.encode()).hexdigest()
            anon_prefix = anon_key[:20] + "..."
            
            await conn.execute("""
                UPDATE api_keys
                SET encrypted_key = $1, key_hash = $2, key_prefix = $3
                WHERE project_id = $4 AND key_type = 'anon'
            """, anon_key, anon_hash, anon_prefix, project_id)
            
            # Update service_role key
            service_hash = hashlib.sha256(service_role_key.encode()).hexdigest()
            service_prefix = service_role_key[:20] + "..."
            
            await conn.execute("""
                UPDATE api_keys
                SET encrypted_key = $1, key_hash = $2, key_prefix = $3
                WHERE project_id = $4 AND key_type = 'service_role'
            """, service_role_key, service_hash, service_prefix, project_id)
            
            # Update project JWT secret
            await conn.execute("""
                UPDATE projects
                SET jwt_secret = $1
                WHERE id = $2
            """, jwt_secret, project_id)
            
            print(f"  ✓ Anon key: {anon_prefix}")
            print(f"  ✓ Service key: {service_prefix}")
            print()
        
        print(f"✓ Successfully regenerated keys for {len(rows)} projects!")
        print("\nIMPORTANT: Users will need to update their applications with the new keys.")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(regenerate_keys())
