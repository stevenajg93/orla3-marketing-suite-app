"""
Google Cloud Storage utility for persistent file storage.
Handles uploading brand assets (logos, images) to GCS bucket.
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from google.cloud import storage
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest

# GCS Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "gen-lang-client-0902837589")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", f"{GCP_PROJECT_ID}-brand-assets")

# OAuth2 Credentials (same as used for Imagen/Veo)
GCP_CLIENT_ID = os.getenv("GCP_CLIENT_ID")
GCP_CLIENT_SECRET = os.getenv("GCP_CLIENT_SECRET")
GCP_REFRESH_TOKEN = os.getenv("GCP_REFRESH_TOKEN")


def get_gcs_client() -> Optional[storage.Client]:
    """
    Get authenticated GCS client using OAuth2 refresh token.
    Returns None if credentials are not configured.
    """
    if not all([GCP_CLIENT_ID, GCP_CLIENT_SECRET, GCP_REFRESH_TOKEN]):
        print("⚠️  GCS not configured - OAuth2 credentials missing")
        return None

    try:
        # Create credentials from refresh token
        credentials = Credentials(
            token=None,
            refresh_token=GCP_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GCP_CLIENT_ID,
            client_secret=GCP_CLIENT_SECRET,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )

        # Refresh to get a new access token
        credentials.refresh(GoogleAuthRequest())

        # Create GCS client
        client = storage.Client(
            project=GCP_PROJECT_ID,
            credentials=credentials
        )

        print(f"✅ GCS client initialized (Bucket: {GCS_BUCKET_NAME})")
        return client

    except Exception as e:
        print(f"❌ Failed to initialize GCS client: {str(e)}")
        return None


def upload_file_to_gcs(
    file_path: str,
    destination_folder: str = "logos",
    make_public: bool = True
) -> Optional[str]:
    """
    Upload a file to Google Cloud Storage.

    Args:
        file_path: Local file path to upload
        destination_folder: Folder in GCS bucket (e.g., 'logos', 'guidelines')
        make_public: Whether to make the file publicly accessible

    Returns:
        Public URL of uploaded file, or None if upload failed
    """
    client = get_gcs_client()
    if not client:
        return None

    try:
        # Get or create bucket
        try:
            bucket = client.get_bucket(GCS_BUCKET_NAME)
        except Exception:
            # Bucket doesn't exist, create it
            bucket = client.create_bucket(GCS_BUCKET_NAME, location="us-central1")
            print(f"✅ Created GCS bucket: {GCS_BUCKET_NAME}")

        # Generate unique filename to avoid collisions
        file_extension = Path(file_path).suffix
        unique_filename = f"{destination_folder}/{uuid.uuid4()}{file_extension}"

        # Upload file
        blob = bucket.blob(unique_filename)
        blob.upload_from_filename(file_path)

        # Make public if requested
        if make_public:
            blob.make_public()

        public_url = blob.public_url
        print(f"✅ Uploaded to GCS: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ GCS upload failed: {str(e)}")
        return None


def upload_bytes_to_gcs(
    file_bytes: bytes,
    filename: str,
    destination_folder: str = "logos",
    content_type: str = "image/png",
    make_public: bool = True
) -> Optional[str]:
    """
    Upload file bytes to Google Cloud Storage.

    Args:
        file_bytes: File content as bytes
        filename: Original filename (for extension)
        destination_folder: Folder in GCS bucket
        content_type: MIME type of file
        make_public: Whether to make the file publicly accessible

    Returns:
        Public URL of uploaded file, or None if upload failed
    """
    client = get_gcs_client()
    if not client:
        return None

    try:
        # Get or create bucket
        try:
            bucket = client.get_bucket(GCS_BUCKET_NAME)
        except Exception:
            bucket = client.create_bucket(GCS_BUCKET_NAME, location="us-central1")
            print(f"✅ Created GCS bucket: {GCS_BUCKET_NAME}")

        # Generate unique filename
        file_extension = Path(filename).suffix
        unique_filename = f"{destination_folder}/{uuid.uuid4()}{file_extension}"

        # Upload bytes
        blob = bucket.blob(unique_filename)
        blob.upload_from_string(file_bytes, content_type=content_type)

        # Make public if requested
        if make_public:
            blob.make_public()

        public_url = blob.public_url
        print(f"✅ Uploaded to GCS: {public_url}")
        return public_url

    except Exception as e:
        print(f"❌ GCS upload failed: {str(e)}")
        return None


def delete_file_from_gcs(gcs_url: str) -> bool:
    """
    Delete a file from Google Cloud Storage.

    Args:
        gcs_url: Public URL of file to delete

    Returns:
        True if deleted successfully, False otherwise
    """
    client = get_gcs_client()
    if not client:
        return False

    try:
        # Extract blob name from URL
        # Format: https://storage.googleapis.com/{bucket}/{blob_path}
        if "storage.googleapis.com" not in gcs_url:
            return False

        parts = gcs_url.split(f"{GCS_BUCKET_NAME}/")
        if len(parts) != 2:
            return False

        blob_name = parts[1]

        # Delete blob
        bucket = client.get_bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.delete()

        print(f"✅ Deleted from GCS: {blob_name}")
        return True

    except Exception as e:
        print(f"❌ GCS delete failed: {str(e)}")
        return False


def is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension."""
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'}
    return Path(filename).suffix.lower() in image_extensions


def is_video_file(filename: str) -> bool:
    """Check if file is a video based on extension."""
    video_extensions = {'.mp4', '.mov', '.avi', '.webm', '.mkv'}
    return Path(filename).suffix.lower() in video_extensions
