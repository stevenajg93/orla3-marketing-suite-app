#!/usr/bin/env python3
"""
Apply Stripe Fields Migration
Adds Stripe customer and subscription tracking to users table
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 70)
print("🚀 APPLYING STRIPE FIELDS MIGRATION")
print("=" * 70)
print("\n⚠️  This will add Stripe tracking fields to the users table")

try:
    # Read migration file
    migration_path = "migrations/002_add_stripe_fields.sql"
    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    print("\n📋 Applying migration...")

    # Apply migration
    cur.execute(migration_sql)
    conn.commit()

    print("\n✅ Migration applied successfully!")

    # Verify columns were added
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name IN ('stripe_customer_id', 'stripe_subscription_id', 'subscription_status')
        ORDER BY column_name
    """)

    columns = cur.fetchall()
    print(f"\n✅ Verified {len(columns)} new columns:")
    for col in columns:
        print(f"  ✓ {col[0]} ({col[1]})")

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    if conn:
        conn.rollback()
    exit(1)
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()

print("\n" + "=" * 70)
print("✅ MIGRATION COMPLETE")
print("=" * 70)
