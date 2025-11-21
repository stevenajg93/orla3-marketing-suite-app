#!/usr/bin/env python3
"""
Check user data in database
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def check_user_data(email):
    """Check if user exists, has content, and has cloud storage connected"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Find user
        print(f"\n🔍 Searching for user: {email}")
        cursor.execute("""
            SELECT id, email, full_name, role, current_organization_id, created_at,
                   email_verified, is_super_admin, account_status
            FROM users
            WHERE email = %s
        """, (email,))
        user = cursor.fetchone()

        if not user:
            print(f"❌ User not found: {email}")
            return

        print(f"✅ User found:")
        print(f"   ID: {user['id']}")
        print(f"   Name: {user['full_name']}")
        print(f"   Role: {user['role']}")
        print(f"   Org ID: {user['current_organization_id']}")
        print(f"   Email Verified: {user['email_verified']}")
        print(f"   Super Admin: {user['is_super_admin']}")
        print(f"   Account Status: {user['account_status']}")
        print(f"   Created: {user['created_at']}")

        user_id = str(user['id'])
        org_id = str(user['current_organization_id']) if user['current_organization_id'] else None

        # Check library content
        print(f"\n📚 Checking library content...")
        cursor.execute("""
            SELECT COUNT(*) as count,
                   array_agg(DISTINCT content_type) as types
            FROM library_content
            WHERE user_id = %s
        """, (user_id,))
        content = cursor.fetchone()

        if content['count'] > 0:
            print(f"✅ Found {content['count']} library items")
            print(f"   Types: {', '.join(content['types']) if content['types'] else 'None'}")
        else:
            print(f"❌ No library content found")

        # Get sample content
        cursor.execute("""
            SELECT id, title, content_type, media_url, created_at
            FROM library_content
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 5
        """, (user_id,))
        samples = cursor.fetchall()

        if samples:
            print(f"\n📋 Sample content (latest 5):")
            for item in samples:
                print(f"   - {item['title'][:50]} ({item['content_type']}) - {item['created_at']}")

        # Check cloud storage connections (user-level)
        print(f"\n☁️  Checking cloud storage (user-level)...")
        cursor.execute("""
            SELECT provider, provider_email, is_active, connected_at,
                   token_expires_at, organization_id
            FROM user_cloud_storage_tokens
            WHERE user_id = %s
            ORDER BY connected_at DESC
        """, (user_id,))
        user_connections = cursor.fetchall()

        if user_connections:
            print(f"✅ Found {len(user_connections)} user-level connection(s):")
            for conn_row in user_connections:
                status = "✅ Active" if conn_row['is_active'] else "❌ Inactive"
                expires = conn_row['token_expires_at']
                expired = " (EXPIRED)" if expires and expires < datetime.now() else ""
                org_marker = f" [org: {conn_row['organization_id']}]" if conn_row['organization_id'] else " [no org_id]"
                print(f"   - {conn_row['provider']} ({conn_row['provider_email']}) - {status}{expired}{org_marker}")
                print(f"     Connected: {conn_row['connected_at']}")
                if expires:
                    print(f"     Expires: {expires}")
        else:
            print(f"❌ No user-level cloud storage connections")

        # Check organization-level cloud storage if user has org
        if org_id:
            print(f"\n☁️  Checking cloud storage (org-level for org {org_id})...")
            cursor.execute("""
                SELECT provider, provider_email, is_active, connected_at,
                       token_expires_at, user_id
                FROM user_cloud_storage_tokens
                WHERE organization_id = %s
                ORDER BY connected_at DESC
            """, (org_id,))
            org_connections = cursor.fetchall()

            if org_connections:
                print(f"✅ Found {len(org_connections)} org-level connection(s):")
                for conn_row in org_connections:
                    status = "✅ Active" if conn_row['is_active'] else "❌ Inactive"
                    expires = conn_row['token_expires_at']
                    expired = " (EXPIRED)" if expires and expires < datetime.now() else ""
                    print(f"   - {conn_row['provider']} ({conn_row['provider_email']}) - {status}{expired}")
                    print(f"     User ID: {conn_row['user_id']}")
                    print(f"     Connected: {conn_row['connected_at']}")
            else:
                print(f"❌ No org-level cloud storage connections")

    finally:
        cursor.close()

    print(f"\n✅ Database check complete")

if __name__ == "__main__":
    check_user_data("s.gillespie@gecslabs.com")
