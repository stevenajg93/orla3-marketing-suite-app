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
