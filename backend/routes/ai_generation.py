from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
import os
import httpx
import base64
from logger import setup_logger
from openai import AsyncOpenAI

logger = setup_logger(__name__)
router = APIRouter()

# Configure AI APIs
openai_key = os.getenv("OPENAI_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

if openai_key:
    openai_client = AsyncOpenAI(api_key=openai_key)
else:
    logger.warning("⚠️  OPENAI_API_KEY not configured - AI image generation will not work")

if not gemini_key:
    logger.warning("⚠️  GEMINI_API_KEY not configured - AI video generation will not work")

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

def aspect_ratio_to_size(aspect_ratio: str) -> str:
    """
    Convert aspect ratio to DALL-E 3 size format.

    DALL-E 3 supports: 1024x1024, 1792x1024, 1024x1792
    """
    mapping = {
        "1:1": "1024x1024",    # Square
        "16:9": "1792x1024",   # Landscape
        "9:16": "1024x1792",   # Portrait
        "4:3": "1792x1024",    # Landscape (closest match)
        "3:4": "1024x1792"     # Portrait (closest match)
    }
    return mapping.get(aspect_ratio, "1024x1024")

@router.post("/generate-image", response_model=ImageGenerateResponse)
async def generate_image(request: ImageGenerateRequest):
    """
    Generate an image using OpenAI's DALL-E 3.

    DALL-E 3 is currently more reliable and produces higher quality images
    than Google Imagen through the Gemini API. Imagen 3 requires Vertex AI
    which needs separate GCP service account credentials.

    Cost: ~$0.04 per image (1024x1024), ~$0.08 per image (1792x1024/1024x1792)
    Generation time: 10-20 seconds

    Args:
        request: ImageGenerateRequest with prompt and aspect ratio

    Returns:
        ImageGenerateResponse with image URL
    """

    if not openai_key:
        logger.error("❌ Image generation failed: OPENAI_API_KEY not configured")
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Please add OPENAI_API_KEY to environment variables."
        )

    try:
        # Convert aspect ratio to DALL-E size
        size = aspect_ratio_to_size(request.aspect_ratio)

        logger.info(f"🎨 Generating image with DALL-E 3: '{request.prompt[:50]}...' (size: {size})")

        # Generate image with DALL-E 3
        response = await openai_client.images.generate(
            model="dall-e-3",
            prompt=request.prompt,
            size=size,
            quality="standard",  # "standard" or "hd" (hd costs 2x)
            n=1  # DALL-E 3 only supports 1 image at a time
        )

        # Get the image URL
        if response.data and len(response.data) > 0:
            image_url = response.data[0].url

            logger.info(f"✅ Image generated successfully: {image_url[:50]}...")

            # Download the image and convert to base64 for storage
            async with httpx.AsyncClient() as client:
                img_response = await client.get(image_url)
                if img_response.status_code == 200:
                    image_base64 = base64.b64encode(img_response.content).decode('utf-8')

                    return ImageGenerateResponse(
                        success=True,
                        image_url=image_url,  # Temporary OpenAI URL (expires after 1 hour)
                        image_data=f"data:image/png;base64,{image_base64}"
                    )
                else:
                    logger.error(f"❌ Failed to download image from URL: {img_response.status_code}")
                    return ImageGenerateResponse(
                        success=True,
                        image_url=image_url  # Return URL even if download fails
                    )
        else:
            logger.error("❌ DALL-E returned no images")
            return ImageGenerateResponse(
                success=False,
                error="No images generated. Please try again or adjust your prompt."
            )

    except Exception as e:
        logger.error(f"❌ Image generation error: {str(e)}", exc_info=True)
        return ImageGenerateResponse(
            success=False,
            error=f"Image generation failed: {str(e)}"
        )

@router.post("/generate-video", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    """
    Generate a video using Google Veo 2 (experimental).

    Note: Google Veo is in limited preview and requires special access.
    This endpoint will likely return an error until you enable Vertex AI
    and request access to the Veo preview program.

    Alternative: Consider using Runway ML or Pika for production video generation.

    Cost: ~$6 per 8-second video (when available)
    Generation time: 2-5 minutes (async)

    Args:
        request: VideoGenerateRequest with prompt, duration, and resolution

    Returns:
        VideoGenerateResponse with job_id for status tracking
    """

    if not gemini_key:
        logger.error("❌ Video generation failed: GEMINI_API_KEY not configured")
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Please add GEMINI_API_KEY to environment variables."
        )

    try:
        logger.info(f"🎬 Generating video with Veo: '{request.prompt[:50]}...' ({request.resolution})")

        # Google Veo video generation via Gemini API
        # Note: This endpoint is experimental and may not be publicly available
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/veo-001:generateVideo",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": gemini_key
                },
                json={
                    "prompt": request.prompt,
                    "video_duration_seconds": request.duration_seconds,
                    "output_config": {
                        "resolution": request.resolution
                    }
                }
            )

            logger.info(f"📡 Video API response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Video generation started: {data}")

                # Extract operation/job ID for status checking
                operation_name = data.get("name") or data.get("operation_id")

                return VideoGenerateResponse(
                    success=True,
                    video_url=data.get("video_url"),
                    status="generating",
                    job_id=operation_name
                )
            elif response.status_code == 404:
                # API endpoint doesn't exist - Veo is not available yet
                logger.error(f"❌ Veo API not available: 404")
                return VideoGenerateResponse(
                    success=False,
                    error="Google Veo video generation is not yet publicly available. It requires Vertex AI access and enrollment in the preview program. Consider using Runway ML (runwayml.com) or Pika (pika.art) as alternatives.",
                    status="failed"
                )
            elif response.status_code == 403:
                logger.error(f"❌ Veo API access denied")
                return VideoGenerateResponse(
                    success=False,
                    error="Access denied to Veo API. Please enable Vertex AI API in Google Cloud Console and request access to the Veo preview program at https://labs.google/veo",
                    status="failed"
                )
            else:
                logger.error(f"❌ Video generation failed: {response.status_code} - {response.text}")
                return VideoGenerateResponse(
                    success=False,
                    error=f"Video generation failed with status {response.status_code}. Veo may not be available in your region or account.",
                    status="failed"
                )

    except httpx.TimeoutException:
        logger.error("❌ Video generation timeout after 60 seconds")
        return VideoGenerateResponse(
            success=False,
            error="Video generation request timed out. The API may be unavailable.",
            status="failed"
        )
    except Exception as e:
        logger.error(f"❌ Video generation error: {str(e)}", exc_info=True)
        return VideoGenerateResponse(
            success=False,
            error=f"Video generation failed: {str(e)}",
            status="failed"
        )

@router.get("/video-status/{job_id}")
async def get_video_status(job_id: str):
    """
    Check status of video generation job.

    Args:
        job_id: The operation ID returned from generate_video

    Returns:
        Dict with status and video_url (when complete)
    """

    if not gemini_key:
        raise HTTPException(status_code=503, detail="Gemini API key not configured")

    try:
        logger.info(f"🔍 Checking video status for job: {job_id}")

        # Check video generation status via operations API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://generativelanguage.googleapis.com/v1beta/{job_id}",
                headers={"x-goog-api-key": gemini_key}
            )

            if response.status_code == 200:
                data = response.json()

                # Check if operation is complete
                is_done = data.get("done", False)

                if is_done:
                    # Extract video URL from response
                    result = data.get("response", {})
                    video_url = result.get("video_uri") or result.get("video_url")

                    logger.info(f"✅ Video generation complete: {video_url}")

                    return {
                        "success": True,
                        "status": "complete",
                        "video_url": video_url,
                        "done": True
                    }
                else:
                    logger.info(f"⏳ Video still generating: {job_id}")
                    return {
                        "success": True,
                        "status": "generating",
                        "done": False
                    }
            else:
                logger.error(f"❌ Video status check failed: {response.status_code}")
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
