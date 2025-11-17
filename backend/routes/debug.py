from fastapi import APIRouter, Request, HTTPException
from middleware import get_user_id
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import httpx

router = APIRouter()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@router.get("/debug/cloud-storage")
async def debug_cloud_storage(request: Request):
    """
    Diagnostic endpoint to debug cloud storage issues
    """
    results = {
        "step_1_user_id": None,
        "step_2_database": None,
        "step_3_connection": None,
        "step_4_selected_folders_column": None,
        "step_5_connection_details": None,
        "step_6_google_drive_test": None,
        "errors": []
    }

    try:
        # Step 1: Get user ID
        user_id = get_user_id(request)
        results["step_1_user_id"] = {
            "success": True,
            "user_id": str(user_id),
            "type": str(type(user_id))
        }
    except Exception as e:
        results["step_1_user_id"] = {"success": False, "error": str(e)}
        results["errors"].append(f"Step 1 failed: {str(e)}")
        return results

    try:
        # Step 2: Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        results["step_2_database"] = {"success": True}
    except Exception as e:
        results["step_2_database"] = {"success": False, "error": str(e)}
        results["errors"].append(f"Step 2 failed: {str(e)}")
        return results

    try:
        # Step 3: Check if selected_folders column exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'user_cloud_storage_tokens' AND column_name = 'selected_folders'
        """)
        has_folder_column = cursor.fetchone() is not None
        results["step_4_selected_folders_column"] = {
            "success": True,
            "exists": has_folder_column
        }
    except Exception as e:
        results["step_4_selected_folders_column"] = {"success": False, "error": str(e)}
        results["errors"].append(f"Step 4 failed: {str(e)}")

    try:
        # Step 4: Get user's cloud storage connection
        user_id_str = str(user_id)

        if has_folder_column:
            cursor.execute("""
                SELECT access_token, refresh_token, token_expires_at, provider_email, selected_folders
                FROM user_cloud_storage_tokens
                WHERE user_id = %s AND provider = %s AND is_active = true
                LIMIT 1
            """, (user_id_str, 'google_drive'))
        else:
            cursor.execute("""
                SELECT access_token, refresh_token, token_expires_at, provider_email
                FROM user_cloud_storage_tokens
                WHERE user_id = %s AND provider = %s AND is_active = true
                LIMIT 1
            """, (user_id_str, 'google_drive'))

        connection = cursor.fetchone()

        if connection:
            # Convert to dict
            if has_folder_column:
                connection = dict(connection)
            else:
                connection = dict(connection)
                connection['selected_folders'] = []

            # Check token expiration
            now = datetime.now(connection['token_expires_at'].tzinfo) if connection.get('token_expires_at') else datetime.utcnow()
            is_expired = connection['token_expires_at'] < now if connection.get('token_expires_at') else False

            results["step_5_connection_details"] = {
                "success": True,
                "has_access_token": bool(connection.get('access_token')),
                "has_refresh_token": bool(connection.get('refresh_token')),
                "provider_email": connection.get('provider_email'),
                "token_expires_at": str(connection.get('token_expires_at')),
                "is_token_expired": is_expired,
                "has_selected_folders": bool(connection.get('selected_folders')),
                "connection_type": str(type(connection))
            }

            # Step 5: Try to call Google Drive API
            try:
                access_token = connection['access_token']
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        "https://www.googleapis.com/drive/v3/drives",
                        headers={"Authorization": f"Bearer {access_token}"},
                        params={"pageSize": 10}
                    )

                    results["step_6_google_drive_test"] = {
                        "success": response.status_code == 200,
                        "status_code": response.status_code,
                        "response": response.text[:500] if response.status_code != 200 else "OK"
                    }
            except Exception as e:
                results["step_6_google_drive_test"] = {
                    "success": False,
                    "error": f"{type(e).__name__}: {str(e)}"
                }
                results["errors"].append(f"Step 6 failed: {str(e)}")
        else:
            results["step_5_connection_details"] = {
                "success": False,
                "error": "No active Google Drive connection found"
            }
            results["errors"].append("No active Google Drive connection in database")

    except Exception as e:
        results["step_3_connection"] = {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
        results["errors"].append(f"Step 3 failed: {type(e).__name__}: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return results


@router.get("/debug/user/{email}")
async def debug_user_data(email: str):
    """
    Check user data: library content and cloud storage connections
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    result = {
        "user": None,
        "library_content": None,
        "cloud_storage_user_level": None,
        "cloud_storage_org_level": None,
        "errors": []
    }

    try:
        # Find user
        cursor.execute("""
            SELECT id, email, full_name, role, current_organization_id, created_at
            FROM users
            WHERE email = %s
        """, (email,))
        user = cursor.fetchone()

        if not user:
            result["errors"].append(f"User not found: {email}")
            return result

        result["user"] = {
            "id": str(user['id']),
            "email": user['email'],
            "full_name": user['full_name'],
            "role": user['role'],
            "organization_id": str(user['current_organization_id']) if user['current_organization_id'] else None,
            "created_at": str(user['created_at'])
        }

        user_id = str(user['id'])
        org_id = str(user['current_organization_id']) if user['current_organization_id'] else None

        # Check library content
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM library_content
            WHERE user_id = %s
        """, (user_id,))
        content_count = cursor.fetchone()

        cursor.execute("""
            SELECT id, title, content_type, media_url IS NOT NULL as has_media_url,
                   LENGTH(body::text) as body_length, created_at
            FROM library_content
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))
        sample_content = cursor.fetchall()

        result["library_content"] = {
            "total_count": content_count['count'],
            "sample_items": [
                {
                    "id": str(item['id']),
                    "title": item['title'],
                    "content_type": item['content_type'],
                    "has_media_url": item['has_media_url'],
                    "body_length": item['body_length'],
                    "created_at": str(item['created_at'])
                }
                for item in sample_content
            ]
        }

        # Check user-level cloud storage
        cursor.execute("""
            SELECT provider, provider_email, is_active, connected_at,
                   token_expires_at, organization_id
            FROM user_cloud_storage_tokens
            WHERE user_id = %s
            ORDER BY connected_at DESC
        """, (user_id,))
        user_connections = cursor.fetchall()

        result["cloud_storage_user_level"] = [
            {
                "provider": conn_row['provider'],
                "provider_email": conn_row['provider_email'],
                "is_active": conn_row['is_active'],
                "connected_at": str(conn_row['connected_at']),
                "token_expires_at": str(conn_row['token_expires_at']) if conn_row['token_expires_at'] else None,
                "is_expired": conn_row['token_expires_at'] < datetime.now() if conn_row['token_expires_at'] else False,
                "organization_id": str(conn_row['organization_id']) if conn_row['organization_id'] else None
            }
            for conn_row in user_connections
        ]

        # Check org-level cloud storage if user has org
        if org_id:
            cursor.execute("""
                SELECT provider, provider_email, is_active, connected_at,
                       token_expires_at, user_id
                FROM user_cloud_storage_tokens
                WHERE organization_id = %s
                ORDER BY connected_at DESC
            """, (org_id,))
            org_connections = cursor.fetchall()

            result["cloud_storage_org_level"] = [
                {
                    "provider": conn_row['provider'],
                    "provider_email": conn_row['provider_email'],
                    "is_active": conn_row['is_active'],
                    "connected_at": str(conn_row['connected_at']),
                    "token_expires_at": str(conn_row['token_expires_at']) if conn_row['token_expires_at'] else None,
                    "is_expired": conn_row['token_expires_at'] < datetime.now() if conn_row['token_expires_at'] else False,
                    "owner_user_id": str(conn_row['user_id'])
                }
                for conn_row in org_connections
            ]
        else:
            result["cloud_storage_org_level"] = []

    except Exception as e:
        result["errors"].append(f"{type(e).__name__}: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return result
