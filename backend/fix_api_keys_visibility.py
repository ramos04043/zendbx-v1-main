"""
Fix API Keys Visibility - Populate encrypted_key column
This script checks if encrypted_key is NULL and populates it with the full JWT
"""

import psycopg2
import sys

def fix_api_keys():
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="nexora_main",
            user="postgres",
            password="Pawan@121"
        )
        cursor = conn.cursor()
        
        # Check current state
        cursor.execute("""
            SELECT id, name, key_type, key_prefix, encrypted_key, 
                   LENGTH(key_prefix) as prefix_len,
                   LENGTH(encrypted_key) as encrypted_len
            FROM api_keys
            WHERE key_type IN ('anon', 'service_role')
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        
        print("=" * 80)
        print("CURRENT API KEYS STATE")
        print("=" * 80)
        
        if not rows:
            print("\n❌ No anon or service_role keys found!")
            print("   Please create a project first.")
            cursor.close()
            conn.close()
            return
        
        needs_fix = []
        
        for row in rows:
            key_id, name, key_type, key_prefix, encrypted_key, prefix_len, encrypted_len = row
            
            print(f"\nKey: {name} ({key_type})")
            print(f"  ID: {key_id}")
            print(f"  key_prefix length: {prefix_len}")
            print(f"  encrypted_key length: {encrypted_len if encrypted_len else 'NULL'}")
            
            # Check if encrypted_key is NULL or empty
            if not encrypted_key or len(encrypted_key) < 50:
                print(f"  ⚠️  ISSUE: encrypted_key is {'NULL' if not encrypted_key else 'too short'}")
                needs_fix.append((key_id, name, key_type, key_prefix))
            else:
                print(f"  ✅ OK: Full key is stored")
        
        if not needs_fix:
            print("\n" + "=" * 80)
            print("✅ ALL KEYS ARE PROPERLY STORED!")
            print("=" * 80)
            cursor.close()
            conn.close()
            return
        
        print("\n" + "=" * 80)
        print(f"FOUND {len(needs_fix)} KEYS THAT NEED FIXING")
        print("=" * 80)
        
        # The issue: key_prefix might be truncated, but we need the full JWT
        # Solution: If encrypted_key is NULL, we need to regenerate the keys
        
        print("\n⚠️  WARNING: encrypted_key is NULL for some keys.")
        print("   This means the full JWT tokens were not stored during project creation.")
        print("\n   SOLUTION:")
        print("   1. The keys need to be regenerated (old keys will stop working)")
        print("   2. OR manually update encrypted_key with the full JWT from your records")
        print("\n   For now, let's check if key_prefix contains the full JWT...")
        
        for key_id, name, key_type, key_prefix in needs_fix:
            print(f"\n   Checking {name}:")
            print(f"   key_prefix: {key_prefix[:50]}...")
            
            # Check if key_prefix is actually a full JWT (starts with eyJ)
            if key_prefix and key_prefix.startswith('eyJ') and len(key_prefix) > 100:
                print(f"   ✅ key_prefix contains full JWT! Copying to encrypted_key...")
                
                cursor.execute("""
                    UPDATE api_keys
                    SET encrypted_key = key_prefix
                    WHERE id = %s
                """, (key_id,))
                
                print(f"   ✅ FIXED: encrypted_key updated for {name}")
            else:
                print(f"   ❌ key_prefix is truncated. Keys need regeneration.")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print("VERIFICATION - Checking again...")
        print("=" * 80)
        
        cursor.execute("""
            SELECT id, name, key_type, 
                   LENGTH(key_prefix) as prefix_len,
                   LENGTH(encrypted_key) as encrypted_len
            FROM api_keys
            WHERE key_type IN ('anon', 'service_role')
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        all_good = True
        
        for row in rows:
            key_id, name, key_type, prefix_len, encrypted_len = row
            print(f"\n{name} ({key_type}):")
            print(f"  key_prefix: {prefix_len} chars")
            print(f"  encrypted_key: {encrypted_len if encrypted_len else 'NULL'} chars")
            
            if not encrypted_len or encrypted_len < 50:
                print(f"  ❌ STILL BROKEN")
                all_good = False
            else:
                print(f"  ✅ FIXED")
        
        if all_good:
            print("\n" + "=" * 80)
            print("🎉 ALL KEYS ARE NOW PROPERLY STORED!")
            print("=" * 80)
            print("\nRefresh your browser to see the full keys.")
        else:
            print("\n" + "=" * 80)
            print("⚠️  SOME KEYS STILL NEED MANUAL FIX")
            print("=" * 80)
            print("\nYou may need to regenerate keys for affected projects.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("\n🔧 ZenDBX API Keys Visibility Fix")
    print("=" * 80)
    fix_api_keys()
