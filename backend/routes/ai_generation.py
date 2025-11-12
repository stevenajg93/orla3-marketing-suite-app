from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
import os
import httpx
import base64
from logger import setup_logger
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest

logger = setup_logger(__name__)
router = APIRouter()

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

def get_access_token() -> str:
    """
    Get a fresh access token using the refresh token.

    Access tokens expire after 1 hour, but refresh tokens never expire.
    This function exchanges the refresh token for a new access token.
    """
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

        logger.info("✅ Got fresh access token from OAuth2")
        return credentials.token

    except Exception as e:
        logger.error(f"❌ Failed to get access token: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to authenticate with Google Cloud: {str(e)}"
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
async def generate_image(request: ImageGenerateRequest):
    """
    Generate an image using Google Imagen 3 (Nano Banana) via Vertex AI.

    Imagen 3 is Google's state-of-the-art text-to-image model:
    - Superior photorealism compared to DALL-E 3
    - Better prompt adherence and understanding
    - More natural lighting and composition
    - Cost: $0.02-0.04 per image

    This uses OAuth2 authentication via Vertex AI REST API.

    Args:
        request: ImageGenerateRequest with prompt and aspect ratio

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
        # Get fresh access token
        access_token = get_access_token()

        logger.info(f"🎨 Generating image with Imagen 4 Ultra: '{request.prompt[:60]}...' (aspect: {request.aspect_ratio})")

        # Vertex AI Imagen 4 Ultra endpoint (highest quality)
        endpoint = (
            f"https://us-central1-aiplatform.googleapis.com/v1/"
            f"projects/{GCP_PROJECT_ID}/locations/us-central1/"
            f"publishers/google/models/imagen-4.0-ultra-generate-001:predict"
        )

        # Request payload for Imagen 4 Ultra with quality enhancements
        payload = {
            "instances": [{
                "prompt": request.prompt
            }],
            "parameters": {
                "sampleCount": request.num_images,
                "aspectRatio": request.aspect_ratio,
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
        logger.error(f"❌ Image generation error: {str(e)}", exc_info=True)
        return ImageGenerateResponse(
            success=False,
            error=f"Image generation failed: {str(e)}"
        )

@router.post("/generate-video-veo", response_model=VideoGenerateResponse)
async def generate_video_veo(request: VideoGenerateRequest):
    """
    Generate a video using Google Veo 3.1 via Vertex AI.

    Google Veo 3.1 is Google's state-of-the-art video generation model:
    - Cinematic quality video generation
    - 4, 6, or 8 second videos
    - 720p or 1080p resolution
    - Audio generation included
    - Production-ready quality

    Cost: $6 per 8-second video (via credits)
    Generation time: 2-5 minutes (async long-running operation)

    Args:
        request: VideoGenerateRequest with prompt, duration, and resolution

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
        # Get fresh access token (same as Imagen 3)
        access_token = get_access_token()

        # Ensure duration is 4, 6, or 8 seconds (Veo requirement)
        duration = 8 if request.duration_seconds > 6 else (6 if request.duration_seconds > 4 else 4)

        logger.info(f"🎬 Generating video with Veo 3.1: '{request.prompt[:60]}...' ({duration}s, {request.resolution})")

        # Vertex AI Veo 3.1 endpoint
        endpoint = (
            f"https://us-central1-aiplatform.googleapis.com/v1/"
            f"projects/{GCP_PROJECT_ID}/locations/us-central1/"
            f"publishers/google/models/veo-3.1-generate-preview:predictLongRunning"
        )

        # Request payload for Veo 3.1
        payload = {
            "instances": [{
                "prompt": request.prompt
            }],
            "parameters": {
                "durationSeconds": duration,
                "resolution": request.resolution,
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

                        if video_base64:
                            logger.info(f"✅ Veo video generation complete (base64, {len(video_base64)} chars)")
                            return {
                                "success": True,
                                "status": "complete",
                                "video_url": f"data:video/mp4;base64,{video_base64}",
                                "done": True
                            }
                        else:
                            gcs_uri = video.get("gcsUri")
                            if gcs_uri:
                                logger.info(f"✅ Veo video generation complete: {gcs_uri}")
                                return {
                                    "success": True,
                                    "status": "complete",
                                    "video_url": gcs_uri,
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

