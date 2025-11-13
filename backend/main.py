from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import Config
from logger import setup_logger
from middleware import UserContextMiddleware

logger = setup_logger(__name__)

app = FastAPI(
    title="Orla3 Marketing Automation API",
    description="AI-powered marketing content generation and automation",
    version="1.0.0"
)

# CORS Configuration - Allow both local development and production
allowed_origins = [
    "http://localhost:3000",  # Local development
    "https://orla3-marketing-suite-app.vercel.app",  # Production Vercel
    "https://marketing.orla3.com",  # Production custom domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# User Context Middleware - Adds user_id to all requests for multi-tenant architecture
app.add_middleware(UserContextMiddleware)

from routes import carousel, publisher, media, drive, draft, social, social_caption, brand_voice, brand_voice_upload, brand_assets, strategy, calendar, library, competitor, ai_generation, oauth, auth, cloud_storage_oauth, social_auth, payment, credits

app.include_router(auth.router, tags=["authentication"])
app.include_router(payment.router, tags=["payment"])
app.include_router(credits.router, tags=["credits"])
app.include_router(cloud_storage_oauth.router, tags=["cloud-storage"])
app.include_router(social_auth.router, prefix="/social-auth", tags=["social-auth"])
app.include_router(carousel.router, prefix="/carousel", tags=["carousel"])
app.include_router(publisher.router, prefix="/publisher", tags=["publisher"])
app.include_router(media.router, tags=["media"])
app.include_router(drive.router, prefix="/drive", tags=["drive"])
app.include_router(draft.router, prefix="/draft", tags=["draft"])
app.include_router(social.router, prefix="/social", tags=["social"])
app.include_router(social_caption.router, prefix="/social-caption", tags=["social"])
app.include_router(brand_voice.router, prefix="/brand-voice", tags=["brand-voice"])
app.include_router(brand_voice_upload.router, prefix="/brand-voice", tags=["brand-voice"])
app.include_router(brand_assets.router, tags=["brand-assets"])
app.include_router(strategy.router, prefix="/strategy", tags=["strategy"])
app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
app.include_router(library.router, prefix="/library", tags=["library"])
app.include_router(competitor.router, prefix="/competitor", tags=["competitor"])
app.include_router(ai_generation.router, prefix="/ai", tags=["ai-generation"])
app.include_router(oauth.router, tags=["oauth"])

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Orla3 Marketing Automation API starting...")
    logger.info(f"✅ Frontend URL: {Config.FRONTEND_URL}")
    logger.info(f"✅ OpenAI API: {'Configured' if Config.OPENAI_API_KEY else 'Missing'}")
    logger.info(f"✅ Anthropic API: {'Configured' if Config.ANTHROPIC_API_KEY else 'Missing'}")
    logger.info(f"✅ Unsplash API: {'Configured' if Config.UNSPLASH_ACCESS_KEY else 'Missing'}")
    logger.info(f"✅ Google Drive: {Config.SHARED_DRIVE_NAME}")

@app.get("/")
def read_root():
    return {"message": "Orla3 Marketing Automation API", "version": "1.0.0", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "services": {"openai": bool(Config.OPENAI_API_KEY), "anthropic": bool(Config.ANTHROPIC_API_KEY), "unsplash": bool(Config.UNSPLASH_ACCESS_KEY)}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
