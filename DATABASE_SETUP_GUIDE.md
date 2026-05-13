# PostgreSQL Database Setup - Supabase Architecture

## 🏗️ Architecture Overview

We use **exactly the same architecture as Supabase**:

### 1. Main Database (Control Plane)
- **Database Name**: `nexora_main`
- **Purpose**: Store platform metadata
- **Contains**:
  - User accounts
  - Project metadata
  - Query history
  - API keys
  - Saved queries

### 2. Project Databases (Data Plane)
- **Created Dynamically**: When user creates a project
- **Naming**: `proj_abc123`, `proj_def456`, etc.
- **Purpose**: Store user's actual data (tables they create)
- **Isolation**: Each project = separate database (complete isolation)

---

## 📝 Step-by-Step Setup

### Step 1: Verify PostgreSQL Installation

1. **Open pgAdmin 4**
2. **Check PostgreSQL is running**:
   - You should see "PostgreSQL 15" (or your version) in the left sidebar
   - If not running, start it from Windows Services

### Step 2: Create Main Database

1. **In pgAdmin**:
   - Right-click on "Databases"
   - Select "Create" → "Database..."
   
2. **Database Settings**:
   - **Database name**: `nexora_main`
   - **Owner**: postgres
   - **Encoding**: UTF8
   - Click "Save"

### Step 3: Initialize Database Schema

1. **Open Query Tool**:
   - Right-click on `nexora_main` database
   - Select "Query Tool"

2. **Load SQL Script**:
   - Click "Open File" icon (folder icon)
   - Navigate to: `backend/database/init_main_database.sql`
   - Click "Open"

3. **Execute Script**:
   - Click "Execute" button (▶ or F5)
   - Wait for completion
   - You should see: "Main database setup completed successfully!"

4. **Verify Tables Created**:
   - Expand `nexora_main` → Schemas → public → Tables
   - You should see 8 tables:
     - users
     - projects
     - user_tables
     - query_history
     - saved_queries
     - api_keys
     - file_uploads
     - project_quotas

### Step 4: Configure Backend Connection

Your `.env` file is already configured with:
```env
DATABASE_URL=postgresql://postgres:Pawan@!21@localhost:5432/nexora_main
```

This connects to your main database.

### Step 5: Test Database Connection

Run this command:
```bash
cd backend
python -c "import asyncio; import asyncpg; asyncio.run(asyncpg.connect('postgresql://postgres:Pawan@!21@localhost:5432/nexora_main').close()); print('✓ Connected successfully!')"
```

If successful, you'll see: `✓ Connected successfully!`

---

## 🔄 How It Works (Supabase-Style)

### When User Creates a Project:

1. **User Action**: Clicks "New Project" → Enters name "Sales Analytics"

2. **Backend Process**:
```python
# 1. Generate unique database name
db_name = "proj_abc123"

# 2. Create new PostgreSQL database
CREATE DATABASE proj_abc123;

# 3. Store metadata in main database
INSERT INTO projects (user_id, name, database_name)
VALUES (user_id, 'Sales Analytics', 'proj_abc123');

# 4. Initialize project database with extensions
\c proj_abc123
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
```

3. **Result**: User now has their own isolated database!

### When User Creates a Table:

1. **User Action**: In Table Editor → "Create Table" → Define columns

2. **Backend Process**:
```python
# 1. Get project's database name
project = get_project(project_id)
db_name = project.database_name  # "proj_abc123"

# 2. Connect to project database
conn = connect_to_database(db_name)

# 3. Create table in project database
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

# 4. Store metadata in main database
INSERT INTO user_tables (project_id, table_name, schema_definition)
VALUES (project_id, 'customers', schema_json);
```

### When User Queries Data:

1. **User Action**: SQL Editor → Write query → Execute

2. **Backend Process**:
```python
# 1. Get project's database
project = get_project(project_id)
db_name = project.database_name

# 2. Validate SQL (security)
if not is_safe_query(sql):
    raise SecurityError("Unsafe query")

# 3. Connect to project database
conn = connect_to_database(db_name)

# 4. Execute query
results = conn.fetch(sql)

# 5. Log in main database
log_query(user_id, project_id, sql, results)
```

---

## 🔐 Security & Isolation

### Database-Level Isolation
- Each project has its own PostgreSQL database
- User A cannot access User B's data
- PostgreSQL enforces this at the database level

### SQL Injection Prevention
```python
# Validate queries before execution
dangerous_keywords = ['DROP DATABASE', 'CREATE USER', 'GRANT', 'REVOKE']
if any(keyword in sql.upper() for keyword in dangerous_keywords):
    raise SecurityError("Dangerous operation not allowed")
```

### Connection Pooling
```python
# Efficient connection management
connection_pools = {}

def get_connection(db_name):
    if db_name not in connection_pools:
        connection_pools[db_name] = create_pool(
            database=db_name,
            min_size=2,
            max_size=10
        )
    return connection_pools[db_name].acquire()
```

---

## 📊 Database Structure

### Main Database Tables

**users**
```sql
- id (UUID)
- email (VARCHAR)
- password_hash (VARCHAR)
- full_name (VARCHAR)
- plan (VARCHAR) -- free, pro, enterprise
- created_at (TIMESTAMPTZ)
```

**projects**
```sql
- id (UUID)
- user_id (UUID) → users(id)
- name (VARCHAR)
- database_name (VARCHAR) -- "proj_abc123"
- status (VARCHAR) -- active, paused, deleted
- created_at (TIMESTAMPTZ)
```

**user_tables** (metadata)
```sql
- id (UUID)
- project_id (UUID) → projects(id)
- table_name (VARCHAR)
- schema_definition (JSONB)
- row_count (INTEGER)
- created_at (TIMESTAMPTZ)
```

**query_history**
```sql
- id (UUID)
- user_id (UUID) → users(id)
- project_id (UUID) → projects(id)
- question (TEXT) -- Natural language question
- sql_query (TEXT)
- status (VARCHAR) -- success, failed
- execution_time_ms (INTEGER)
- rows_returned (INTEGER)
- created_at (TIMESTAMPTZ)
```

---

## 🚀 Testing Your Setup

### 1. Check Main Database
```sql
-- In pgAdmin Query Tool (nexora_main)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Should show 8 tables
```

### 2. Test Backend Connection
```bash
cd backend
python test_setup.py
```

Expected output:
```
✓ FastAPI installed
✓ asyncpg installed
✓ Connected to database
✓ Found 8 tables in database
```

### 3. Start Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Visit: http://localhost:8000/docs

### 4. Create First User (API Test)
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456",
    "full_name": "Test User"
  }'
```

### 5. Create First Project (Creates New Database!)
```bash
# Use the access_token from signup response
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "My First Project",
    "description": "Testing Nexora AI"
  }'
```

**This will create a new PostgreSQL database!**

Check in pgAdmin:
- Refresh "Databases"
- You should see a new database: `proj_abc123` (or similar)

---

## 🎯 Advantages of This Architecture

### 1. Complete Data Isolation
- Each project = separate database
- No risk of data leakage between projects
- Easy to backup/restore individual projects

### 2. Scalability
- Can distribute project databases across multiple servers
- Each database can be optimized independently
- Easy to implement sharding

### 3. Security
- Database-level access control
- PostgreSQL enforces isolation
- No application-level security bugs can leak data

### 4. Flexibility
- Users can use any PostgreSQL features
- Can grant direct database access if needed
- Easy to migrate projects

### 5. Performance
- Connection pooling per database
- Queries don't interfere between projects
- Can scale individual projects

---

## 🔧 Advanced Configuration

### Enable PostgreSQL Extensions (Per Project)

When a project database is created, we automatically enable:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";        -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Query statistics
CREATE EXTENSION IF NOT EXISTS "pg_trgm";          -- Text search
CREATE EXTENSION IF NOT EXISTS "postgis";          -- Geospatial (optional)
```

### Connection Pool Settings

In `backend/app/core/config.py`:
```python
DATABASE_POOL_SIZE = 20        # Max connections per database
DATABASE_MAX_OVERFLOW = 10     # Extra connections if needed
```

### Query Limits

```python
QUERY_TIMEOUT_SECONDS = 10     # Max query execution time
MAX_ROWS_RETURNED = 1000       # Max rows per query
```

---

## 📈 Monitoring

### Check Database Sizes
```sql
SELECT 
    datname as database_name,
    pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
WHERE datname LIKE 'proj_%'
ORDER BY pg_database_size(datname) DESC;
```

### Check Active Connections
```sql
SELECT 
    datname,
    count(*) as connections
FROM pg_stat_activity
WHERE datname LIKE 'proj_%'
GROUP BY datname;
```

### Check Query Performance
```sql
SELECT 
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

---

## 🆘 Troubleshooting

### Can't Connect to PostgreSQL
```bash
# Check if PostgreSQL is running
services.msc
# Look for "postgresql-x64-XX" service
```

### Database Already Exists Error
```sql
-- Drop and recreate
DROP DATABASE IF EXISTS nexora_main;
CREATE DATABASE nexora_main;
```

### Permission Denied
```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE nexora_main TO postgres;
```

### Too Many Connections
```sql
-- Check current connections
SELECT count(*) FROM pg_stat_activity;

-- Increase max connections (postgresql.conf)
max_connections = 200
```

---

## ✅ Checklist

- [ ] PostgreSQL installed and running
- [ ] pgAdmin installed
- [ ] Database `nexora_main` created
- [ ] SQL initialization script executed
- [ ] 8 tables visible in pgAdmin
- [ ] Backend `.env` configured
- [ ] Python dependencies installed
- [ ] Backend connection test passed
- [ ] Backend starts without errors
- [ ] Can access API docs at http://localhost:8000/docs

---

## 🎉 You're Ready!

Once all checklist items are complete:

1. **Start Backend**: `uvicorn app.main:app --reload --port 8000`
2. **Start Frontend**: `npm run dev`
3. **Open Browser**: http://localhost:3000
4. **Create Account** → **Create Project** → **Start Building!**

Your PostgreSQL database is now configured exactly like Supabase! 🚀
