from dotenv import load_dotenv; load_dotenv('.env.local', override=True)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
import os
import google.generativeai as genai
import base64
import httpx

router = APIRouter()

# Configure Gemini API
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)

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
    error: Optional[str] = None

@router.post("/generate-image", response_model=ImageGenerateResponse)
async def generate_image(request: ImageGenerateRequest):
    """Generate an image using Google Imagen 3 (nano banana)"""

    if not gemini_key:
        raise HTTPException(status_code=503, detail="Gemini API key not configured")

    try:
        # Use Imagen 3 model through Gemini API
        model = genai.GenerativeModel('imagen-3.0-generate-002')

        # Generate image
        response = model.generate_images(
            prompt=request.prompt,
            number_of_images=request.num_images,
            aspect_ratio=request.aspect_ratio
        )

        # Get first image
        if response.images and len(response.images) > 0:
            image = response.images[0]

            # Convert to base64 for frontend display
            image_base64 = base64.b64encode(image._pil_image.tobytes()).decode('utf-8')

            return ImageGenerateResponse(
                success=True,
                image_data=f"data:image/png;base64,{image_base64}",
                image_url=None  # Imagen returns data, not URL
            )
        else:
            return ImageGenerateResponse(
                success=False,
                error="No images generated"
            )

    except Exception as e:
        print(f"Imagen 3 generation error: {str(e)}")
        return ImageGenerateResponse(
            success=False,
            error=f"Image generation failed: {str(e)}"
        )

@router.post("/generate-video", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    """Generate a video using Google Veo 3.1"""

    if not gemini_key:
        raise HTTPException(status_code=503, detail="Gemini API key not configured")

    try:
        # Note: Veo 3.1 API might have different implementation
        # This is a template - actual implementation depends on API structure

        # Use Veo model through Gemini API
        # API endpoint for Veo video generation
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/veo-3.1:generateVideo",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": gemini_key
                },
                json={
                    "prompt": request.prompt,
                    "config": {
                        "duration_seconds": request.duration_seconds,
                        "resolution": request.resolution,
                        "generate_audio": True
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()

                # Video generation is async - return job ID or video URL
                return VideoGenerateResponse(
                    success=True,
                    video_url=data.get("video_url"),
                    status="generating"
                )
            else:
                return VideoGenerateResponse(
                    success=False,
                    error=f"Video generation failed: {response.text}",
                    status="failed"
                )

    except Exception as e:
        print(f"Veo 3 generation error: {str(e)}")
        return VideoGenerateResponse(
            success=False,
            error=f"Video generation failed: {str(e)}",
            status="failed"
        )

@router.get("/video-status/{job_id}")
async def get_video_status(job_id: str):
    """Check status of video generation job"""

    if not gemini_key:
        raise HTTPException(status_code=503, detail="Gemini API key not configured")

    try:
        # Check video generation status
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://generativelanguage.googleapis.com/v1beta/operations/{job_id}",
                headers={"x-goog-api-key": gemini_key}
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get("status"),
                    "video_url": data.get("result", {}).get("video_url")
                }
            else:
                return {
                    "success": False,
                    "error": response.text
                }

    except Exception as e:
        print(f"Video status check error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
