#!/usr/bin/env python3
"""
Apply Credit Tracking Migration
Adds credit balance tracking and transaction history
"""

from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment")
    exit(1)

print("🔄 Applying credit tracking migration...")
print(f"📍 Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Read migration file
    with open('migrations/003_add_credit_tracking.sql', 'r') as f:
        migration_sql = f.read()

    # Execute migration
    cur.execute(migration_sql)
    conn.commit()

    print("✅ Credit tracking migration applied successfully!")

    # Show summary
    cur.execute("""
        SELECT
            COUNT(*) as total_users,
            SUM(credit_balance) as total_credits,
            AVG(credit_balance) as avg_credits
        FROM users
        WHERE credit_balance > 0
    """)
    summary = cur.fetchone()

    print(f"\n📊 Credit System Summary:")
    print(f"   Total Users: {summary[0]}")
    print(f"   Total Credits Allocated: {summary[1]:,}")
    print(f"   Average Credits per User: {int(summary[2]):,}")

    # Show credit distribution by plan
    cur.execute("""
        SELECT
            plan,
            COUNT(*) as users,
            SUM(credit_balance) as total_credits
        FROM users
        WHERE subscription_status = 'active'
        GROUP BY plan
        ORDER BY total_credits DESC
    """)

    print(f"\n📈 Credits by Plan:")
    for row in cur.fetchall():
        print(f"   {row[0].capitalize()}: {row[1]} users, {row[2]:,} credits")

    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    exit(1)
except FileNotFoundError:
    print("❌ Migration file not found: migrations/003_add_credit_tracking.sql")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
