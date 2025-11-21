#!/usr/bin/env python3
"""
Check and verify user email status
"""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from db_pool import get_db_connection

def check_and_verify(email, verify=False):
    """Check user's email verification status and optionally verify"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            # Check current status
            cursor.execute("""
                SELECT id, email, full_name, email_verified, is_super_admin,
                       account_status
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

            if not user['email_verified']:
                print(f"\n⚠️  EMAIL NOT VERIFIED - This user cannot login!")

                if verify:
                    cursor.execute("""
                        UPDATE users
                        SET email_verified = true,
                            verification_token = NULL,
                            verification_token_expires = NULL
                        WHERE email = %s
                        RETURNING email_verified
                    """, (email,))

                    result = cursor.fetchone()
                    conn.commit()

                    print(f"✅ Email verified successfully!")
                    print(f"   email_verified = {result['email_verified']}")
                else:
                    print(f"\n   To verify, run:")
                    print(f"   python3 verify_user_email.py {email} verify\n")
            else:
                print(f"\n✅ Email is already verified - login should work\n")

        finally:
            cursor.close()

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "s.gillespie@gecslabs.com"
    verify = len(sys.argv) > 2 and sys.argv[2] == "verify"

    check_and_verify(email, verify)
