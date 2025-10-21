from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
load_dotenv('../.env.local')  # Also check parent directory

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes import blog, carousel, captions, text_publisher, video_publisher, media, drive

app.include_router(blog.router, prefix="/blog", tags=["blog"])
app.include_router(carousel.router, prefix="/carousel", tags=["carousel"])
app.include_router(captions.router, prefix="/captions", tags=["captions"])
app.include_router(text_publisher.router, prefix="/text-publisher", tags=["text-publisher"])
app.include_router(video_publisher.router, prefix="/video-publisher", tags=["video-publisher"])
app.include_router(media.router, tags=["media"])
app.include_router(drive.router, prefix="/drive", tags=["drive"])

@app.get("/")
def read_root():
    return {"message": "Orla3 Marketing Automation API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
