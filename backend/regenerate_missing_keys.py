"""
Regenerate API Keys for projects with NULL encrypted_key
This will generate new JWT tokens for affected projects
"""

import psycopg2
import sys
from app.utils.jwt_keys import generate_project_keys
import hashlib

def regenerate_keys():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="nexora_main",
            user="postgres",
            password="Pawan@121"
        )
        cursor = conn.cursor()
        
        # Find projects with NULL encrypted_key
        cursor.execute("""
            SELECT DISTINCT project_id
            FROM api_keys
            WHERE key_type IN ('anon', 'service_role')
            AND (encrypted_key IS NULL OR LENGTH(encrypted_key) < 50)
        """)
        
        project_ids = [row[0] for row in cursor.fetchall()]
        
        if not project_ids:
            print("✅ No projects need key regeneration!")
            cursor.close()
            conn.close()
            return
        
        print(f"\n🔧 Found {len(project_ids)} projects that need new keys")
        print("=" * 80)
        
        for project_id in project_ids:
            print(f"\nRegenerating keys for project: {project_id}")
            
            # Generate new keys
            jwt_secret, anon_key, service_role_key = generate_project_keys(str(project_id))
            
            print(f"  ✓ Generated new JWT secret")
            print(f"  ✓ Generated new anon key ({len(anon_key)} chars)")
            print(f"  ✓ Generated new service_role key ({len(service_role_key)} chars)")
            
            # Update anon key
            cursor.execute("""
                UPDATE api_keys
                SET encrypted_key = %s,
                    key_prefix = %s,
                    key_hash = %s
                WHERE project_id = %s AND key_type = 'anon'
            """, (
                anon_key,
                anon_key[:20] + '...',
                hashlib.sha256(anon_key.encode()).hexdigest(),
                project_id
            ))
            
            # Update service_role key
            cursor.execute("""
                UPDATE api_keys
                SET encrypted_key = %s,
                    key_prefix = %s,
                    key_hash = %s
                WHERE project_id = %s AND key_type = 'service_role'
            """, (
                service_role_key,
                service_role_key[:20] + '...',
                hashlib.sha256(service_role_key.encode()).hexdigest(),
                project_id
            ))
            
            # Update JWT secret in projects table
            cursor.execute("""
                UPDATE projects
                SET jwt_secret = %s
                WHERE id = %s
            """, (jwt_secret, project_id))
            
            print(f"  ✅ Keys updated in database")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("🎉 ALL KEYS REGENERATED SUCCESSFULLY!")
        print("=" * 80)
        print("\n⚠️  IMPORTANT:")
        print("  - Old API keys will NO LONGER WORK")
        print("  - Users need to copy the NEW keys from the dashboard")
        print("  - Refresh the browser to see the new keys")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("\n🔑 ZenDBX API Keys Regeneration")
    print("=" * 80)
    print("\n⚠️  WARNING: This will generate NEW keys for affected projects.")
    print("   Old keys will stop working!")
    print("\nPress ENTER to continue or Ctrl+C to cancel...")
    input()
    
    regenerate_keys()
