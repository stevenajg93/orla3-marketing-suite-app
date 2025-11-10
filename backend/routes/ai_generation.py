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

# Load Runway ML API key
RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY")

if not all([GCP_CLIENT_ID, GCP_CLIENT_SECRET, GCP_REFRESH_TOKEN]):
    logger.warning("⚠️  OAuth2 credentials not fully configured - AI image generation will not work")
    logger.warning(f"   GCP_CLIENT_ID: {'✓' if GCP_CLIENT_ID else '✗'}")
    logger.warning(f"   GCP_CLIENT_SECRET: {'✓' if GCP_CLIENT_SECRET else '✗'}")
    logger.warning(f"   GCP_REFRESH_TOKEN: {'✓' if GCP_REFRESH_TOKEN else '✗'}")
else:
    logger.info(f"🔧 OAuth2 configured for Vertex AI (Project: {GCP_PROJECT_ID})")

if not RUNWAY_API_KEY:
    logger.warning("⚠️  RUNWAY_API_KEY not configured - AI video generation will not work")
else:
    logger.info(f"🎬 Runway ML API key configured")

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

        logger.info(f"🎨 Generating image with Imagen 3: '{request.prompt[:60]}...' (aspect: {request.aspect_ratio})")

        # Vertex AI Imagen 3 endpoint
        endpoint = (
            f"https://us-central1-aiplatform.googleapis.com/v1/"
            f"projects/{GCP_PROJECT_ID}/locations/us-central1/"
            f"publishers/google/models/imagegeneration@006:predict"
        )

        # Request payload for Imagen 3
        payload = {
            "instances": [{
                "prompt": request.prompt
            }],
            "parameters": {
                "sampleCount": request.num_images,
                "aspectRatio": request.aspect_ratio,
                "safetyFilterLevel": "block_some",
                "personGeneration": "allow_adult"
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

@router.post("/generate-video", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    """
    Generate a video using Runway ML Gen-3 Alpha Turbo.

    Runway ML is the industry-leading AI video generation platform:
    - Used by Hollywood studios and top creators
    - Best-in-class quality and consistency
    - Reliable production-ready API
    - 5 or 10 second video clips

    Cost: ~$0.10 per 5-second video (~$12 per 100 videos)
    Generation time: 1-3 minutes (async operation)

    Args:
        request: VideoGenerateRequest with prompt and duration

    Returns:
        VideoGenerateResponse with task ID for status tracking
    """

    if not RUNWAY_API_KEY:
        logger.error("❌ Runway ML API key not configured")
        raise HTTPException(
            status_code=503,
            detail="RUNWAY_API_KEY not configured. Please add to environment variables."
        )

    try:
        # Map duration to Runway's supported values (5 or 10 seconds)
        runway_duration = 5 if request.duration_seconds <= 5 else 10

        # Map resolution to pixel dimensions
        runway_ratio = "1920:1080" if request.resolution == "1080p" else "1280:720"

        logger.info(f"🎬 Generating video with Runway Veo 3.1: '{request.prompt[:60]}...' ({runway_duration}s, {request.resolution})")

        # Runway ML API endpoint (correct base URL)
        endpoint = "https://api.dev.runwayml.com/v1/text_to_video"

        # Request payload for Runway Veo 3.1
        # Model: veo3.1, Ratio: pixel dimensions (not aspect ratio)
        payload = {
            "model": "veo3.1",
            "promptText": request.prompt,
            "duration": runway_duration,
            "ratio": runway_ratio
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {RUNWAY_API_KEY}",
                    "Content-Type": "application/json",
                    "X-Runway-Version": "2024-11-06"
                }
            )

            logger.info(f"📡 Runway API response status: {response.status_code}")

            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                task_id = data.get("id")

                logger.info(f"✅ Video generation task created: {task_id}")

                return VideoGenerateResponse(
                    success=True,
                    status="generating",
                    job_id=task_id
                )

            elif response.status_code == 401:
                logger.error(f"❌ Runway API authentication failed")
                return VideoGenerateResponse(
                    success=False,
                    error="Runway ML API key is invalid. Please check your RUNWAY_API_KEY environment variable.",
                    status="failed"
                )

            elif response.status_code == 402:
                logger.error(f"❌ Runway API insufficient credits")
                return VideoGenerateResponse(
                    success=False,
                    error="Insufficient Runway ML credits. Please add credits at https://app.runwayml.com/",
                    status="failed"
                )

            elif response.status_code == 400:
                error_text = response.text
                logger.error(f"❌ Invalid request (400): {error_text}")
                return VideoGenerateResponse(
                    success=False,
                    error=f"Invalid request. Check:\n1. Prompt doesn't violate content policy\n2. Video duration is supported\n\nError: {error_text[:200]}",
                    status="failed"
                )

            else:
                error_text = response.text
                logger.error(f"❌ Runway request failed: {response.status_code} - {error_text}")
                return VideoGenerateResponse(
                    success=False,
                    error=f"Video generation failed (HTTP {response.status_code}): {error_text[:200]}",
                    status="failed"
                )

    except httpx.TimeoutException:
        logger.error("❌ Runway request timeout")
        return VideoGenerateResponse(
            success=False,
            error="Video generation request timed out. Please try again.",
            status="failed"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Video generation error: {str(e)}", exc_info=True)
        return VideoGenerateResponse(
            success=False,
            error=f"Video generation failed: {str(e)}",
            status="failed"
        )

@router.get("/video-status/{job_id:path}")
async def get_video_status(job_id: str):
    """
    Check status of Runway ML video generation task.

    Args:
        job_id: The task ID returned from generate_video

    Returns:
        Dict with status and video_url (when complete)
    """

    if not RUNWAY_API_KEY:
        raise HTTPException(status_code=503, detail="RUNWAY_API_KEY not configured")

    try:
        logger.info(f"🔍 Checking Runway video status for task: {job_id}")

        # Runway ML task status endpoint (correct base URL)
        endpoint = f"https://api.dev.runwayml.com/v1/tasks/{job_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                endpoint,
                headers={
                    "Authorization": f"Bearer {RUNWAY_API_KEY}",
                    "X-Runway-Version": "2024-11-06"
                }
            )

            if response.status_code == 200:
                data = response.json()
                task_status = data.get("status")  # "PENDING", "RUNNING", "SUCCEEDED", "FAILED"

                logger.info(f"📊 Runway task status: {task_status}")

                if task_status == "SUCCEEDED":
                    # Extract video URL from response
                    video_url = data.get("output", [None])[0] if data.get("output") else None

                    if video_url:
                        logger.info(f"✅ Video generation complete: {video_url}")
                        return {
                            "success": True,
                            "status": "complete",
                            "video_url": video_url,
                            "done": True
                        }
                    else:
                        logger.error(f"❌ Video succeeded but no URL: {data}")
                        return {
                            "success": False,
                            "error": "Video generation succeeded but no video URL returned"
                        }

                elif task_status == "FAILED":
                    error_msg = data.get("failure") or "Unknown error"
                    logger.error(f"❌ Video generation failed: {error_msg}")
                    return {
                        "success": False,
                        "status": "failed",
                        "error": f"Video generation failed: {error_msg}"
                    }

                elif task_status in ["PENDING", "RUNNING"]:
                    logger.info(f"⏳ Video still generating ({task_status})")
                    progress = data.get("progress", 0)
                    return {
                        "success": True,
                        "status": "generating",
                        "done": False,
                        "progress": progress
                    }

                else:
                    logger.warning(f"⚠️  Unknown status: {task_status}")
                    return {
                        "success": True,
                        "status": "generating",
                        "done": False
                    }

            elif response.status_code == 404:
                logger.error(f"❌ Task not found: {job_id}")
                return {
                    "success": False,
                    "error": "Video generation task not found"
                }

            else:
                logger.error(f"❌ Status check failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Status check failed: {response.text[:200]}"
                }

    except Exception as e:
        logger.error(f"❌ Video status check error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
