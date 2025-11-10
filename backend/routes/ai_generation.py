from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
import os
import httpx
import base64
from logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

# Configure AI APIs
gemini_api_key = os.getenv("GEMINI_API_KEY")
gcp_project_id = os.getenv("GCP_PROJECT_ID", "gen-lang-client-0902837589")

if not gemini_api_key:
    logger.warning("⚠️  GEMINI_API_KEY not configured - AI generation features will not work")

logger.info(f"🔧 Vertex AI configured: Project ID = {gcp_project_id}")

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

def aspect_ratio_to_imagen_format(aspect_ratio: str) -> str:
    """
    Convert aspect ratio to Imagen 3 format.

    Imagen 3 supports: 1:1, 3:4, 4:3, 9:16, 16:9
    """
    return aspect_ratio  # Imagen 3 uses the same format!

@router.post("/generate-image", response_model=ImageGenerateResponse)
async def generate_image(request: ImageGenerateRequest):
    """
    Generate an image using Google Imagen 3 via Vertex AI.

    Imagen 3 is Google's state-of-the-art text-to-image model with:
    - Superior photorealism compared to DALL-E 3
    - Better prompt adherence
    - More natural lighting and composition
    - Lower cost ($0.02-0.04 per image depending on resolution)

    This uses Vertex AI REST API with API key authentication.

    Args:
        request: ImageGenerateRequest with prompt and aspect ratio

    Returns:
        ImageGenerateResponse with base64 encoded image data
    """

    if not gemini_api_key:
        logger.error("❌ Imagen generation failed: GEMINI_API_KEY not configured")
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY not configured. Please add to environment variables."
        )

    try:
        aspect_ratio_formatted = aspect_ratio_to_imagen_format(request.aspect_ratio)

        logger.info(f"🎨 Generating image with Imagen 3: '{request.prompt[:60]}...' (aspect: {aspect_ratio_formatted})")

        # Vertex AI Imagen 3 endpoint
        endpoint = (
            f"https://us-central1-aiplatform.googleapis.com/v1/"
            f"projects/{gcp_project_id}/locations/us-central1/"
            f"publishers/google/models/imagegeneration@006:predict"
        )

        # Request payload for Imagen 3
        payload = {
            "instances": [
                {
                    "prompt": request.prompt
                }
            ],
            "parameters": {
                "sampleCount": request.num_images,
                "aspectRatio": aspect_ratio_formatted,
                "safetyFilterLevel": "block_some",
                "personGeneration": "allow_adult"
            }
        }

        # Make the request
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                },
                params={
                    "key": gemini_api_key  # API key authentication
                }
            )

            logger.info(f"📡 Imagen API response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Extract image from response
                # Imagen returns base64 encoded images in predictions array
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
                    error=f"Access denied to Imagen API. Please ensure:\n1. Vertex AI API is enabled in your GCP project\n2. API key has 'Vertex AI User' permissions\n3. Billing is enabled on project {gcp_project_id}\n\nError: {error_text[:200]}"
                )

            elif response.status_code == 400:
                error_text = response.text
                logger.error(f"❌ Invalid request (400): {error_text}")
                return ImageGenerateResponse(
                    success=False,
                    error=f"Invalid request to Imagen API. This might be due to:\n1. Invalid prompt (check for restricted content)\n2. Unsupported aspect ratio\n3. API format changed\n\nError: {error_text[:200]}"
                )

            else:
                error_text = response.text
                logger.error(f"❌ Imagen request failed: {response.status_code} - {error_text}")
                return ImageGenerateResponse(
                    success=False,
                    error=f"Image generation failed with status {response.status_code}: {error_text[:200]}"
                )

    except httpx.TimeoutException:
        logger.error("❌ Imagen request timeout after 60 seconds")
        return ImageGenerateResponse(
            success=False,
            error="Image generation timed out. Imagen 3 is processing your request but it's taking longer than expected. Please try again."
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
    Generate a video using Google Veo via Vertex AI.

    Google Veo is Google's experimental video generation model.
    Note: Veo may require special access or allowlisting in your GCP project.

    Cost: ~$6 per 8-second video with audio (when available)
    Generation time: 2-5 minutes (async operation)

    Args:
        request: VideoGenerateRequest with prompt, duration, and resolution

    Returns:
        VideoGenerateResponse with operation ID for status tracking
    """

    if not gemini_api_key:
        logger.error("❌ Video generation failed: GEMINI_API_KEY not configured")
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY not configured. Please add to environment variables."
        )

    try:
        logger.info(f"🎬 Generating video with Veo: '{request.prompt[:60]}...' ({request.resolution})")

        # Vertex AI Veo endpoint (experimental)
        # Note: This endpoint may not be available without special access
        endpoint = (
            f"https://us-central1-aiplatform.googleapis.com/v1/"
            f"projects/{gcp_project_id}/locations/us-central1/"
            f"publishers/google/models/veo-001:predict"
        )

        # Request payload for Veo
        payload = {
            "instances": [
                {
                    "prompt": request.prompt
                }
            ],
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
                    "Content-Type": "application/json",
                },
                params={
                    "key": gemini_api_key
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
                    error="Google Veo is not available yet. It requires:\n1. Special allowlist access from Google\n2. Enrollment in Vertex AI preview programs\n3. May not be GA (generally available)\n\nAlternatives: Consider Runway ML (runwayml.com) or Pika (pika.art) for production video generation.",
                    status="failed"
                )

            elif response.status_code == 403:
                error_text = response.text
                logger.error(f"❌ Veo API access denied (403): {error_text}")
                return VideoGenerateResponse(
                    success=False,
                    error=f"Access denied to Veo API. This model requires special preview access. Please:\n1. Request access at https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/video-generation\n2. Ensure billing is enabled\n3. Contact Google Cloud support for allowlist\n\nError: {error_text[:200]}",
                    status="failed"
                )

            else:
                error_text = response.text
                logger.error(f"❌ Veo request failed: {response.status_code} - {error_text}")
                return VideoGenerateResponse(
                    success=False,
                    error=f"Video generation failed with status {response.status_code}. Veo may not be available in your region or account. Error: {error_text[:200]}",
                    status="failed"
                )

    except httpx.TimeoutException:
        logger.error("❌ Veo request timeout after 120 seconds")
        return VideoGenerateResponse(
            success=False,
            error="Video generation request timed out. The API may be unavailable or overloaded.",
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
    Check status of video generation operation.

    Args:
        job_id: The operation ID returned from generate_video

    Returns:
        Dict with status and video_url (when complete)
    """

    if not gemini_api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not configured")

    try:
        logger.info(f"🔍 Checking video status for operation: {job_id}")

        # Construct the operations endpoint
        # Format: projects/{project}/locations/{location}/operations/{operation_id}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://us-central1-aiplatform.googleapis.com/v1/{job_id}",
                params={"key": gemini_api_key}
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
                    logger.info(f"⏳ Video still generating: {job_id}")
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
