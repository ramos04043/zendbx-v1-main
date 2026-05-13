# Testing Triggers - Complete Guide

Let's test the trigger system with a real-world example: automatically updating timestamps.

---

## Step 1: Prepare Your Table

First, make sure you have a table with an `updated_at` column.

### Option A: Create a New Test Table

1. Go to **Database → Tables**
2. Click **"New Table"**
3. Create table `products`:
   - `id` | SERIAL | PRIMARY KEY | NOT NULL
   - `name` | TEXT | NOT NULL
   - `price` | INTEGER
   - `created_at` | TIMESTAMP
   - `updated_at` | TIMESTAMP

4. Click **"Create"**

### Option B: Use Existing Table

If you already have a `users` table, make sure it has an `updated_at` column.
If not, you can add it:
1. Select the table
2. Click "Add Column"
3. Add: `updated_at` | TIMESTAMP

---

## Step 2: Create the Trigger Function

1. Go to **Database → Functions**
2. Click **"New Function"**
3. Paste this code:

```sql
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;
```

4. Click **"Create Function"**

**What this does:**
- This is a trigger function (returns `trigger`)
- `NEW` represents the new row being inserted/updated
- It sets `updated_at` to the current timestamp
- Returns the modified row

---

## Step 3: Create the Trigger

1. Go to **Database → Triggers**
2. Click **"New Trigger"**
3. Fill in the form:
   - **Trigger Name**: `update_products_timestamp`
   - **Table**: Select `products` (or your table)
   - **Event**: Select `UPDATE`
   - **Timing**: Select `BEFORE`
   - **Function**: Select `update_timestamp`

4. You should see the SQL preview:
```sql
CREATE TRIGGER update_products_timestamp
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();
```

5. Click **"Create Trigger"**

**Expected Result:**
- Trigger appears in sidebar with blue UPDATE icon
- Configuration shows all settings
- SQL definition is displayed

---

## Step 4: Test the Trigger

Now let's test if it actually works!

### 4.1 Insert Test Data

Go to **SQL Editor** and run:

```sql
-- Insert a test product
INSERT INTO products (name, price, created_at, updated_at)
VALUES ('Laptop', 999, NOW(), NOW());

-- Check the data
SELECT * FROM products;
```

You should see your product with both timestamps set.

### 4.2 Update the Product (This triggers the function!)

```sql
-- Update the product
UPDATE products 
SET price = 1099 
WHERE name = 'Laptop';

-- Check the updated_at timestamp
SELECT name, price, created_at, updated_at 
FROM products 
WHERE name = 'Laptop';
```

**Expected Result:**
- `updated_at` should be MORE RECENT than `created_at`
- The trigger automatically updated the timestamp!

---

## Step 5: Create More Trigger Examples

### Example 1: Audit Log Trigger

**Step 1: Create audit table**
```sql
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  table_name TEXT NOT NULL,
  action TEXT NOT NULL,
  record_id INTEGER,
  changed_at TIMESTAMP DEFAULT NOW()
);
```

**Step 2: Create audit function**
```sql
CREATE OR REPLACE FUNCTION log_changes()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  INSERT INTO audit_log (table_name, action, record_id, changed_at)
  VALUES (TG_TABLE_NAME, TG_OP, NEW.id, NOW());
  RETURN NEW;
END;
$$;
```

**Step 3: Create trigger**
- Name: `audit_products_changes`
- Table: `products`
- Event: `INSERT` (or `UPDATE`)
- Timing: `AFTER`
- Function: `log_changes`

**Step 4: Test it**
```sql
-- Insert a product
INSERT INTO products (name, price, created_at, updated_at)
VALUES ('Mouse', 25, NOW(), NOW());

-- Check the audit log
SELECT * FROM audit_log;
```

You should see a log entry!

---

### Example 2: Validation Trigger

**Step 1: Create validation function**
```sql
CREATE OR REPLACE FUNCTION validate_price()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.price < 0 THEN
    RAISE EXCEPTION 'Price cannot be negative: %', NEW.price;
  END IF;
  
  IF NEW.price > 1000000 THEN
    RAISE EXCEPTION 'Price too high: %', NEW.price;
  END IF;
  
  RETURN NEW;
END;
$$;
```

**Step 2: Create trigger**
- Name: `validate_product_price`
- Table: `products`
- Event: `INSERT` (or `UPDATE`)
- Timing: `BEFORE`
- Function: `validate_price`

**Step 3: Test it**
```sql
-- This should work
INSERT INTO products (name, price, created_at, updated_at)
VALUES ('Keyboard', 50, NOW(), NOW());

-- This should FAIL (negative price)
INSERT INTO products (name, price, created_at, updated_at)
VALUES ('Bad Product', -10, NOW(), NOW());
```

The second insert should fail with an error message!

---

### Example 3: Auto-Generate Slug

**Step 1: Add slug column to products**
```sql
ALTER TABLE products ADD COLUMN slug TEXT;
```

**Step 2: Create slug function**
```sql
CREATE OR REPLACE FUNCTION generate_slug()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.slug = LOWER(
    REGEXP_REPLACE(
      REGEXP_REPLACE(NEW.name, '[^a-zA-Z0-9\s-]', '', 'g'),
      '\s+', '-', 'g'
    )
  );
  RETURN NEW;
END;
$$;
```

**Step 3: Create trigger**
- Name: `auto_generate_slug`
- Table: `products`
- Event: `INSERT`
- Timing: `BEFORE`
- Function: `generate_slug`

**Step 4: Test it**
```sql
-- Insert product with special characters
INSERT INTO products (name, price, created_at, updated_at)
VALUES ('Super Cool Product!', 199, NOW(), NOW());

-- Check the slug
SELECT name, slug FROM products WHERE name LIKE 'Super%';
```

You should see: `slug = "super-cool-product"`

---

## Step 6: View All Triggers

1. Go to **Database → Triggers**
2. You should see all your triggers in the sidebar
3. Click on each to view:
   - Configuration
   - SQL definition
   - Info about how it works

---

## Step 7: Test Trigger Deletion

1. Select a trigger
2. Click **"Delete Trigger"**
3. Confirm deletion
4. Trigger is removed

**To verify:**
```sql
-- Try the action that would trigger it
UPDATE products SET price = 500 WHERE id = 1;

-- If the trigger was for updating timestamp, 
-- updated_at won't change anymore
```

---

## Common Trigger Patterns

### Pattern 1: BEFORE INSERT/UPDATE
```sql
-- Modify data before saving
CREATE TRIGGER my_trigger
BEFORE INSERT OR UPDATE ON my_table
FOR EACH ROW
EXECUTE FUNCTION my_function();
```

### Pattern 2: AFTER INSERT/UPDATE/DELETE
```sql
-- Log or notify after data changes
CREATE TRIGGER my_trigger
AFTER INSERT OR UPDATE OR DELETE ON my_table
FOR EACH ROW
EXECUTE FUNCTION my_function();
```

### Pattern 3: Prevent Deletion (Soft Delete)
```sql
CREATE OR REPLACE FUNCTION prevent_delete()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE my_table SET deleted_at = NOW() WHERE id = OLD.id;
  RETURN NULL;  -- Prevents actual deletion
END;
$$;

CREATE TRIGGER soft_delete_trigger
BEFORE DELETE ON my_table
FOR EACH ROW
EXECUTE FUNCTION prevent_delete();
```

---

## Troubleshooting

### Issue: "Need tables & functions first"
**Solution:** Create at least one table and one function before creating triggers.

### Issue: Trigger not firing
**Check:**
1. Is the trigger created? (Check in Triggers page)
2. Is the function correct? (Check in Functions page)
3. Are you performing the right action? (INSERT/UPDATE/DELETE)
4. Is the timing correct? (BEFORE/AFTER)

### Issue: Error when creating trigger
**Common causes:**
1. Function doesn't exist
2. Function doesn't return `trigger` type
3. Table doesn't exist
4. Trigger name already exists

### Issue: Function error when trigger fires
**Debug:**
```sql
-- Check PostgreSQL logs
-- Or add RAISE NOTICE in your function:
CREATE OR REPLACE FUNCTION my_function()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE NOTICE 'Trigger fired! OLD: %, NEW: %', OLD, NEW;
  RETURN NEW;
END;
$$;
```

---

## Testing Checklist

✅ Created a table with `updated_at` column
✅ Created `update_timestamp()` function
✅ Created trigger on UPDATE event
✅ Tested by updating a record
✅ Verified `updated_at` changed automatically
✅ Created audit log system
✅ Created validation trigger
✅ Viewed all triggers in UI
✅ Deleted a trigger successfully

---

## Real-World Use Cases

1. **Auto-timestamps**: Update `updated_at` on every change
2. **Audit logging**: Track who changed what and when
3. **Data validation**: Ensure data meets business rules
4. **Cascading updates**: Update related tables automatically
5. **Notifications**: Send alerts when data changes
6. **Soft deletes**: Mark as deleted instead of removing
7. **Auto-generate fields**: Create slugs, codes, etc.
8. **Maintain counters**: Update aggregate counts
9. **Enforce constraints**: Complex business logic
10. **Data transformation**: Clean/format data on insert

---

## Next Steps

1. Create a complete audit system
2. Add validation to all your tables
3. Set up auto-timestamps on all tables
4. Create custom business logic triggers
5. Monitor trigger performance

---

## Quick Reference

**Trigger Variables:**
- `NEW` - New row (INSERT/UPDATE)
- `OLD` - Old row (UPDATE/DELETE)
- `TG_TABLE_NAME` - Table name
- `TG_OP` - Operation (INSERT/UPDATE/DELETE)
- `TG_WHEN` - BEFORE or AFTER

**Return Values:**
- `RETURN NEW` - Use modified row (BEFORE triggers)
- `RETURN OLD` - Use old row
- `RETURN NULL` - Cancel operation (BEFORE triggers)

Happy testing! 🚀
