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
    logger.warning("⚠️  OAuth2 credentials not fully configured - AI generation will not work")
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
    Generate a video using Google Veo via Vertex AI.

    Google Veo is Google's experimental video generation model.
    Note: Veo may require special preview access in your GCP project.

    Cost: ~$6 per 8-second video with audio (when available)
    Generation time: 2-5 minutes (async operation)

    Args:
        request: VideoGenerateRequest with prompt, duration, and resolution

    Returns:
        VideoGenerateResponse with operation ID for status tracking
    """

    if not all([GCP_CLIENT_ID, GCP_CLIENT_SECRET, GCP_REFRESH_TOKEN]):
        logger.error("❌ OAuth2 credentials not configured")
        raise HTTPException(
            status_code=503,
            detail="OAuth2 credentials not configured."
        )

    try:
        # Get fresh access token
        access_token = get_access_token()

        logger.info(f"🎬 Generating video with Veo: '{request.prompt[:60]}...' ({request.resolution})")

        # Vertex AI Veo endpoint (experimental)
        endpoint = (
            f"https://us-central1-aiplatform.googleapis.com/v1/"
            f"projects/{GCP_PROJECT_ID}/locations/us-central1/"
            f"publishers/google/models/veo-001:predict"
        )

        # Request payload for Veo
        payload = {
            "instances": [{
                "prompt": request.prompt
            }],
            "parameters": {
                "durationSeconds": request.duration_seconds,
                "resolution": request.resolution
            }
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }
            )

            logger.info(f"📡 Veo API response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Video generation started: {data}")

                # Veo returns an operation for async processing
                operation_name = data.get("name") or data.get("operationId")

                return VideoGenerateResponse(
                    success=True,
                    status="generating",
                    job_id=operation_name
                )

            elif response.status_code == 404:
                logger.error(f"❌ Veo API not found (404)")
                return VideoGenerateResponse(
                    success=False,
                    error="Google Veo is not available yet. It requires special allowlist access from Google.\n\nAlternatives: Consider Runway ML (runwayml.com) or Pika (pika.art) for production video generation.",
                    status="unavailable"
                )

            elif response.status_code == 403:
                error_text = response.text
                logger.error(f"❌ Veo API access denied (403): {error_text}")
                return VideoGenerateResponse(
                    success=False,
                    error=f"Access denied to Veo API. This model requires special preview access. Please:\n1. Request access at https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/video-generation\n2. Ensure billing is enabled\n3. Contact Google Cloud support for allowlist\n\nError: {error_text[:200]}",
                    status="unavailable"
                )

            else:
                error_text = response.text
                logger.error(f"❌ Veo request failed: {response.status_code} - {error_text}")
                return VideoGenerateResponse(
                    success=False,
                    error=f"Video generation failed (HTTP {response.status_code}). Veo may not be available in your region. Error: {error_text[:200]}",
                    status="failed"
                )

    except httpx.TimeoutException:
        logger.error("❌ Veo request timeout")
        return VideoGenerateResponse(
            success=False,
            error="Video generation request timed out.",
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
    Check status of video generation operation.

    Args:
        job_id: The operation ID returned from generate_video

    Returns:
        Dict with status and video_url (when complete)
    """

    if not all([GCP_CLIENT_ID, GCP_CLIENT_SECRET, GCP_REFRESH_TOKEN]):
        raise HTTPException(status_code=503, detail="OAuth2 credentials not configured")

    try:
        # Get fresh access token
        access_token = get_access_token()

        logger.info(f"🔍 Checking video status for operation: {job_id}")

        # Construct the full operation URL
        operation_url = f"https://us-central1-aiplatform.googleapis.com/v1/{job_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                operation_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code == 200:
                data = response.json()
                is_done = data.get("done", False)

                if is_done:
                    # Extract video from response
                    response_data = data.get("response", {})
                    video_url = response_data.get("videoUri") or response_data.get("videoUrl")

                    logger.info(f"✅ Video generation complete: {video_url}")

                    return {
                        "success": True,
                        "status": "complete",
                        "video_url": video_url,
                        "done": True
                    }
                else:
                    logger.info(f"⏳ Video still generating")
                    return {
                        "success": True,
                        "status": "generating",
                        "done": False
                    }
            else:
                logger.error(f"❌ Operation status check failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Status check failed: {response.text}"
                }

    except Exception as e:
        logger.error(f"❌ Video status check error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
