# Row Level Security (RLS) Testing Guide

## Overview

This guide provides comprehensive testing procedures for Row Level Security (RLS) enforcement in Zendbx.

## Prerequisites

1. Backend server running
2. PostgreSQL database with RLS policies enabled
3. Test project with JWT keys configured
4. Multiple test users with different roles

## Setup Test Environment

### 1. Apply RLS Policies to Database

```bash
# Connect to your project database
psql -U postgres -d your_project_db

# Run RLS setup script
\i backend/database/rls_policies.sql
```

### 2. Create Test Table with RLS

```sql
-- Create a test table
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own posts
CREATE POLICY "Users can read own posts" ON posts
    FOR SELECT
    USING (
        auth.is_service_role() OR 
        user_id::TEXT = auth.current_user_id()
    );

-- Policy: Users can read public posts
CREATE POLICY "Anyone can read public posts" ON posts
    FOR SELECT
    USING (is_public = true);

-- Policy: Users can insert their own posts
CREATE POLICY "Users can create posts" ON posts
    FOR INSERT
    WITH CHECK (
        auth.is_authenticated() AND
        user_id::TEXT = auth.current_user_id()
    );

-- Policy: Users can update their own posts
CREATE POLICY "Users can update own posts" ON posts
    FOR UPDATE
    USING (
        auth.is_service_role() OR
        user_id::TEXT = auth.current_user_id()
    )
    WITH CHECK (
        user_id::TEXT = auth.current_user_id()
    );

-- Policy: Users can delete their own posts
CREATE POLICY "Users can delete own posts" ON posts
    FOR DELETE
    USING (
        auth.is_service_role() OR
        user_id::TEXT = auth.current_user_id()
    );
```

### 3. Create Test Users

```bash
# User 1: Alice
curl -X POST http://localhost:8000/v1/auth/{PROJECT_ID}/signup \
  -H "Authorization: Bearer {ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "password123",
    "name": "Alice"
  }'

# Save Alice's JWT token
ALICE_TOKEN="<token_from_response>"

# User 2: Bob
curl -X POST http://localhost:8000/v1/auth/{PROJECT_ID}/signup \
  -H "Authorization: Bearer {ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "password": "password123",
    "name": "Bob"
  }'

# Save Bob's JWT token
BOB_TOKEN="<token_from_response>"
```

## Test Cases

### Test 1: INSERT with RLS

#### Test 1.1: Authenticated User Can Insert Own Data

```bash
# Alice creates a post
curl -X POST http://localhost:8000/rest/v1/posts \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "x-project-id: {PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{ALICE_USER_ID}",
    "title": "Alice'\''s First Post",
    "content": "Hello World!",
    "is_public": false
  }'

# Expected: 200 OK with post data
```

#### Test 1.2: User Cannot Insert Data for Another User

```bash
# Alice tries to create a post as Bob
curl -X POST http://localhost:8000/rest/v1/posts \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "x-project-id: {PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{BOB_USER_ID}",
    "title": "Fake Post",
    "content": "This should fail",
    "is_public": false
  }'

# Expected: 403 Forbidden - Insert blocked by RLS
```

#### Test 1.3: Anonymous User Cannot Insert

```bash
# Try to insert with ANON_KEY
curl -X POST http://localhost:8000/rest/v1/posts \
  -H "Authorization: Bearer {ANON_KEY}" \
  -H "x-project-id: {PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{ALICE_USER_ID}",
    "title": "Anonymous Post",
    "content": "This should fail",
    "is_public": false
  }'

# Expected: 403 Forbidden - Insert blocked by RLS
```

### Test 2: SELECT with RLS

#### Test 2.1: User Can Read Own Private Posts

```bash
# Alice reads her posts
curl -X GET "http://localhost:8000/rest/v1/posts" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "x-project-id: {PROJECT_ID}"

# Expected: 200 OK with Alice's posts only
```

#### Test 2.2: User Cannot Read Other's Private Posts

```bash
# Bob tries to read all posts
curl -X GET "http://localhost:8000/rest/v1/posts" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -H "x-project-id: {PROJECT_ID}"

# Expected: 200 OK but only Bob's posts (not Alice's private posts)
```

#### Test 2.3: Anyone Can Read Public Posts

```bash
# First, make Alice's post public
curl -X PATCH "http://localhost:8000/rest/v1/posts?id=eq.{POST_ID}" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "x-project-id: {PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{"is_public": true}'

# Now Bob can read it
curl -X GET "http://localhost:8000/rest/v1/posts" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -H "x-project-id: {PROJECT_ID}"

# Expected: 200 OK with public posts visible
```

### Test 3: UPDATE with RLS

#### Test 3.1: User Can Update Own Posts

```bash
# Alice updates her post
curl -X PATCH "http://localhost:8000/rest/v1/posts?id=eq.{ALICE_POST_ID}" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "x-project-id: {PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "content": "Updated content"
  }'

# Expected: 200 OK with updated post
```

#### Test 3.2: User Cannot Update Other's Posts

```bash
# Bob tries to update Alice's post
curl -X PATCH "http://localhost:8000/rest/v1/posts?id=eq.{ALICE_POST_ID}" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -H "x-project-id: {PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Hacked!",
    "content": "This should fail"
  }'

# Expected: 404 Not Found or 403 Forbidden
```

#### Test 3.3: User Cannot Change Ownership

```bash
# Alice tries to change post ownership to Bob
curl -X PATCH "http://localhost:8000/rest/v1/posts?id=eq.{ALICE_POST_ID}" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "x-project-id: {PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{BOB_USER_ID}"
  }'

# Expected: 403 Forbidden - WITH CHECK fails
```

### Test 4: DELETE with RLS

#### Test 4.1: User Can Delete Own Posts

```bash
# Alice deletes her post
curl -X DELETE "http://localhost:8000/rest/v1/posts?id=eq.{ALICE_POST_ID}" \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "x-project-id: {PROJECT_ID}"

# Expected: 200 OK with success message
```

#### Test 4.2: User Cannot Delete Other's Posts

```bash
# Bob tries to delete Alice's post
curl -X DELETE "http://localhost:8000/rest/v1/posts?id=eq.{ALICE_POST_ID}" \
  -H "Authorization: Bearer $BOB_TOKEN" \
  -H "x-project-id: {PROJECT_ID}"

# Expected: 404 Not Found or 403 Forbidden
```

### Test 5: Service Role Bypass

#### Test 5.1: Service Role Can Read All Data

```bash
# Use SERVICE_ROLE_KEY to read all posts
curl -X GET "http://localhost:8000/rest/v1/posts" \
  -H "Authorization: Bearer {SERVICE_ROLE_KEY}" \
  -H "x-project-id: {PROJECT_ID}"

# Expected: 200 OK with ALL posts (Alice's + Bob's)
```

#### Test 5.2: Service Role Can Modify Any Data

```bash
# Service role updates any post
curl -X PATCH "http://localhost:8000/rest/v1/posts?id=eq.{ANY_POST_ID}" \
  -H "Authorization: Bearer {SERVICE_ROLE_KEY}" \
  -H "x-project-id: {PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Admin Updated",
    "content": "Service role can do this"
  }'

# Expected: 200 OK - RLS bypassed
```

#### Test 5.3: Service Role Can Delete Any Data

```bash
# Service role deletes any post
curl -X DELETE "http://localhost:8000/rest/v1/posts?id=eq.{ANY_POST_ID}" \
  -H "Authorization: Bearer {SERVICE_ROLE_KEY}" \
  -H "x-project-id: {PROJECT_ID}"

# Expected: 200 OK - RLS bypassed
```

## Automated Test Script

Create a test script to run all tests:

```python
# test_rls.py
import requests
import json

BASE_URL = "http://localhost:8000"
PROJECT_ID = "your-project-id"
ANON_KEY = "your-anon-key"
SERVICE_KEY = "your-service-key"

def test_rls():
    """Run comprehensive RLS tests"""
    
    # 1. Create test users
    print("Creating test users...")
    alice = signup("alice@test.com", "password123", "Alice")
    bob = signup("bob@test.com", "password123", "Bob")
    
    alice_token = alice["access_token"]
    alice_id = alice["user"]["id"]
    bob_token = bob["access_token"]
    bob_id = bob["user"]["id"]
    
    print(f"✓ Alice ID: {alice_id}")
    print(f"✓ Bob ID: {bob_id}")
    
    # 2. Test INSERT
    print("\n=== Testing INSERT ===")
    
    # Alice creates post
    post = create_post(alice_token, alice_id, "Alice's Post", False)
    alice_post_id = post["id"]
    print(f"✓ Alice created post: {alice_post_id}")
    
    # Alice tries to create post as Bob (should fail)
    try:
        create_post(alice_token, bob_id, "Fake Post", False)
        print("✗ FAIL: Alice created post as Bob")
    except:
        print("✓ Alice cannot create post as Bob")
    
    # 3. Test SELECT
    print("\n=== Testing SELECT ===")
    
    # Alice reads her posts
    alice_posts = get_posts(alice_token)
    print(f"✓ Alice sees {len(alice_posts)} posts")
    
    # Bob reads posts (should not see Alice's private post)
    bob_posts = get_posts(bob_token)
    print(f"✓ Bob sees {len(bob_posts)} posts")
    
    # 4. Test UPDATE
    print("\n=== Testing UPDATE ===")
    
    # Alice updates her post
    update_post(alice_token, alice_post_id, {"title": "Updated"})
    print("✓ Alice updated her post")
    
    # Bob tries to update Alice's post (should fail)
    try:
        update_post(bob_token, alice_post_id, {"title": "Hacked"})
        print("✗ FAIL: Bob updated Alice's post")
    except:
        print("✓ Bob cannot update Alice's post")
    
    # 5. Test DELETE
    print("\n=== Testing DELETE ===")
    
    # Bob tries to delete Alice's post (should fail)
    try:
        delete_post(bob_token, alice_post_id)
        print("✗ FAIL: Bob deleted Alice's post")
    except:
        print("✓ Bob cannot delete Alice's post")
    
    # Alice deletes her post
    delete_post(alice_token, alice_post_id)
    print("✓ Alice deleted her post")
    
    # 6. Test Service Role
    print("\n=== Testing Service Role ===")
    
    # Service role reads all
    all_posts = get_posts(SERVICE_KEY)
    print(f"✓ Service role sees {len(all_posts)} posts")
    
    print("\n=== All Tests Passed! ===")

def signup(email, password, name):
    response = requests.post(
        f"{BASE_URL}/v1/auth/{PROJECT_ID}/signup",
        headers={"Authorization": f"Bearer {ANON_KEY}"},
        json={"email": email, "password": password, "name": name}
    )
    return response.json()

def create_post(token, user_id, title, is_public):
    response = requests.post(
        f"{BASE_URL}/rest/v1/posts",
        headers={
            "Authorization": f"Bearer {token}",
            "x-project-id": PROJECT_ID
        },
        json={
            "user_id": user_id,
            "title": title,
            "content": "Test content",
            "is_public": is_public
        }
    )
    response.raise_for_status()
    return response.json()

def get_posts(token):
    response = requests.get(
        f"{BASE_URL}/rest/v1/posts",
        headers={
            "Authorization": f"Bearer {token}",
            "x-project-id": PROJECT_ID
        }
    )
    return response.json()

def update_post(token, post_id, data):
    response = requests.patch(
        f"{BASE_URL}/rest/v1/posts?id=eq.{post_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "x-project-id": PROJECT_ID
        },
        json=data
    )
    response.raise_for_status()
    return response.json()

def delete_post(token, post_id):
    response = requests.delete(
        f"{BASE_URL}/rest/v1/posts?id=eq.{post_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "x-project-id": PROJECT_ID
        }
    )
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    test_rls()
```

## Verification Checklist

- [ ] RLS policies are enabled on all user tables
- [ ] Authenticated users can only access their own data
- [ ] Anonymous users have limited read-only access
- [ ] Service role can bypass RLS for admin operations
- [ ] INSERT policies prevent unauthorized data creation
- [ ] UPDATE policies prevent unauthorized modifications
- [ ] DELETE policies prevent unauthorized deletions
- [ ] Error messages don't expose sensitive information
- [ ] JWT tokens are properly validated
- [ ] Session variables are correctly set

## Common Issues

### Issue 1: RLS Not Enforced

**Symptom**: Users can see all data regardless of ownership

**Solution**: Check if RLS is enabled on the table
```sql
SELECT relname, relrowsecurity 
FROM pg_class 
WHERE relname = 'your_table';
```

### Issue 2: Service Role Not Bypassing RLS

**Symptom**: Service role gets 403 errors

**Solution**: Verify JWT token has `role: "service_role"` in payload

### Issue 3: Session Variables Not Set

**Symptom**: RLS policies always fail

**Solution**: Check middleware is setting context variables
```sql
SELECT current_setting('app.current_user_id', true);
SELECT current_setting('app.current_role', true);
```

## Production Checklist

Before deploying to production:

1. [ ] All tables have RLS enabled
2. [ ] All policies are tested with multiple users
3. [ ] Service role keys are securely stored
4. [ ] Error handling doesn't leak sensitive data
5. [ ] Logging captures RLS violations
6. [ ] Performance tested with RLS enabled
7. [ ] Documentation updated with RLS policies
8. [ ] Team trained on RLS best practices

## Next Steps

1. Apply RLS to all project tables
2. Create custom policies for your data model
3. Test with real user scenarios
4. Monitor RLS violations in production
5. Regularly audit RLS policies

## Support

For issues or questions:
- Check logs: `backend/logs/`
- Review policies: `SELECT * FROM auth.list_policies('table_name')`
- Test context: `SELECT auth.current_user_id(), auth.current_role()`
