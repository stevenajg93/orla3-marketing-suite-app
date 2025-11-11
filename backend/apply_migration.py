#!/usr/bin/env python3
"""
Apply database migration to Railway PostgreSQL
Run this script locally to update the database schema
"""
import os
import psycopg2
from pathlib import Path

# Get DATABASE_URL from environment (Railway connection string)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set")
    print("📋 To fix this:")
    print("   1. Go to Railway → Backend service → Variables")
    print("   2. Copy the DATABASE_URL value")
    print("   3. Run: export DATABASE_URL='<paste-value-here>'")
    print("   4. Then run this script again")
    exit(1)

# Read migration file
migration_file = Path(__file__).parent / "migrations" / "001_add_generating_status.sql"

if not migration_file.exists():
    print(f"❌ ERROR: Migration file not found: {migration_file}")
    exit(1)

print("=" * 60)
print("🔧 ORLA³ DATABASE MIGRATION")
print("=" * 60)
print(f"📁 Migration: {migration_file.name}")
print(f"🔗 Database: {DATABASE_URL[:30]}...")
print()

try:
    # Read the migration SQL
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print("📖 Migration SQL:")
    print("-" * 60)
    for line in migration_sql.split('\n'):
        if line.strip() and not line.strip().startswith('--'):
            print(f"   {line}")
    print("-" * 60)
    print()

    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("✅ Connected!")
    print()

    # Execute migration
    print("🚀 Executing migration...")
    cur.execute(migration_sql)
    conn.commit()

    print("✅ Migration applied successfully!")
    print()

    # Verify the changes
    print("🔍 Verifying changes...")
    cur.execute("""
        SELECT constraint_name, check_clause
        FROM information_schema.check_constraints
        WHERE constraint_schema = 'public'
        AND constraint_name LIKE '%content_library%'
        ORDER BY constraint_name;
    """)

    constraints = cur.fetchall()
    for name, clause in constraints:
        print(f"   ✓ {name}: {clause[:80]}...")

    print()
    print("=" * 60)
    print("🎉 SUCCESS! Database is now ready for AI generation!")
    print("=" * 60)
    print()
    print("📝 Next steps:")
    print("   1. Test video generation on marketing.orla3.com")
    print("   2. Videos should now save to database with status='generating'")
    print("   3. When complete, they'll update to status='draft'")
    print()

    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"❌ DATABASE ERROR: {e}")
    print()
    print("💡 Troubleshooting:")
    print("   - Check that DATABASE_URL is correct")
    print("   - Verify you have database permissions")
    print("   - Check Railway database is accessible")
    exit(1)

except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)
