"""
Media upload utilities for social media platforms
Handles video/image uploads, chunking, validation
"""
import httpx
import asyncio
from typing import Optional, Dict, BinaryIO
import logging
import os
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)


class MediaUploadError(Exception):
    """Custom exception for media upload errors"""
    pass


# Platform-specific media limits
MEDIA_LIMITS = {
    "tiktok": {
        "video_max_size_mb": 287,  # TikTok max video size
        "video_max_duration_seconds": 600,  # 10 minutes
        "supported_formats": ["mp4", "mov", "mpeg", "avi", "webm"]
    },
    "youtube": {
        "video_max_size_mb": 256000,  # 256 GB (YouTube max)
        "video_max_duration_seconds": 43200,  # 12 hours
        "supported_formats": ["mp4", "mov", "mpeg", "avi", "wmv", "flv", "webm"]
    },
    "twitter": {
        "image_max_size_mb": 5,
        "video_max_size_mb": 512,
        "video_max_duration_seconds": 140,
        "max_images": 4,
        "supported_image_formats": ["jpg", "jpeg", "png", "gif", "webp"],
        "supported_video_formats": ["mp4", "mov"]
    },
    "linkedin": {
        "image_max_size_mb": 10,
        "video_max_size_mb": 5120,  # 5 GB
        "video_max_duration_seconds": 600,  # 10 minutes
        "supported_image_formats": ["jpg", "jpeg", "png", "gif"],
        "supported_video_formats": ["mp4", "mov", "wmv", "flv", "avi"]
    },
    "reddit": {
        "image_max_size_mb": 20,
        "video_max_size_mb": 1024,  # 1 GB
        "supported_image_formats": ["jpg", "jpeg", "png", "gif"],
        "supported_video_formats": ["mp4", "mov"]
    }
}


def validate_media_file(file_path: str, platform: str, media_type: str = "image") -> bool:
    """
    Validate media file meets platform requirements

    Args:
        file_path: Path to media file
        platform: Platform name (tiktok, youtube, twitter, etc.)
        media_type: "image" or "video"

    Returns:
        bool: True if valid

    Raises:
        MediaUploadError: If validation fails
    """
    if not os.path.exists(file_path):
        raise MediaUploadError(f"File not found: {file_path}")

    # Get file size in MB
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    # Get file extension
    file_ext = Path(file_path).suffix.lstrip('.').lower()

    # Get platform limits
    limits = MEDIA_LIMITS.get(platform, {})

    if media_type == "video":
        max_size = limits.get("video_max_size_mb", 1000)
        supported_formats = limits.get("supported_formats", limits.get("supported_video_formats", []))

        if file_size_mb > max_size:
            raise MediaUploadError(f"{platform} video must be under {max_size}MB (file is {file_size_mb:.1f}MB)")

        if file_ext not in supported_formats:
            raise MediaUploadError(f"{platform} only supports {', '.join(supported_formats)} video formats")

    elif media_type == "image":
        max_size = limits.get("image_max_size_mb", 10)
        supported_formats = limits.get("supported_image_formats", ["jpg", "jpeg", "png", "gif"])

        if file_size_mb > max_size:
            raise MediaUploadError(f"{platform} image must be under {max_size}MB (file is {file_size_mb:.1f}MB)")

        if file_ext not in supported_formats:
            raise MediaUploadError(f"{platform} only supports {', '.join(supported_formats)} image formats")

    return True


async def chunked_upload(
    url: str,
    file_path: str,
    chunk_size: int = 5 * 1024 * 1024,  # 5MB chunks
    headers: Optional[Dict] = None,
    method: str = "POST"
) -> httpx.Response:
    """
    Upload large file in chunks
    Used for TikTok, YouTube large videos

    Args:
        url: Upload URL
        file_path: Path to file
        chunk_size: Size of each chunk in bytes
        headers: HTTP headers
        method: HTTP method (POST/PUT)

    Returns:
        httpx.Response: Final response
    """
    file_size = os.path.getsize(file_path)
    headers = headers or {}

    async with httpx.AsyncClient(timeout=300.0) as client:
        with open(file_path, 'rb') as f:
            offset = 0
            while offset < file_size:
                chunk = f.read(chunk_size)
                chunk_headers = {
                    **headers,
                    'Content-Range': f'bytes {offset}-{offset + len(chunk) - 1}/{file_size}',
                    'Content-Length': str(len(chunk))
                }

                if method == "POST":
                    response = await client.post(url, content=chunk, headers=chunk_headers)
                else:
                    response = await client.put(url, content=chunk, headers=chunk_headers)

                if response.status_code not in [200, 201, 202, 308]:  # 308 = Resume Incomplete
                    raise MediaUploadError(f"Chunk upload failed: {response.status_code} - {response.text}")

                offset += len(chunk)
                logger.info(f"Uploaded {offset}/{file_size} bytes ({(offset/file_size)*100:.1f}%)")

    return response


async def upload_twitter_media(file_path: str, access_token: str, media_type: str = "image") -> str:
    """
    Upload media to Twitter using v1.1 API (v2 doesn't support media yet)

    Args:
        file_path: Path to media file
        access_token: Twitter OAuth 2.0 access token
        media_type: "image" or "video"

    Returns:
        str: media_id_string
    """
    validate_media_file(file_path, "twitter", media_type)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Twitter v1.1 media upload
        with open(file_path, 'rb') as f:
            files = {'media': f}

            # Note: Twitter v1.1 requires OAuth 1.0a, but we're using OAuth 2.0
            # This is a simplified version - production would need OAuth 1.0a signing
            response = await client.post(
                "https://upload.twitter.com/1.1/media/upload.json",
                headers={"Authorization": f"Bearer {access_token}"},
                files=files
            )

            if response.status_code != 200:
                raise MediaUploadError(f"Twitter media upload failed: {response.status_code} - {response.text}")

            data = response.json()
            return data['media_id_string']


async def upload_linkedin_image(file_path: str, access_token: str, person_urn: str) -> str:
    """
    Upload image to LinkedIn using asset registration

    Args:
        file_path: Path to image file
        access_token: LinkedIn OAuth 2.0 access token
        person_urn: LinkedIn person URN (urn:li:person:XXXXX)

    Returns:
        str: asset URN
    """
    validate_media_file(file_path, "linkedin", "image")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Register upload
        register_payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": person_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }

        register_response = await client.post(
            "https://api.linkedin.com/v2/assets?action=registerUpload",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=register_payload
        )

        if register_response.status_code != 200:
            raise MediaUploadError(f"LinkedIn asset registration failed: {register_response.status_code}")

        register_data = register_response.json()
        upload_url = register_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = register_data['value']['asset']

        # Step 2: Upload image binary
        with open(file_path, 'rb') as f:
            upload_response = await client.put(
                upload_url,
                headers={"Authorization": f"Bearer {access_token}"},
                content=f.read()
            )

            if upload_response.status_code != 201:
                raise MediaUploadError(f"LinkedIn image upload failed: {upload_response.status_code}")

        return asset_urn


async def download_url_to_file(url: str, output_path: str) -> str:
    """
    Download file from URL to local path
    Used when media is hosted remotely

    Args:
        url: Source URL
        output_path: Destination file path

    Returns:
        str: output_path
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url)

        if response.status_code != 200:
            raise MediaUploadError(f"Failed to download {url}: {response.status_code}")

        with open(output_path, 'wb') as f:
            f.write(response.content)

        return output_path


def get_mime_type(file_path: str) -> str:
    """Get MIME type from file path"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'
