# Multi-Tenant Architecture - Deployment Checklist

## Overview
This checklist guides you through deploying the new Supabase-like multi-tenant architecture.

---

## Pre-Deployment

- [ ] Backup current database
  ```bash
  pg_dump nexora_main > backup_$(date +%Y%m%d).sql
  ```

- [ ] Review all new files created:
  - [ ] `backend/app/core/db_router.py`
  - [ ] `backend/app/middleware/project_context.py`
  - [ ] `backend/app/services/auto_table.py`
  - [ ] `backend/app/api/rest_v1.py`
  - [ ] `backend/app/api/public_auth_v2.py`

- [ ] Read documentation:
  - [ ] `MULTI_TENANT_ARCHITECTURE.md`
  - [ ] `IMPLEMENTATION_GUIDE_MULTI_TENANT.md`

---

## Deployment Steps

### Step 1: Update main.py

Add to `backend/app/main.py` after CORS middleware:

```python
# Add Project Context Middleware
from app.middleware.project_context import ProjectContextMiddleware
app.add_middleware(ProjectContextMiddleware)
```

Add to router imports:

```python
from app.api import rest_v1, public_auth_v2
```

Add to router includes (before existing routers):

```python
app.include_router(rest_v1.router, tags=["rest-api"])
app.include_router(public_auth_v2.router, tags=["auth-v2"])
```

Update shutdown handler:

```python
@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    from app.core.db_router import close_all_pools
    await close_all_pools()
    print("Application shutdown complete")
```

- [ ] Changes made to main.py
- [ ] Syntax verified

### Step 2: Create Migration Script

Create `migrate_to_multi_tenant.py` in root directory (see IMPLEMENTATION_GUIDE_MULTI_TENANT.md for full script).

- [ ] Migration script created
- [ ] Script tested on backup database first

### Step 3: Stop Backend

```bash
# Windows
taskkill /F /IM python.exe

# Or use restart_backend.bat
```

- [ ] Backend stopped

### Step 4: Run Migration

```bash
python migrate_to_multi_tenant.py
```

- [ ] Migration completed successfully
- [ ] Users migrated to project databases
- [ ] No errors in migration log

### Step 5: Start Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- [ ] Backend started successfully
- [ ] No startup errors
- [ ] Middleware loaded correctly

---

## Testing

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

Expected: `{"status": "healthy", ...}`

- [ ] Health check passed

### Test 2: Sign Up (Auto User Sync)

```bash
curl -X POST http://localhost:8000/v1/auth/4f181617-a248-4575-9b1a-3436fe7f3ad9/signup \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.2221c18b0d31e449e29636868ef3dabf0851c97984506431fdfcabaf8fdf8e58" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123", "name": "Test User"}'
```

Expected: Returns access_token and user object

- [ ] Signup successful
- [ ] User appears in dashboard Tables → users
- [ ] No errors in logs

### Test 3: Auto Table Creation

```bash
curl -X POST http://localhost:8000/rest/v1/posts \
  -H "x-project-id: 4f181617-a248-4575-9b1a-3436fe7f3ad9" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.2221c18b0d31e449e29636868ef3dabf0851c97984506431fdfcabaf8fdf8e58" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Post", "content": "Hello World"}'
```

Expected: Returns created post with ID

- [ ] Post created successfully
- [ ] `posts` table auto-created
- [ ] Post appears in dashboard Tables → posts
- [ ] No errors in logs

### Test 4: Get Records

```bash
curl -X GET http://localhost:8000/rest/v1/users \
  -H "x-project-id: 4f181617-a248-4575-9b1a-3436fe7f3ad9" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.2221c18b0d31e449e29636868ef3dabf0851c97984506431fdfcabaf8fdf8e58"
```

Expected: Returns array of users

- [ ] Users retrieved successfully
- [ ] Only project-specific users returned
- [ ] No errors in logs

### Test 5: Multi-Tenant Isolation

Create users in two different projects and verify they can't see each other's data.

- [ ] Data isolation verified
- [ ] No cross-project data leakage

### Test 6: Example Login Page

Open `example_login_page.html` in browser and test:

- [ ] Sign up works
- [ ] Login works
- [ ] User appears in dashboard immediately
- [ ] No CORS errors

---

## Monitoring

### Check Logs

Monitor backend logs for:
- [ ] No connection errors
- [ ] Project context resolution working
- [ ] Table auto-creation events logged
- [ ] User sync events logged

### Check Database

Verify in each project database:
- [ ] `users` table exists
- [ ] Users are being inserted
- [ ] Auto-created tables have correct schema

### Check Dashboard

- [ ] Tables page shows all tables
- [ ] Users table shows all users
- [ ] Auto-created tables visible
- [ ] No errors in frontend console

---

## Rollback Plan

If issues occur:

### Step 1: Stop New Backend

```bash
taskkill /F /IM python.exe
```

### Step 2: Restore Backup

```bash
psql -U postgres -d nexora_main < backup_YYYYMMDD.sql
```

### Step 3: Revert Code Changes

```bash
git checkout backend/app/main.py
```

### Step 4: Start Old Backend

```bash
cd backend
python -m uvicorn app.main:app --reload
```

---

## Post-Deployment

### Cleanup Old Code

Once confirmed working for 24+ hours:

- [ ] Remove `project_users` table from main DB
- [ ] Remove old sync triggers
- [ ] Remove old sync functions
- [ ] Delete temporary test scripts

### Update Documentation

- [ ] Update README.md with new API examples
- [ ] Update API documentation
- [ ] Create developer guide for new system

### Monitor Performance

- [ ] Check connection pool usage
- [ ] Monitor query performance
- [ ] Check memory usage
- [ ] Verify no connection leaks

---

## Success Criteria

✅ All tests passing
✅ No errors in logs
✅ Users auto-syncing correctly
✅ Tables auto-creating correctly
✅ Complete data isolation between projects
✅ Dashboard showing correct data
✅ Example login page working
✅ Performance acceptable

---

## Support

If you encounter issues:

1. Check logs: `backend/logs/` or console output
2. Review `IMPLEMENTATION_GUIDE_MULTI_TENANT.md`
3. Check database connections
4. Verify PROJECT_ID and ANON_KEY are correct
5. Test with curl commands first before frontend

---

## Timeline

- **Deployment**: 30 minutes
- **Testing**: 1 hour
- **Monitoring**: 24 hours
- **Cleanup**: 1 hour

**Total**: ~26 hours from start to full cleanup

---

## Notes

- Keep backup for at least 7 days
- Monitor closely for first 24 hours
- Have rollback plan ready
- Test thoroughly before production use


---

## Automated Backup Scheduler

### Overview
The backup scheduler automatically creates database backups on a configurable schedule with staggered execution to prevent resource spikes.

### Features
- ✅ Weekly backups (default: Sunday 12:00 AM)
- ✅ Staggered execution (0-30 min random offset per project)
- ✅ Automatic retry on failure (3 attempts with exponential backoff)
- ✅ Configurable retention period (default: 30 days)
- ✅ Automatic cleanup of old backups
- ✅ Per-project schedule configuration
- ✅ Manual backup trigger via API

### Setup Instructions

1. **Install Dependencies**
   ```bash
   cd backend
   pip install apscheduler==3.10.4
   ```

2. **Run Migration**
   ```bash
   python add_backup_scheduler.py
   ```
   This adds the `stagger_offset_minutes` column and creates default schedules for existing projects.

3. **Update Environment Variables**
   Add to `.env`:
   ```env
   BACKUP_ENABLED=true
   BACKUP_DEFAULT_SCHEDULE=weekly
   BACKUP_DEFAULT_TIME=00:00
   BACKUP_DEFAULT_DAY=0
   BACKUP_STAGGER_MAX_MINUTES=30
   BACKUP_RETENTION_DAYS=30
   BACKUP_MAX_RETRIES=3
   ```

4. **Test the Scheduler**
   ```bash
   python test_backup_scheduler.py
   ```

5. **Start Backend**
   The scheduler starts automatically when the backend starts:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   
   You should see:
   ```
   ⏰ Backup scheduler started
   📅 Loaded X backup schedules
   ```

### API Endpoints

**Get Schedule**
```http
GET /api/backup-schedules/{project_id}
Authorization: Bearer <token>
```

**Update Schedule**
```http
PUT /api/backup-schedules/{project_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "frequency": "weekly",
  "time_of_day": "00:00",
  "day_of_week": 0,
  "retention_days": 30,
  "enabled": true
}
```

**Manual Trigger**
```http
POST /api/backup-schedules/{project_id}/run-now
Authorization: Bearer <token>
```

**Get Next Run Time**
```http
GET /api/backup-schedules/{project_id}/next-run
Authorization: Bearer <token>
```

**Delete Schedule**
```http
DELETE /api/backup-schedules/{project_id}
Authorization: Bearer <token>
```

### Configuration Options

**Frequency Options:**
- `hourly` - Every hour
- `daily` - Every day at specified time
- `weekly` - Every week on specified day
- `monthly` - Every month on specified day

**Day of Week (for weekly):**
- `0` = Sunday
- `1` = Monday
- `2` = Tuesday
- `3` = Wednesday
- `4` = Thursday
- `5` = Friday
- `6` = Saturday

**Day of Month (for monthly):**
- `1-31` = Day of month

### Staggering Example

With 5 projects and 30-minute stagger window:
```
Sunday 00:00 → Project A (offset: 0 min)
Sunday 00:03 → Project B (offset: 3 min)
Sunday 00:12 → Project C (offset: 12 min)
Sunday 00:18 → Project D (offset: 18 min)
Sunday 00:27 → Project E (offset: 27 min)
```

### Monitoring

**Check Scheduled Jobs**
```http
GET /api/backup-schedules/admin/list-all
Authorization: Bearer <token>
```

**View Backup History**
```http
GET /api/backups/list/{project_id}
Authorization: Bearer <token>
```

### Troubleshooting

**Scheduler not starting:**
- Check `BACKUP_ENABLED=true` in `.env`
- Verify APScheduler is installed: `pip show apscheduler`
- Check logs for errors during startup

**Backups failing:**
- Verify `pg_dump` is installed and in PATH
- Check database connection settings
- Review backup logs in `backups` table
- Check disk space in `./backups` directory

**Schedule not executing:**
- Verify schedule is enabled in database
- Check `next_run_at` timestamp in `backup_schedules` table
- Ensure backend is running continuously
- Check system timezone matches UTC

### Production Considerations

1. **Disk Space**: Monitor `./backups` directory size
2. **Retention**: Adjust `BACKUP_RETENTION_DAYS` based on storage capacity
3. **Timing**: Schedule during low-traffic hours
4. **Monitoring**: Set up alerts for failed backups
5. **Testing**: Regularly test backup restoration
6. **Offsite Storage**: Consider copying backups to S3/cloud storage

### Files Created

- `backend/app/services/scheduler_service.py` - Main scheduler service
- `backend/app/api/backup_schedules.py` - API endpoints
- `backend/database/add_stagger_offset.sql` - Schema migration
- `backend/add_backup_scheduler.py` - Migration script
- `backend/test_backup_scheduler.py` - Test script
- `backend/setup_backup_scheduler.bat` - Setup automation

### Database Schema

**backup_schedules table:**
- `stagger_offset_minutes` - Random offset (0-30) for staggered execution
- `next_run_at` - Calculated next execution time
- `last_run_at` - Last successful execution time

**backups table:**
- `backup_type` - 'manual', 'scheduled', or 'auto'
- `status` - 'pending', 'in_progress', 'completed', 'failed'
- `error_message` - Failure details if status='failed'
