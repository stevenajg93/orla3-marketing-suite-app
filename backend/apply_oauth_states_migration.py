#!/usr/bin/env python3
"""
Apply OAuth States Table Migration
Adds oauth_states table for OAuth CSRF protection
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def apply_migration():
    """Apply the oauth_states table migration"""
    try:
        migration_path = "migrations/005_add_oauth_states_table.sql"

        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        print("🔄 Applying oauth_states table migration...")
        cur.execute(migration_sql)
        conn.commit()

        print("✅ Migration applied successfully!")
        print("   - Created oauth_states table")
        print("   - Added indexes for performance")
        print("   - OAuth flows now ready for all 9 platforms")

        cur.close()
        conn.close()

    except FileNotFoundError:
        print(f"❌ Migration file not found: {migration_path}")
        print("   Make sure you're running this from the backend directory")
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    apply_migration()
