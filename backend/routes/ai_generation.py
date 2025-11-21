from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Literal
import os
import httpx
import base64
from logger import setup_logger
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from utils.auth import decode_token
from utils.credits import deduct_credits, InsufficientCreditsError
from lib.gcs_storage import upload_bytes_to_gcs

logger = setup_logger(__name__)
router = APIRouter()

@router.get("/test-gcp-auth")
async def test_gcp_auth():
    """Test GCP OAuth2 authentication without making actual API calls"""
    try:
        if not all([GCP_CLIENT_ID, GCP_CLIENT_SECRET, GCP_REFRESH_TOKEN]):
            return {
                "success": False,
                "error": "GCP credentials not configured",
                "details": {
                    "GCP_CLIENT_ID": bool(GCP_CLIENT_ID),
                    "GCP_CLIENT_SECRET": bool(GCP_CLIENT_SECRET),
                    "GCP_REFRESH_TOKEN": bool(GCP_REFRESH_TOKEN)
                }
            }

        # Try to get access token
        access_token = get_access_token()

        return {
            "success": True,
            "message": "GCP OAuth2 authentication successful",
            "token_preview": access_token[:50] + "..." if access_token else None
        }
    except Exception as e:
        logger.error(f"GCP auth test failed: {type(e).__name__}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}",
            "error_type": type(e).__name__
        }

# Load OAuth2 credentials from environment
GCP_CLIENT_ID = os.getenv("GCP_CLIENT_ID")
GCP_CLIENT_SECRET = os.getenv("GCP_CLIENT_SECRET")
GCP_REFRESH_TOKEN = os.getenv("GCP_REFRESH_TOKEN")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "gen-lang-client-0902837589")

if not all([GCP_CLIENT_ID, GCP_CLIENT_SECRET, GCP_REFRESH_TOKEN]):
    logger.warning("⚠️  OAuth2 credentials not fully configured - AI image/video generation will not work")
    logger.warning(f"   GCP_CLIENT_ID: {'✓' if GCP_CLIENT_ID else '✗'}")
    logger.warning(f"   GCP_CLIENT_SECRET: {'✓' if GCP_CLIENT_SECRET else '✗'}")
    logger.warning(f"   GCP_REFRESH_TOKEN: {'✓' if GCP_REFRESH_TOKEN else '✗'}")
else:
    logger.info(f"🔧 OAuth2 configured for Vertex AI (Project: {GCP_PROJECT_ID})")

def get_user_from_request(request: Request) -> str:
    """Extract user_id from JWT token in Authorization header"""
    auth_header = request.headers.get('authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Missing authorization token")

    token = auth_header.replace('Bearer ', '')
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload.get('sub')  # user_id

def get_access_token() -> str:
    """
    Get a fresh access token using the refresh token.

    Access tokens expire after 1 hour, but refresh tokens never expire.
    This function exchanges the refresh token for a new access token.
    """
    try:
        logger.info("🔐 Attempting to refresh GCP access token...")

        # Create credentials from refresh token
        credentials = Credentials(
            token=None,
            refresh_token=GCP_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GCP_CLIENT_ID,
            client_secret=GCP_CLIENT_SECRET,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )

        logger.info("🔄 Calling credentials.refresh()...")
        # Refresh to get a new access token
        credentials.refresh(GoogleAuthRequest())

        if not credentials.token:
            logger.error("❌ Token refresh succeeded but token is None")
            raise HTTPException(
                status_code=503,
                detail="Token refresh succeeded but received no token"
            )

        logger.info(f"✅ Got fresh access token from OAuth2 (length: {len(credentials.token)})")
        return credentials.token

    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e) if str(e) else repr(e)
        logger.error(f"❌ Failed to get access token ({error_type}): {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to authenticate with Google Cloud ({error_type}): {error_msg}"
        )

class ImageGenerateRequest(BaseModel):
    prompt: str
    aspect_ratio: Optional[Literal["1:1", "16:9", "9:16", "4:3", "3:4"]] = "1:1"
    num_images: Optional[int] = 1

class VideoGenerateRequest(BaseModel):
    prompt: str
    duration_seconds: Optional[int] = 8
    resolution: Optional[Literal["720p", "1080p"]] = "720p"

class ImageGenerateResponse(BaseModel):
    success: bool
    image_url: Optional[str] = None
    image_data: Optional[str] = None  # Base64 encoded
    error: Optional[str] = None

class VideoGenerateResponse(BaseModel):
    success: bool
    video_url: Optional[str] = None
    status: Optional[str] = None  # "generating", "complete", "failed"
    job_id: Optional[str] = None
    error: Optional[str] = None

@router.post("/generate-image", response_model=ImageGenerateResponse)
async def generate_image(image_request: ImageGenerateRequest, request: Request):
    """
    Generate an image using Google Imagen 4 Ultra via Vertex AI.

    Imagen 4 Ultra is Google's state-of-the-art text-to-image model:
    - Superior photorealism compared to DALL-E 3
    - Better prompt adherence and understanding
    - More natural lighting and composition
    - Cost: 20 credits per image

    This uses OAuth2 authentication via Vertex AI REST API.

    Args:
        image_request: ImageGenerateRequest with prompt and aspect ratio
        request: FastAPI Request for authentication

    Returns:
        ImageGenerateResponse with base64 encoded image data
    """

    if not all([GCP_CLIENT_ID, GCP_CLIENT_SECRET, GCP_REFRESH_TOKEN]):
        logger.error("❌ OAuth2 credentials not configured")
        raise HTTPException(
            status_code=503,
            detail="OAuth2 credentials not configured. Please add GCP_CLIENT_ID, GCP_CLIENT_SECRET, and GCP_REFRESH_TOKEN to environment variables."
        )

    try:
        # Get user_id from JWT token
        user_id = get_user_from_request(request)

        # Check and deduct credits BEFORE generating (20 credits for ultra quality)
        try:
            deduct_credits(
                user_id=user_id,
                operation_type="ai_image_ultra",
                operation_details={
                    "prompt": image_request.prompt[:100],
                    "aspect_ratio": image_request.aspect_ratio,
                    "model": "imagen-4.0-ultra"
                },
                description=f"Generated AI image (Imagen 4 Ultra) - {image_request.aspect_ratio}"
            )
        except InsufficientCreditsError as e:
            logger.warning(f"❌ Insufficient credits for user {user_id}: {e}")
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "message": f"Insufficient credits. Required: {e.required}, Available: {e.available}",
                    "required": e.required,
                    "available": e.available
                }
            )
        # Get fresh access token
        access_token = get_access_token()

        logger.info(f"🎨 Generating image with Imagen 4 Ultra for user {user_id}: '{image_request.prompt[:60]}...' (aspect: {image_request.aspect_ratio})")

        # Vertex AI Imagen 4 Ultra endpoint (highest quality)
        endpoint = (
            f"https://us-central1-aiplatform.googleapis.com/v1/"
            f"projects/{GCP_PROJECT_ID}/locations/us-central1/"
            f"publishers/google/models/imagen-4.0-ultra-generate-001:predict"
        )

        # Request payload for Imagen 4 Ultra with quality enhancements
        payload = {
            "instances": [{
                "prompt": image_request.prompt
            }],
            "parameters": {
                "sampleCount": image_request.num_images,
                "aspectRatio": image_request.aspect_ratio,
                "sampleImageSize": "2K",  # Maximum resolution
                "enhancePrompt": True,  # AI-enhanced prompts for better quality
                "safetySetting": "block_some",
                "personGeneration": "allow_adult",
                "addWatermark": False,  # No watermark for cleaner images
                "outputOptions": {
                    "mimeType": "image/png"  # PNG for best quality
                }
            }
        }

        # Make the request with OAuth2 bearer token
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }
            )

            logger.info(f"📡 Imagen API response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Extract image from response
                if "predictions" in data and len(data["predictions"]) > 0:
                    prediction = data["predictions"][0]

                    # Image is in bytesBase64Encoded field
                    if "bytesBase64Encoded" in prediction:
                        image_base64 = prediction["bytesBase64Encoded"]
                        logger.info(f"✅ Image generated successfully ({len(image_base64)} chars)")

                        return ImageGenerateResponse(
                            success=True,
                            image_data=f"data:image/png;base64,{image_base64}",
                            image_url=None
                        )
                    else:
                        logger.error(f"❌ No bytesBase64Encoded in response: {prediction.keys()}")
                        return ImageGenerateResponse(
                            success=False,
                            error=f"Unexpected response format. Keys: {list(prediction.keys())}"
                        )
                else:
                    logger.error(f"❌ No predictions in response: {data.keys()}")
                    return ImageGenerateResponse(
                        success=False,
                        error="No images generated. Response missing predictions."
                    )

            elif response.status_code == 403:
                error_text = response.text
                logger.error(f"❌ Imagen API access denied (403): {error_text}")
                return ImageGenerateResponse(
                    success=False,
                    error=f"Access denied to Imagen API. Please ensure:\n1. Vertex AI API is enabled in project {GCP_PROJECT_ID}\n2. Your Google account has 'Vertex AI User' role\n3. Billing is enabled\n\nError: {error_text[:200]}"
                )

            elif response.status_code == 400:
                error_text = response.text
                logger.error(f"❌ Invalid request (400): {error_text}")
                return ImageGenerateResponse(
                    success=False,
                    error=f"Invalid request. Check:\n1. Prompt doesn't violate content policy\n2. Aspect ratio is supported\n\nError: {error_text[:200]}"
                )

            else:
                error_text = response.text
                logger.error(f"❌ Request failed: {response.status_code} - {error_text}")
                return ImageGenerateResponse(
                    success=False,
                    error=f"Image generation failed (HTTP {response.status_code}): {error_text[:200]}"
                )

    except httpx.TimeoutException:
        logger.error("❌ Request timeout after 60 seconds")
        return ImageGenerateResponse(
            success=False,
            error="Image generation timed out. Please try again."
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e) if str(e) else "Unknown error"
        logger.error(f"❌ Image generation error ({error_type}): {error_msg}", exc_info=True)
        return ImageGenerateResponse(
            success=False,
            error=f"Image generation failed ({error_type}): {error_msg}"
        )

@router.post("/generate-video-veo", response_model=VideoGenerateResponse)
async def generate_video_veo(video_request: VideoGenerateRequest, request: Request):
    """
    Generate a video using Google Veo 3.1 via Vertex AI.

    Google Veo 3.1 is Google's state-of-the-art video generation model:
    - Cinematic quality video generation
    - 4, 6, or 8 second videos
    - 720p or 1080p resolution
    - Audio generation included
    - Production-ready quality

    Cost: 200 credits per 8-second video
    Generation time: 2-5 minutes (async long-running operation)

    Args:
        video_request: VideoGenerateRequest with prompt, duration, and resolution
        request: FastAPI Request for authentication

    Returns:
        VideoGenerateResponse with operation ID for status tracking
    """

    if not all([GCP_CLIENT_ID, GCP_CLIENT_SECRET, GCP_REFRESH_TOKEN]):
        logger.error("❌ OAuth2 credentials not configured")
        raise HTTPException(
            status_code=503,
            detail="OAuth2 credentials not configured. Please add GCP_CLIENT_ID, GCP_CLIENT_SECRET, and GCP_REFRESH_TOKEN to environment variables."
        )

    try:
        # Get user_id from JWT token
        user_id = get_user_from_request(request)

        # Check and deduct credits BEFORE generating (200 credits for 8-second video)
        try:
            deduct_credits(
                user_id=user_id,
                operation_type="ai_video_8sec",
                operation_details={
                    "prompt": video_request.prompt[:100],
                    "duration": video_request.duration_seconds,
                    "resolution": video_request.resolution,
                    "model": "veo-3.1"
                },
                description=f"Generated AI video (Veo 3.1) - {video_request.duration_seconds}s, {video_request.resolution}"
            )
        except InsufficientCreditsError as e:
            logger.warning(f"❌ Insufficient credits for user {user_id}: {e}")
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "message": f"Insufficient credits. Required: {e.required}, Available: {e.available}",
                    "required": e.required,
                    "available": e.available
                }
            )
        # Get fresh access token (same as Imagen 3)
        access_token = get_access_token()

        # Ensure duration is 4, 6, or 8 seconds (Veo requirement)
        duration = 8 if video_request.duration_seconds > 6 else (6 if video_request.duration_seconds > 4 else 4)

        logger.info(f"🎬 Generating video with Veo 3.1 for user {user_id}: '{video_request.prompt[:60]}...' ({duration}s, {video_request.resolution})")

        # Vertex AI Veo 3.1 endpoint
        endpoint = (
            f"https://us-central1-aiplatform.googleapis.com/v1/"
            f"projects/{GCP_PROJECT_ID}/locations/us-central1/"
            f"publishers/google/models/veo-3.1-generate-preview:predictLongRunning"
        )

        # Request payload for Veo 3.1
        payload = {
            "instances": [{
                "prompt": video_request.prompt
            }],
            "parameters": {
                "durationSeconds": duration,
                "resolution": video_request.resolution,
                "generateAudio": True,  # Required for Veo 3
                "sampleCount": 1,
                "aspectRatio": "16:9",
                "enhancePrompt": True,
                "personGeneration": "allow_adult"
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }
            )

            logger.info(f"📡 Veo API response status: {response.status_code}")
            logger.info(f"📡 Veo API response body: {response.text[:500]}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"📊 Full Veo response data: {data}")

                # Extract operation name (long-running operation ID)
                operation_name = data.get("name")

                if not operation_name:
                    logger.error(f"❌ No operation name in response! Keys: {list(data.keys())}")
                    return VideoGenerateResponse(
                        success=False,
                        error=f"No operation ID returned from Veo. Response keys: {list(data.keys())}",
                        status="failed"
                    )

                logger.info(f"✅ Video generation task created: {operation_name}")

                return VideoGenerateResponse(
                    success=True,
                    status="generating",
                    job_id=operation_name  # Store operation name as job_id
                )

            elif response.status_code == 403:
                error_text = response.text
                logger.error(f"❌ Veo API access denied (403): {error_text}")
                return VideoGenerateResponse(
                    success=False,
                    error=f"Access denied to Veo API. This likely means:\n1. Your GCP account needs Veo 3.1 allowlist approval\n2. Apply at: https://cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-1-generate-preview\n3. Vertex AI API may not be enabled\n\nError: {error_text[:200]}",
                    status="failed"
                )

            elif response.status_code == 400:
                error_text = response.text
                logger.error(f"❌ Invalid request (400): {error_text}")
                return VideoGenerateResponse(
                    success=False,
                    error=f"Invalid request. Check:\n1. Prompt doesn't violate content policy\n2. Duration is 4, 6, or 8 seconds\n\nError: {error_text[:200]}",
                    status="failed"
                )

            else:
                error_text = response.text
                logger.error(f"❌ Veo request failed: {response.status_code} - {error_text}")
                return VideoGenerateResponse(
                    success=False,
                    error=f"Video generation failed (HTTP {response.status_code}): {error_text[:200]}",
                    status="failed"
                )

    except httpx.TimeoutException:
        logger.error("❌ Veo request timeout")
        return VideoGenerateResponse(
            success=False,
            error="Video generation request timed out. Please try again.",
            status="failed"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Veo video generation error: {str(e)}", exc_info=True)
        return VideoGenerateResponse(
            success=False,
            error=f"Video generation failed: {str(e)}",
            status="failed"
        )

@router.get("/veo-status/{operation_name:path}")
async def get_veo_status(operation_name: str):
    """
    Check status of Google Veo 3.1 video generation operation.

    Args:
        operation_name: The operation name returned from generate_video_veo

    Returns:
        Dict with status and video_url (when complete)
    """

    if not all([GCP_CLIENT_ID, GCP_CLIENT_SECRET, GCP_REFRESH_TOKEN]):
        raise HTTPException(status_code=503, detail="OAuth2 credentials not configured")

    try:
        # Get fresh access token
        access_token = get_access_token()

        logger.info(f"🔍 Checking Veo operation status: {operation_name[:80]}...")

        # Vertex AI Veo status endpoint - uses fetchPredictOperation
        endpoint = (
            f"https://us-central1-aiplatform.googleapis.com/v1/"
            f"projects/{GCP_PROJECT_ID}/locations/us-central1/"
            f"publishers/google/models/veo-3.1-generate-preview:fetchPredictOperation"
        )

        payload = {
            "operationName": operation_name
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(f"📊 Full Veo operation response: {data}")

                # Check if operation is done
                done = data.get("done", False)
                logger.info(f"🔍 Operation done: {done}")

                if done:
                    # Check for error
                    if "error" in data:
                        error_msg = data["error"].get("message", "Unknown error")
                        logger.error(f"❌ Veo operation failed: {error_msg}")
                        return {
                            "success": False,
                            "status": "failed",
                            "error": f"Video generation failed: {error_msg}"
                        }

                    # Extract video URL from response
                    response_data = data.get("response", {})
                    logger.info(f"🔍 Response data keys: {response_data.keys()}")

                    videos = response_data.get("videos", [])
                    logger.info(f"🔍 Videos count: {len(videos)}")

                    if videos and len(videos) > 0:
                        video = videos[0]
                        logger.info(f"🔍 Video keys: {video.keys()}")
                        logger.info(f"🔍 Full video: {video}")

                        # Video is in bytesBase64Encoded or gcsUri
                        video_base64 = video.get("bytesBase64Encoded")
                        gcs_uri = video.get("gcsUri")

                        # CRITICAL: Download and upload to permanent storage
                        # Veo GCS URIs contain JWT tokens that expire, causing 401 errors
                        # Users pay for these videos - they must never expire!
                        permanent_url = None

                        if video_base64:
                            logger.info(f"📦 Veo video in base64 format ({len(video_base64)} chars)")
                            try:
                                # Decode base64 video
                                video_bytes = base64.b64decode(video_base64)
                                logger.info(f"📦 Decoded video: {len(video_bytes)} bytes")

                                # Upload to permanent GCS storage
                                permanent_url = upload_bytes_to_gcs(
                                    file_bytes=video_bytes,
                                    filename="veo-video.mp4",
                                    destination_folder="ai-videos",
                                    content_type="video/mp4",
                                    make_public=True
                                )

                                if permanent_url:
                                    logger.info(f"✅ Veo video saved to permanent storage: {permanent_url}")
                                else:
                                    logger.warning("⚠️ Failed to upload to permanent storage, falling back to base64")
                                    permanent_url = f"data:video/mp4;base64,{video_base64}"

                            except Exception as e:
                                logger.error(f"❌ Failed to process base64 video: {e}")
                                permanent_url = f"data:video/mp4;base64,{video_base64}"

                        elif gcs_uri:
                            logger.info(f"📦 Veo video in GCS URI format: {gcs_uri}")
                            try:
                                # Download video from temporary GCS URI (has JWT token)
                                async with httpx.AsyncClient(timeout=120.0) as client:
                                    download_response = await client.get(gcs_uri)

                                    if download_response.status_code == 200:
                                        video_bytes = download_response.content
                                        logger.info(f"📥 Downloaded video: {len(video_bytes)} bytes")

                                        # Upload to permanent GCS storage
                                        permanent_url = upload_bytes_to_gcs(
                                            file_bytes=video_bytes,
                                            filename="veo-video.mp4",
                                            destination_folder="ai-videos",
                                            content_type="video/mp4",
                                            make_public=True
                                        )

                                        if permanent_url:
                                            logger.info(f"✅ Veo video saved to permanent storage: {permanent_url}")
                                        else:
                                            logger.error("❌ Failed to upload to permanent storage")
                                            permanent_url = gcs_uri  # Fallback to temporary URI
                                    else:
                                        logger.error(f"❌ Failed to download video: {download_response.status_code}")
                                        permanent_url = gcs_uri  # Fallback to temporary URI

                            except Exception as e:
                                logger.error(f"❌ Failed to download/upload video: {e}")
                                permanent_url = gcs_uri  # Fallback to temporary URI

                        if permanent_url:
                            return {
                                "success": True,
                                "status": "complete",
                                "video_url": permanent_url,
                                "done": True
                            }

                    logger.error(f"❌ Veo succeeded but no video in videos array. Full response: {data}")
                    return {
                        "success": False,
                        "error": "Video generation succeeded but no video returned"
                    }

                else:
                    # Still generating
                    logger.info(f"⏳ Veo video still generating")
                    return {
                        "success": True,
                        "status": "generating",
                        "done": False
                    }

            else:
                logger.error(f"❌ Veo status check failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Status check failed: {response.text[:200]}"
                }

    except Exception as e:
        logger.error(f"❌ Veo status check error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/repair-veo-video")
async def repair_veo_video(request: Request):
    """
    Repair a Veo video that has an expired JWT token URL.

    This endpoint attempts to download the video from the expired URL
    and re-upload it to permanent storage. If download fails (401),
    the video cannot be recovered.

    Request body:
        {
            "video_url": "https://...gcs_uri_with_jwt...",
            "content_id": "abc123"  # optional, for logging
        }

    Returns:
        {
            "success": bool,
            "permanent_url": str,  # new permanent URL if successful
            "error": str  # error message if failed
        }
    """
    try:
        body = await request.json()
        video_url = body.get("video_url")
        content_id = body.get("content_id", "unknown")

        if not video_url:
            raise HTTPException(status_code=400, detail="video_url is required")

        logger.info(f"🔧 Attempting to repair Veo video (content_id: {content_id})")
        logger.info(f"   Original URL: {video_url[:100]}...")

        # If it's a base64 data URL, it's already permanent
        if video_url.startswith("data:video/"):
            return {
                "success": True,
                "permanent_url": video_url,
                "message": "Video is already in permanent base64 format"
            }

        # If it's already in our permanent storage, return it
        if "storage.googleapis.com" in video_url and "ai-videos" in video_url:
            return {
                "success": True,
                "permanent_url": video_url,
                "message": "Video is already in permanent GCS storage"
            }

        # Try to download the video (may fail if JWT expired)
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.info("📥 Downloading video from temporary URL...")
                download_response = await client.get(video_url)

                if download_response.status_code == 200:
                    video_bytes = download_response.content
                    logger.info(f"✅ Downloaded video: {len(video_bytes)} bytes")

                    # Upload to permanent storage
                    permanent_url = upload_bytes_to_gcs(
                        file_bytes=video_bytes,
                        filename="veo-video.mp4",
                        destination_folder="ai-videos",
                        content_type="video/mp4",
                        make_public=True
                    )

                    if permanent_url:
                        logger.info(f"✅ Video repaired and saved: {permanent_url}")
                        return {
                            "success": True,
                            "permanent_url": permanent_url,
                            "message": "Video successfully repaired and uploaded to permanent storage"
                        }
                    else:
                        logger.error("❌ Failed to upload to permanent storage")
                        return {
                            "success": False,
                            "error": "Failed to upload video to permanent storage"
                        }

                elif download_response.status_code == 401:
                    logger.error(f"❌ Video URL has expired (401 Unauthorized)")
                    return {
                        "success": False,
                        "error": "Video URL has expired and cannot be recovered. The video must be regenerated.",
                        "expired": True
                    }
                else:
                    logger.error(f"❌ Failed to download video: {download_response.status_code}")
                    return {
                        "success": False,
                        "error": f"Failed to download video (HTTP {download_response.status_code})"
                    }

        except Exception as download_error:
            logger.error(f"❌ Download error: {str(download_error)}")
            return {
                "success": False,
                "error": f"Failed to download video: {str(download_error)}"
            }

    except Exception as e:
        logger.error(f"❌ Video repair error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

