"""
Script to upgrade a user to Pro plan
Usage: python upgrade_user_to_pro.py <email>
"""

import asyncio
import sys
from app.core.database import execute_on_main_db

async def upgrade_user_to_pro(email: str):
    """Upgrade user to Pro plan"""
    
    print(f"🔍 Looking for user: {email}")
    
    # Check if user exists
    user = await execute_on_main_db(
        "SELECT id, email, full_name, plan FROM users WHERE email = $1",
        email
    )
    
    if not user:
        print(f"❌ User not found: {email}")
        return False
    
    user_data = dict(user[0])
    print(f"✅ Found user: {user_data['full_name']} ({user_data['email']})")
    print(f"📊 Current plan: {user_data['plan']}")
    
    # Update to Pro plan
    await execute_on_main_db(
        "UPDATE users SET plan = $1, updated_at = NOW() WHERE email = $2",
        "pro",
        email
    )
    
    print(f"✅ Successfully upgraded {email} to Pro plan!")
    
    # Verify update
    updated_user = await execute_on_main_db(
        "SELECT plan FROM users WHERE email = $1",
        email
    )
    
    if updated_user:
        new_plan = dict(updated_user[0])['plan']
        print(f"✅ Verified: New plan is '{new_plan}'")
    
    return True

async def main():
    if len(sys.argv) < 2:
        print("Usage: python upgrade_user_to_pro.py <email>")
        print("Example: python upgrade_user_to_pro.py ramos@madrid.com")
        sys.exit(1)
    
    email = sys.argv[1]
    
    try:
        success = await upgrade_user_to_pro(email)
        if success:
            print("\n🎉 User upgrade completed successfully!")
        else:
            print("\n❌ User upgrade failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
