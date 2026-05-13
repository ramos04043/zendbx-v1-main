# ZenDBX Complete Workflow Guide
## From Signup to Production - How Everything Works

---

## 📋 Table of Contents
1. [User Onboarding Flow](#user-onboarding-flow)
2. [Project Creation Process](#project-creation-process)
3. [Database Architecture](#database-architecture)
4. [API Key Generation](#api-key-generation)
5. [Data Management](#data-management)
6. [Authentication System](#authentication-system)
7. [Real-time Features](#real-time-features)
8. [Complete User Journey](#complete-user-journey)

---

## 1. User Onboarding Flow

### Step 1: User Registration
```
User visits → /signup
↓
Enters: Email, Password, Full Name
↓
Backend: POST /api/auth/signup
↓
Actions:
1. Hash password using bcrypt
2. Create user record in main database
3. Generate JWT token with user_id, email, role
4. Return token + user data
↓
Frontend: Store token in localStorage
↓
Redirect to /dashboard
```

**Database Changes:**
```sql
-- Main database: users table
INSERT INTO users (email, password_hash, full_name, role, plan)
VALUES ('user@example.com', '$2b$12$...', 'John Doe', 'user', 'free');
```

### Step 2: First Login Check
```
Dashboard loads → useEffect runs
↓
Check: Does user have projects?
↓
Query: GET /api/projects
↓
If projects.length === 0:
  → Redirect to /onboarding
Else:
  → Load dashboard with first project
```

---

## 2. Project Creation Process

### Phase 1: User Creates Project (Onboarding)
```
User at /onboarding
↓
Enters: Project Name (e.g., "My App")
↓
Frontend: POST /api/projects
Body: { name: "My App", description: "..." }
Headers: { Authorization: "Bearer <token>" }
```

### Phase 2: Backend Project Creation
```python
# backend/app/api/projects.py

1. Validate user authentication (JWT token)
2. Generate unique project_id (UUID)
3. Generate project_slug from name ("my-app")
4. Create project record in main database
5. Create dedicated PostgreSQL database for project
6. Initialize project database with template schema
7. Generate API keys (anon_key, service_key)
8. Set up Row Level Security (RLS) policies
9. Return project data to frontend
```

**Detailed Backend Steps:**

#### Step 2.1: Create Project Record
```sql
-- Main database: projects table
INSERT INTO projects (
  id, 
  user_id, 
  name, 
  slug, 
  database_url,
  status
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  '<user_id>',
  'My App',
  'my-app',
  'postgresql://localhost:5432/zendbx_project_550e8400',
  'active'
);
```

#### Step 2.2: Create Dedicated Database
```python
# backend/app/services/db_manager.py

async def create_project_database(project_id: UUID):
    # 1. Create new PostgreSQL database
    await execute_sql(f"CREATE DATABASE zendbx_project_{project_id}")
    
    # 2. Connect to new database
    conn = await connect_to_db(f"zendbx_project_{project_id}")
    
    # 3. Run template schema
    await execute_schema_file("project_database_template.sql")
```

#### Step 2.3: Initialize Project Schema
```sql
-- backend/database/project_database_template.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create auth schema for project users
CREATE SCHEMA IF NOT EXISTS auth;

-- Create auth.users table (project-specific users)
CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    encrypted_password TEXT,
    email_confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create public schema for user data
CREATE SCHEMA IF NOT EXISTS public;

-- Enable Row Level Security
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view own data"
    ON auth.users FOR SELECT
    USING (auth.uid() = id);
```

#### Step 2.4: Generate API Keys
```python
# backend/app/utils/jwt_keys.py

async def generate_project_keys(project_id: UUID):
    # Generate JWT secret for this project
    jwt_secret = secrets.token_urlsafe(32)
    
    # Create anon key (public, limited permissions)
    anon_key = create_jwt({
        "role": "anon",
        "project_id": str(project_id)
    }, jwt_secret)
    
    # Create service key (private, full permissions)
    service_key = create_jwt({
        "role": "service_role",
        "project_id": str(project_id)
    }, jwt_secret)
    
    # Store encrypted keys in database
    await store_keys(project_id, anon_key, service_key, jwt_secret)
    
    return {
        "anon_key": anon_key,
        "service_key": service_key
    }
```

#### Step 2.5: Store Keys in Database
```sql
-- Main database: project_keys table
INSERT INTO project_keys (
    project_id,
    anon_key_encrypted,
    service_key_encrypted,
    jwt_secret_encrypted
) VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    '<encrypted_anon_key>',
    '<encrypted_service_key>',
    '<encrypted_jwt_secret>'
);
```

### Phase 3: Frontend Receives Project
```javascript
// Response from POST /api/projects
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My App",
  "slug": "my-app",
  "database_url": "postgresql://...",
  "anon_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "service_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "created_at": "2024-03-30T10:00:00Z"
}

// Frontend stores project_id
localStorage.setItem('current_project_id', project.id);

// Redirect to dashboard
router.push('/dashboard');
```

---

## 3. Database Architecture

### Multi-Tenant Architecture

```
┌─────────────────────────────────────────┐
│         Main Database (zendbx)          │
│  - users (platform users)               │
│  - projects (all projects)              │
│  - project_keys (API keys)              │
│  - sessions (user sessions)             │
│  - audit_logs (activity tracking)       │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┬───────────┐
        ↓                       ↓           ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Project DB #1    │  │ Project DB #2    │  │ Project DB #3    │
│ zendbx_project_  │  │ zendbx_project_  │  │ zendbx_project_  │
│ 550e8400...      │  │ 660e9500...      │  │ 770ea600...      │
│                  │  │                  │  │                  │
│ - auth.users     │  │ - auth.users     │  │ - auth.users     │
│ - public.posts   │  │ - public.orders  │  │ - public.tasks   │
│ - public.comments│  │ - public.products│  │ - public.notes   │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

### Connection Pooling
```python
# backend/app/core/db_router.py

# Main database pool
main_pool = await asyncpg.create_pool(MAIN_DATABASE_URL)

# Project database pools (cached)
project_pools = {}

async def get_project_pool(project_id: UUID):
    if project_id not in project_pools:
        # Create new pool for this project
        project_pools[project_id] = await asyncpg.create_pool(
            f"postgresql://localhost:5432/zendbx_project_{project_id}"
        )
    return project_pools[project_id]
```

---

## 4. API Key Generation & Usage

### Key Types

1. **Anon Key** (Public)
   - Used in frontend applications
   - Limited to RLS-protected operations
   - Can only access data user has permission for

2. **Service Key** (Private)
   - Used in backend/server applications
   - Bypasses RLS policies
   - Full database access

### How Keys Work

```javascript
// Frontend: Using anon key
const { data, error } = await fetch('https://api.zendbx.com/rest/v1/posts', {
  headers: {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',  // anon_key
    'Authorization': 'Bearer <user_jwt_token>'
  }
});

// Backend processes request:
// 1. Validate apikey → extract project_id
// 2. Connect to project database
// 3. Validate user JWT token
// 4. Set RLS context: SET LOCAL jwt.claims.sub = '<user_id>'
// 5. Execute query (RLS automatically filters results)
// 6. Return data
```

### RLS (Row Level Security) in Action

```sql
-- Example: Posts table with RLS
CREATE TABLE public.posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    title TEXT,
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own posts
CREATE POLICY "Users can view own posts"
    ON public.posts FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own posts
CREATE POLICY "Users can insert own posts"
    ON public.posts FOR INSERT
    WITH CHECK (auth.uid() = user_id);
```

When user queries:
```sql
-- User sends: SELECT * FROM posts;
-- RLS automatically converts to:
SELECT * FROM posts WHERE user_id = '<current_user_id>';
```

---

## 5. Data Management

### Creating Tables

#### Option 1: SQL Editor
```
User goes to /dashboard/sql-editor
↓
Writes SQL:
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    price DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
↓
Click "Run Query"
↓
Backend: POST /api/projects/{project_id}/queries
↓
Execute on project database
↓
Return results
```

#### Option 2: AI Builder
```
User goes to /dashboard/ai-builder
↓
Describes in natural language:
"Create a products table with name, price, and description"
↓
Frontend: POST /api/ai/generate-schema
↓
AI generates SQL schema
↓
User reviews and approves
↓
Execute SQL on project database
```

#### Option 3: CSV Import
```
User goes to /dashboard/import
↓
Uploads CSV file
↓
Frontend: POST /api/projects/{project_id}/import
↓
Backend:
1. Parse CSV
2. Infer column types
3. Create table automatically
4. Insert data
5. Return success
```

### Inserting Data

#### Via REST API
```javascript
// Using anon_key
POST https://api.zendbx.com/rest/v1/products
Headers: {
  'apikey': '<anon_key>',
  'Authorization': 'Bearer <user_token>',
  'Content-Type': 'application/json'
}
Body: {
  "name": "iPhone 15",
  "price": 999.99,
  "description": "Latest iPhone"
}

// Backend:
// 1. Validate keys
// 2. Connect to project DB
// 3. INSERT INTO products ...
// 4. Return inserted row
```

---

## 6. Authentication System

### Project-Level Authentication

Each project has its own auth system:

```
Project Database
└── auth.users (project-specific users)
    ├── User 1 (app user, not platform user)
    ├── User 2
    └── User 3
```

### Sign Up Flow (Project Users)

```javascript
// Frontend app using ZenDBX
POST https://api.zendbx.com/auth/v2/signup
Headers: {
  'apikey': '<anon_key>'
}
Body: {
  "email": "customer@example.com",
  "password": "password123"
}

// Backend:
// 1. Validate anon_key → get project_id
// 2. Connect to project database
// 3. Hash password
// 4. INSERT INTO auth.users ...
// 5. Generate JWT token for this user
// 6. Return token
```

### Login Flow (Project Users)

```javascript
POST https://api.zendbx.com/auth/v2/login
Headers: {
  'apikey': '<anon_key>'
}
Body: {
  "email": "customer@example.com",
  "password": "password123"
}

// Backend:
// 1. Validate anon_key
// 2. Query auth.users in project DB
// 3. Verify password
// 4. Generate JWT with user_id
// 5. Return token
```

---

## 7. Real-time Features

### WebSocket Connection

```javascript
// Frontend
const ws = new WebSocket('ws://localhost:3001');

// Subscribe to table changes
ws.send(JSON.stringify({
  event: 'subscribe',
  channel: 'public:posts',
  apikey: '<anon_key>'
}));

// Receive real-time updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New post:', data);
};
```

### Backend Real-time Listener

```python
# backend/app/services/realtime_listener.py

# Listen to PostgreSQL NOTIFY events
async def listen_to_changes(project_id):
    conn = await get_project_connection(project_id)
    
    # Listen to all table changes
    await conn.execute("LISTEN table_changes")
    
    async for notification in conn.notifications():
        # Forward to WebSocket server
        await websocket_client.broadcast({
            'table': notification.payload['table'],
            'action': notification.payload['action'],
            'data': notification.payload['data']
        })
```

### Database Triggers

```sql
-- Trigger function to notify on changes
CREATE OR REPLACE FUNCTION notify_table_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'table_changes',
        json_build_object(
            'table', TG_TABLE_NAME,
            'action', TG_OP,
            'data', row_to_json(NEW)
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to table
CREATE TRIGGER posts_notify
AFTER INSERT OR UPDATE OR DELETE ON public.posts
FOR EACH ROW EXECUTE FUNCTION notify_table_change();
```

---

## 8. Complete User Journey

### Scenario: Building a Blog App

#### Step 1: Platform Setup
```
1. User signs up on ZenDBX → /signup
2. Creates account → stored in main database
3. Logs in → receives JWT token
4. Redirected to /onboarding (no projects yet)
```

#### Step 2: Create Project
```
5. User creates project "My Blog"
6. Backend creates:
   - Project record in main DB
   - Dedicated database: zendbx_project_abc123
   - API keys (anon_key, service_key)
   - Initial schema (auth.users table)
7. User redirected to /dashboard
```

#### Step 3: Design Database
```
8. User goes to SQL Editor
9. Creates tables:
   - posts (id, title, content, author_id, created_at)
   - comments (id, post_id, user_id, content, created_at)
10. Enables RLS on both tables
11. Creates policies for user access
```

#### Step 4: Add Sample Data
```
12. User goes to /dashboard/import
13. Uploads posts.csv
14. Backend creates table and imports data
15. User sees data in /dashboard/tables
```

#### Step 5: Get API Keys
```
16. User goes to /dashboard/api-keys
17. Copies anon_key and service_key
18. Views API documentation
```

#### Step 6: Build Frontend App
```javascript
// User's React app
import { createClient } from '@supabase/supabase-js'

const zendbx = createClient(
  'https://api.zendbx.com',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' // anon_key
)

// Fetch posts
const { data: posts } = await zendbx
  .from('posts')
  .select('*')
  .order('created_at', { ascending: false })

// Insert post
const { data, error } = await zendbx
  .from('posts')
  .insert({
    title: 'My First Post',
    content: 'Hello World!'
  })
```

#### Step 7: Add Authentication
```javascript
// Sign up new user (in project database)
const { data, error } = await zendbx.auth.signUp({
  email: 'user@example.com',
  password: 'password123'
})

// Login
const { data, error } = await zendbx.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
})

// Now all queries are scoped to this user via RLS
```

#### Step 8: Real-time Updates
```javascript
// Subscribe to new posts
const subscription = zendbx
  .channel('public:posts')
  .on('postgres_changes', 
    { event: 'INSERT', schema: 'public', table: 'posts' },
    (payload) => {
      console.log('New post!', payload.new)
    }
  )
  .subscribe()
```

#### Step 9: Monitor & Scale
```
19. User checks /dashboard for metrics:
    - API request count
    - Database size
    - Active users
    - Storage usage
20. User invites team members via /dashboard/team
21. User creates backups via /dashboard/backups
22. User upgrades plan for more resources
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User's Frontend App                      │
│                  (React, Vue, Next.js, etc.)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/WebSocket
                         │ Headers: apikey, Authorization
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                      ZenDBX Platform                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   FastAPI    │  │  WebSocket   │  │   Frontend   │     │
│  │   Backend    │  │    Server    │  │  Dashboard   │     │
│  │  (Port 8000) │  │  (Port 3001) │  │ (Port 3000)  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘     │
│         │                  │                                 │
│         │                  │                                 │
│  ┌──────┴──────────────────┴─────────────────────────┐     │
│  │           Connection Pool Manager                  │     │
│  │  - Main DB Pool                                    │     │
│  │  - Project DB Pools (cached)                       │     │
│  │  - RLS Context Management                          │     │
│  └──────┬─────────────────────────────────────────────┘     │
└─────────┼─────────────────────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Server                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Main Database (zendbx)                              │  │
│  │  - users, projects, project_keys, sessions, etc.     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Project Database #1 (zendbx_project_abc123)         │  │
│  │  - auth.users, public.posts, public.comments         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Project Database #2 (zendbx_project_def456)         │  │
│  │  - auth.users, public.products, public.orders        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

1. **Multi-Tenant**: Each project gets its own isolated PostgreSQL database
2. **Secure**: API keys + JWT tokens + RLS policies protect data
3. **Real-time**: WebSocket + PostgreSQL NOTIFY for live updates
4. **Flexible**: SQL editor, AI builder, CSV import for data management
5. **Scalable**: Connection pooling, separate databases, resource limits
6. **Complete**: Authentication, authorization, real-time, backups, team collaboration

This is how ZenDBX works from start to finish!
