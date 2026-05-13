# 🧪 Zendbx Realtime Testing Guide

Complete step-by-step guide to test the PostgreSQL → WebSocket realtime integration.

---

## 📋 Prerequisites

Before testing, ensure you have:
- [x] PostgreSQL running
- [x] Node.js installed
- [x] Python 3.8+ installed
- [x] All dependencies installed

---

## 🚀 Step-by-Step Testing

### Step 1: Install Database Triggers

**Option A: Automated Setup (Recommended)**

```bash
# Run the setup script
setup_realtime.bat
```

**Option B: Manual Setup**

```bash
# Connect to your database and run the SQL
psql -U postgres -d nexora_main -f backend/database/realtime_triggers.sql
```

**Verify Installation:**

```sql
-- Connect to database
psql -U postgres -d nexora_main

-- Check if functions exist
\df notify_database_change
\df add_realtime_trigger
\df list_realtime_triggers

-- Should show 3 functions
```

---

### Step 2: Configure Backend

**Edit `backend/.env`** (or create if it doesn't exist):

```env
# Add these lines
WEBSOCKET_SERVER_URL=http://localhost:3002
ENABLE_REALTIME=true

# Make sure DATABASE_URL is correct
DATABASE_URL=postgresql://postgres:password@localhost:5432/nexora_main
```

**Verify Configuration:**

```bash
cd backend
python -c "from app.core.config import settings; print(f'WebSocket URL: {settings.WEBSOCKET_SERVER_URL}'); print(f'Realtime Enabled: {settings.ENABLE_REALTIME}')"
```

---

### Step 3: Start All Services

Open **3 separate terminals**:

**Terminal 1: WebSocket Server**

```bash
cd websocket-server
npm install  # First time only
npm start
```

Expected output:
```
🚀 Zendbx WebSocket Server started successfully
📡 Server running on port 3002
🔗 WebSocket endpoint: ws://localhost:3002
💚 Health check: http://localhost:3002/health
```

**Terminal 2: Backend Server**

```bash
cd backend
uvicorn app.main:app --reload
```

Expected output:
```
Starting ZENDBX v1.0.0...
Environment: development
Database: Connected
📡 Realtime listener started
🔗 WebSocket server: http://localhost:3002
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Terminal 3: Frontend (Optional)**

```bash
cd frontend
npm run dev
```

---

### Step 4: Create Test Table and Enable Realtime

**Open a new terminal and connect to PostgreSQL:**

```bash
psql -U postgres -d nexora_main
```

**Run these commands:**

```sql
-- Create a test table
DROP TABLE IF EXISTS realtime_test;
CREATE TABLE realtime_test (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    value INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable realtime on the test table
SELECT add_realtime_trigger('public', 'realtime_test');

-- Verify trigger was added
SELECT * FROM list_realtime_triggers();

-- Should show: public | realtime_test | realtime_test_realtime_trigger
```

---

### Step 5: Test with Web Interface (Easiest Method)

**Open your browser:**

```
http://localhost:3002/test/test-realtime.html
```

**What you'll see:**
- Beautiful dashboard with connection status
- Subscription management
- Real-time event viewer
- Statistics (INSERT/UPDATE/DELETE counts)

**Steps:**

1. **Subscribe to the test table:**
   - Type `table:realtime_test` in the input field
   - Click "Subscribe to Channel"
   - You should see it appear in the subscriptions list

2. **Open another terminal and make database changes:**

```bash
psql -U postgres -d nexora_main
```

```sql
-- Test INSERT
INSERT INTO realtime_test (name, value) VALUES ('Test Item 1', 100);

-- Test UPDATE
UPDATE realtime_test SET value = 200 WHERE name = 'Test Item 1';

-- Test DELETE
DELETE FROM realtime_test WHERE name = 'Test Item 1';
```

3. **Watch the events appear in real-time!**
   - Each operation should appear instantly in the web interface
   - You'll see the operation type, table name, and data
   - Statistics will update automatically

---

### Step 6: Test with Python Script

**Run the automated test:**

```bash
cd backend
python test_realtime.py
```

**Expected output:**

```
============================================================
ZENDBX REALTIME INTEGRATION TEST
============================================================
🔧 Setting up realtime triggers...
✅ Realtime trigger system installed
✅ Test table created
✅ Realtime trigger added to public.realtime_test

📋 Active realtime triggers:
   - public.realtime_test

🧪 Testing INSERT operation...
✅ INSERT executed - check WebSocket for notification

🧪 Testing UPDATE operation...
✅ UPDATE executed - check WebSocket for notification

🧪 Testing DELETE operation...
✅ DELETE executed - check WebSocket for notification

============================================================
✅ All tests completed!
============================================================
```

**Check Backend Terminal:**

You should see logs like:
```
📨 Received notification: realtime_test - INSERT
✅ Broadcasted event to WebSocket: realtime_test
```

**Check WebSocket Terminal:**

You should see logs like:
```
📡 Broadcasting db_change to channel: table:realtime_test
```

---

### Step 7: Test with Direct LISTEN (Advanced)

**Listen directly to PostgreSQL notifications:**

```bash
cd backend
python test_realtime.py --listen
```

**Expected output:**

```
👂 Listening to database notifications...
   (Press Ctrl+C to stop)
```

**In another terminal, make database changes:**

```sql
INSERT INTO realtime_test (name, value) VALUES ('Direct Test', 999);
```

**You should see:**

```
📨 Notification received:
   Table: realtime_test
   Operation: INSERT
   Timestamp: 2024-03-30T12:00:00.123Z
   New data: {'id': 1, 'name': 'Direct Test', 'value': 999, ...}
```

Press `Ctrl+C` to stop listening.

---

### Step 8: Test with Multiple Clients

**Open multiple browser tabs:**

1. Open `http://localhost:3002/test/test-realtime.html` in **Tab 1**
2. Open `http://localhost:3002/test/test-realtime.html` in **Tab 2**
3. Subscribe both to `table:realtime_test`

**Make a database change:**

```sql
INSERT INTO realtime_test (name, value) VALUES ('Multi-Client Test', 555);
```

**Result:**
- Both tabs should receive the event simultaneously
- Both should show the same data
- This proves broadcasting works!

---

### Step 9: Test Different Operations

**Test all CRUD operations:**

```sql
-- INSERT (should show new data)
INSERT INTO realtime_test (name, value) 
VALUES ('Alice', 100), ('Bob', 200), ('Charlie', 300);

-- UPDATE (should show old and new data)
UPDATE realtime_test SET value = value + 50 WHERE name = 'Alice';

-- DELETE (should show old data)
DELETE FROM realtime_test WHERE name = 'Bob';

-- Bulk operations
INSERT INTO realtime_test (name, value)
SELECT 'User ' || i, i * 10
FROM generate_series(1, 5) i;
```

Each operation should trigger a separate event in the web interface.

---

### Step 10: Test API Endpoints

**Get realtime status:**

```bash
curl -X GET http://localhost:8000/api/realtime/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**List tables with realtime:**

```bash
curl -X GET http://localhost:8000/api/projects/PROJECT_ID/realtime/triggers \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Enable realtime on a table:**

```bash
curl -X POST "http://localhost:8000/api/projects/PROJECT_ID/realtime/triggers?table_name=users&schema_name=public" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔍 Troubleshooting

### Problem: No events received

**Check 1: Verify trigger is installed**

```sql
SELECT * FROM list_realtime_triggers();
```

If empty, run:
```sql
SELECT add_realtime_trigger('public', 'realtime_test');
```

**Check 2: Verify backend is listening**

Look for this in backend logs:
```
📡 Connected to main for realtime notifications
```

If not present, check:
- `ENABLE_REALTIME=true` in `.env`
- `DATABASE_URL` is correct
- PostgreSQL is running

**Check 3: Verify WebSocket server is running**

```bash
curl http://localhost:3002/health
```

Should return:
```json
{"status":"ok","connections":0,"uptime":123}
```

**Check 4: Verify client is subscribed**

In browser console:
```javascript
socket.emit('subscribe', { channel: 'table:realtime_test' });
```

---

### Problem: Backend can't connect to WebSocket

**Check WebSocket URL:**

```bash
cd backend
python -c "from app.core.config import settings; print(settings.WEBSOCKET_SERVER_URL)"
```

Should output: `http://localhost:3002`

**Test WebSocket server manually:**

```bash
curl -X POST http://localhost:3002/broadcast \
  -H "Content-Type: application/json" \
  -d '{"event":"test","channel":"test:channel","data":{"message":"hello"}}'
```

Should return:
```json
{"success":true,"event":"test","channel":"test:channel","subscribers":0}
```

---

### Problem: Events delayed or missing

**Check database connection:**

```sql
-- Check active connections
SELECT * FROM pg_stat_activity WHERE datname = 'nexora_main';
```

**Check for errors in backend logs:**

Look for:
```
PostgreSQL error in main: ...
```

**Restart services:**

```bash
# Stop all services (Ctrl+C in each terminal)
# Then restart in order:
# 1. WebSocket server
# 2. Backend
# 3. Frontend
```

---

## ✅ Success Checklist

After testing, you should have verified:

- [x] Database triggers installed
- [x] Backend listener connected
- [x] WebSocket server receiving events
- [x] Web interface showing events
- [x] INSERT operations work
- [x] UPDATE operations work
- [x] DELETE operations work
- [x] Multiple clients receive events
- [x] Events appear in < 1 second
- [x] Auto-reconnect works (restart backend and it reconnects)

---

## 🎯 Next Steps

Once testing is complete:

1. **Enable realtime on your actual tables:**
   ```sql
   SELECT add_realtime_trigger('public', 'users');
   SELECT add_realtime_trigger('public', 'posts');
   SELECT add_realtime_trigger('public', 'comments');
   ```

2. **Integrate into your frontend:**
   - See `REALTIME_IMPLEMENTATION.md` for React examples
   - Use the `useRealtimeTable` hook pattern
   - Subscribe to relevant channels

3. **Monitor performance:**
   - Check WebSocket stats: `http://localhost:3002/stats`
   - Monitor backend logs for errors
   - Watch database performance

4. **Add authentication:**
   - Implement WebSocket auth middleware
   - Validate channel subscriptions
   - Filter events based on user permissions

---

## 📚 Additional Resources

- **Full Documentation**: [REALTIME_IMPLEMENTATION.md](./REALTIME_IMPLEMENTATION.md)
- **Status Overview**: [REALTIME_STATUS.md](./REALTIME_STATUS.md)
- **WebSocket Basics**: [WEBSOCKET_QUICKSTART.md](./WEBSOCKET_QUICKSTART.md)
- **Test Interface**: http://localhost:3002/test/test-realtime.html

---

## 🎉 You're Done!

If all tests pass, your realtime system is working perfectly! Any database change will now automatically broadcast to all connected clients in real-time.

**Happy building! 🚀**
