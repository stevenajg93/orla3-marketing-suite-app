#!/usr/bin/env python3
"""
Apply Multi-Tenant Architecture Migration
Reads migration SQL file and applies it to the database
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in environment")
    exit(1)

print("=" * 70)
print("🚀 APPLYING MULTI-TENANT ARCHITECTURE MIGRATION")
print("=" * 70)
print(f"\nDatabase: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}")
print("\nThis migration will:")
print("  ✓ Create users, refresh_tokens, audit_log tables")
print("  ✓ Create user_cloud_storage_tokens table")
print("  ✓ Add user_id columns to all existing tables")
print("  ✓ Update constraints for multi-tenancy")
print("\n⚠️  WARNING: This is an irreversible schema change!")
print("\nPress ENTER to continue or CTRL+C to cancel...")
input()

try:
    # Read migration file
    migration_path = "migrations/001_add_multi_tenant_architecture.sql"
    print(f"\n📖 Reading migration from: {migration_path}")

    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False  # Use transaction
    cur = conn.cursor()

    # Apply migration
    print("📝 Applying migration...")
    cur.execute(migration_sql)

    # Commit transaction
    print("💾 Committing changes...")
    conn.commit()

    # Verify tables created
    print("\n✅ Migration applied successfully!")
    print("\nVerifying new tables...")

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('users', 'refresh_tokens', 'audit_log', 'user_cloud_storage_tokens')
        ORDER BY table_name
    """)

    tables = cur.fetchall()
    print(f"\nNew tables created ({len(tables)}):")
    for table in tables:
        print(f"  ✓ {table[0]}")

    # Check user_id columns added
    cur.execute("""
        SELECT table_name
        FROM information_schema.columns
        WHERE column_name = 'user_id'
        AND table_schema = 'public'
        ORDER BY table_name
    """)

    user_id_tables = cur.fetchall()
    print(f"\nTables with user_id column ({len(user_id_tables)}):")
    for table in user_id_tables:
        print(f"  ✓ {table[0]}")

    print("\n" + "=" * 70)
    print("🎉 MULTI-TENANT MIGRATION COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Create your first user account via /auth/register")
    print("  2. All new data will be associated with user accounts")
    print("  3. Implement OAuth routes for cloud storage")
    print("\n")

    cur.close()
    conn.close()

except FileNotFoundError:
    print(f"\n❌ ERROR: Migration file not found: {migration_path}")
    print("   Make sure you're running this from the backend directory")
    exit(1)

except psycopg2.Error as e:
    print(f"\n❌ DATABASE ERROR: {str(e)}")
    if conn:
        conn.rollback()
        print("   Changes rolled back")
    exit(1)

except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
    if conn:
        conn.rollback()
        print("   Changes rolled back")
    exit(1)
