from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
import os
import google.generativeai as genai
import base64
import httpx
import io
from logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# Configure Gemini API
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)
else:
    logger.warning("⚠️  GEMINI_API_KEY not configured - AI generation features will not work")

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
    Generate an image using Google Imagen 3 (Nano Banana model).

    This endpoint uses the Gemini API's image generation capabilities.
    Cost: ~$0.03 per image

    Args:
        request: ImageGenerateRequest with prompt and aspect ratio

    Returns:
        ImageGenerateResponse with base64 encoded image data
    """

    if not gemini_key:
        logger.error("❌ Imagen generation failed: GEMINI_API_KEY not configured")
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Please add GEMINI_API_KEY to environment variables."
        )

    try:
        logger.info(f"🎨 Generating image with Imagen 3: '{request.prompt[:50]}...' (aspect: {request.aspect_ratio})")

        # Use Imagen 3 model through Gemini API
        # Model name: imagen-3.0-generate-001 (not 002)
        model = genai.ImageGenerationModel("imagen-3.0-generate-001")

        # Generate image with proper parameters
        response = model.generate_images(
            prompt=request.prompt,
            number_of_images=request.num_images,
            aspect_ratio=request.aspect_ratio,
            safety_filter_level="block_some",
            person_generation="allow_adult"
        )

        # Get first image from response
        if response.images and len(response.images) > 0:
            image = response.images[0]

            # Convert PIL image to base64 for frontend
            # Use proper buffer to save image bytes
            image_bytes_buffer = io.BytesIO()
            image._pil_image.save(image_bytes_buffer, format='PNG')
            image_bytes_buffer.seek(0)

            # Encode to base64
            image_base64 = base64.b64encode(image_bytes_buffer.getvalue()).decode('utf-8')

            logger.info(f"✅ Image generated successfully ({len(image_base64)} bytes)")

            return ImageGenerateResponse(
                success=True,
                image_data=f"data:image/png;base64,{image_base64}",
                image_url=None  # Imagen returns data, not URL
            )
        else:
            logger.error("❌ Imagen returned no images")
            return ImageGenerateResponse(
                success=False,
                error="No images generated. Please try again or adjust your prompt."
            )

    except AttributeError as e:
        # This happens if the API structure is different than expected
        logger.error(f"❌ Imagen API structure error: {str(e)}", exc_info=True)
        return ImageGenerateResponse(
            success=False,
            error=f"Image generation API error. The Imagen 3 API may have changed. Please contact support. Error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Imagen generation error: {str(e)}", exc_info=True)
        return ImageGenerateResponse(
            success=False,
            error=f"Image generation failed: {str(e)}"
        )

@router.post("/generate-video", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    """
    Generate a video using Google Veo 2 (updated from Veo 3.1).

    Note: Google Veo is still in limited preview. This endpoint uses the
    experimental Gemini API video generation endpoint.

    Cost: ~$6 per 8-second video with audio
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
        # Endpoint: https://generativelanguage.googleapis.com/v1beta/models/veo-001:generateVideo
        # Note: This may require Vertex AI access instead of Gemini API

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Try Gemini API endpoint first
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
                    video_url=data.get("video_url"),  # May not be available immediately
                    status="generating",
                    job_id=operation_name
                )
            elif response.status_code == 404:
                # API endpoint doesn't exist - Veo may not be available yet
                logger.error(f"❌ Veo API not available: 404 - {response.text}")
                return VideoGenerateResponse(
                    success=False,
                    error="Google Veo video generation is not yet available via this API. It may require Vertex AI access or be in limited preview. Please check Google Cloud Console for Veo access.",
                    status="failed"
                )
            elif response.status_code == 403:
                logger.error(f"❌ Veo API access denied: {response.text}")
                return VideoGenerateResponse(
                    success=False,
                    error="Access denied to Veo API. You may need to enable Vertex AI API or request access to Veo preview program.",
                    status="failed"
                )
            else:
                logger.error(f"❌ Video generation failed: {response.status_code} - {response.text}")
                return VideoGenerateResponse(
                    success=False,
                    error=f"Video generation failed with status {response.status_code}: {response.text}",
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
                logger.error(f"❌ Video status check failed: {response.status_code} - {response.text}")
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
