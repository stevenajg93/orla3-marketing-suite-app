#!/usr/bin/env python3
"""
Quick check if user email is verified
"""
import os
from dotenv import load_dotenv
from db_pool import get_db_connection

load_dotenv()

def check_verified(email):
    """Check if user's email is verified"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, email, full_name, email_verified, is_super_admin,
                       account_status, created_at
                FROM users
                WHERE email = %s
            """, (email,))

            user = cursor.fetchone()

            if not user:
                print(f"❌ User not found: {email}")
                return

            print(f"\n✅ User: {user['email']}")
            print(f"   ID: {user['id']}")
            print(f"   Name: {user['full_name']}")
            print(f"   Email Verified: {user['email_verified']}")
            print(f"   Super Admin: {user['is_super_admin']}")
            print(f"   Account Status: {user['account_status']}")
            print(f"   Created: {user['created_at']}\n")

            if not user['email_verified']:
                print("⚠️  EMAIL NOT VERIFIED - This user cannot login!")
                print("   Run this SQL to verify:")
                print(f"   UPDATE users SET email_verified = true WHERE email = '{email}';\n")
        finally:
            cursor.close()

if __name__ == "__main__":
    check_verified("s.gillespie@gecslabs.com")
