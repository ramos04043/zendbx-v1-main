# CSV Import Feature Guide

## Overview
The CSV Import feature allows you to upload CSV files and import them into your database with built-in data cleaning capabilities.

## Features

### 1. Data Cleaning
- **Remove Duplicates**: Automatically detects and removes duplicate rows based on all column values
- **Skip Empty Rows**: Filters out rows that contain only empty cells
- **Data Preview**: Shows the first 10 rows before importing

### 2. Data Quality Insights
Before importing, you'll see:
- Total number of rows
- Number of duplicate rows detected
- Number of empty rows detected

### 3. Automatic Table Creation
- Automatically creates a table with appropriate column types
- Adds `id`, `created_at`, and `updated_at` columns automatically
- Infers column types from your data (INTEGER, DECIMAL, TEXT, etc.)

## How to Use

### Step 1: Upload CSV File
1. Navigate to Dashboard → Import
2. Click "Choose CSV File"
3. Select your CSV file

### Step 2: Review Data
- Check the data quality statistics
- Preview the first 10 rows
- Review detected duplicates and empty rows

### Step 3: Configure Import
1. Enter a table name (auto-generated from filename)
2. Choose whether to remove duplicates (recommended)
3. Choose whether to skip empty rows (recommended)

### Step 4: Import
- Click "Import Data"
- Wait for the import to complete
- View success message with import statistics

## API Endpoints

### Backend Endpoint
```
POST /api/import
```

**Request Body:**
```json
{
  "tableName": "my_table",
  "headers": ["column1", "column2", "column3"],
  "rows": [
    ["value1", "value2", "value3"],
    ["value4", "value5", "value6"]
  ],
  "removeDuplicates": true,
  "skipEmptyRows": true
}
```

**Response:**
```json
{
  "success": true,
  "table_name": "my_table",
  "inserted": 150,
  "total_rows": 200,
  "cleaned_rows": 150
}
```

## CSV Format Requirements

- File must have `.csv` extension
- First row should contain column headers
- Columns separated by commas
- UTF-8 encoding recommended

## Example CSV
```csv
name,email,age,city
John Doe,john@example.com,30,New York
Jane Smith,jane@example.com,25,Los Angeles
John Doe,john@example.com,30,New York
,,,,
Bob Johnson,bob@example.com,35,Chicago
```

In this example:
- Row 3 is a duplicate of Row 1 (will be removed if "Remove Duplicates" is enabled)
- Row 4 is empty (will be skipped if "Skip Empty Rows" is enabled)
- Final import: 3 unique rows

## Technical Details

### Column Type Inference
The system automatically infers PostgreSQL column types:
- Integers → `INTEGER`
- Decimals → `DECIMAL`
- Booleans → `BOOLEAN`
- Dates → `TIMESTAMPTZ`
- Text → `VARCHAR` or `TEXT`

### Duplicate Detection
Duplicates are detected by comparing all column values in a row. Two rows are considered duplicates if all their values match exactly.

### Table Structure
Created tables include:
- `id SERIAL PRIMARY KEY` - Auto-incrementing ID
- Your CSV columns with inferred types
- `created_at TIMESTAMPTZ DEFAULT NOW()` - Creation timestamp
- `updated_at TIMESTAMPTZ DEFAULT NOW()` - Last update timestamp

## Troubleshooting

### "No project found" Error
- Make sure you have created at least one project
- The import will use your most recent project

### "Failed to parse CSV" Error
- Check that your file is a valid CSV
- Ensure proper comma separation
- Verify UTF-8 encoding

### Import Fails Silently
- Check that table name doesn't already exist
- Verify you have proper permissions
- Check backend logs for detailed errors

## Future Enhancements
- Support for custom column type selection
- Ability to map CSV columns to existing tables
- Support for Excel files (.xlsx)
- Batch import for multiple files
- Import history and rollback
