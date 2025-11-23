from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import Config
from logger import setup_logger
from middleware import UserContextMiddleware

logger = setup_logger(__name__)

app = FastAPI(
    title="Orla3 Marketing Automation API",
    description="AI-powered marketing content generation and automation",
    version="1.0.1"  # Updated to include Reddit, Tumblr, WordPress publishers
)

# CORS Configuration - Allow both local development and production
# allow_credentials=True is REQUIRED for HttpOnly cookie authentication
# Note: When using credentials, allow_origins cannot be "*" - must be explicit list
allowed_origins = [
    "http://localhost:3000",  # Local development
    "https://orla3-marketing-suite-app.vercel.app",  # Production Vercel
    "https://marketing.orla3.com",  # Production custom domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,  # Required for sending/receiving HttpOnly cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# User Context Middleware - Adds user_id to all requests for multi-tenant architecture
app.add_middleware(UserContextMiddleware)

from routes import carousel, publisher, media, drive, draft, social, social_caption, brand_voice, brand_voice_upload, brand_assets, strategy, calendar, library, competitor, ai_generation, oauth, auth, cloud_storage_oauth, cloud_storage_browse, social_auth, payment, credits, social_engagement, social_discovery, auto_reply_settings, debug, admin, admin_pricing, organization, version, draft_campaign, analytics
app.include_router(version.router, tags=["version"])
app.include_router(debug.router, tags=["debug"])
app.include_router(admin.router, tags=["admin"])
app.include_router(admin_pricing.router, tags=["admin-pricing"])
app.include_router(auth.router, tags=["authentication"])
app.include_router(organization.router, tags=["organization"])
app.include_router(payment.router, tags=["payment"])
app.include_router(credits.router, tags=["credits"])
app.include_router(cloud_storage_oauth.router, tags=["cloud-storage"])
app.include_router(cloud_storage_browse.router, tags=["cloud-storage"])
app.include_router(social_auth.router, prefix="/social-auth", tags=["social-auth"])
app.include_router(social_engagement.router, prefix="/social", tags=["social-engagement"])
app.include_router(social_discovery.router, prefix="/social", tags=["social-discovery"])
app.include_router(auto_reply_settings.router, prefix="/auto-reply", tags=["auto-reply"])
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
app.include_router(draft_campaign.router, tags=["draft-campaigns"])
app.include_router(analytics.router, tags=["analytics"])

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Orla3 Marketing Automation API starting...")

    # Initialize database connection pool
    try:
        from db_pool import init_connection_pool
        init_connection_pool(minconn=2, maxconn=20)
        logger.info("✅ Database connection pool initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize connection pool: {e}")
        raise  # Critical error - can't continue without database

    logger.info(f"✅ Frontend URL: {Config.FRONTEND_URL}")
    logger.info(f"✅ OpenAI API: {'Configured' if Config.OPENAI_API_KEY else 'Missing'}")
    logger.info(f"✅ Anthropic API: {'Configured' if Config.ANTHROPIC_API_KEY else 'Missing'}")
    logger.info(f"✅ Unsplash API: {'Configured' if Config.UNSPLASH_ACCESS_KEY else 'Missing'}")
    logger.info(f"✅ Google Drive: {Config.SHARED_DRIVE_NAME}")

    # Start background scheduler for scheduled posts
    try:
        from scheduler import start_scheduler
        start_scheduler()
        logger.info("✅ Background scheduler initialized")
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")

@app.get("/")
def read_root():
    return {"message": "Orla3 Marketing Automation API", "version": "1.0.0", "status": "running"}

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Orla3 Marketing Automation API shutting down...")

    # Close database connection pool
    try:
        from db_pool import close_all_connections
        close_all_connections()
        logger.info("✅ Database connection pool closed")
    except Exception as e:
        logger.error(f"❌ Error closing connection pool: {e}")

    # Stop background scheduler
    try:
        from scheduler import stop_scheduler
        stop_scheduler()
        logger.info("✅ Background scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}")

@app.get("/health")
def health_check():
    return {"status": "healthy", "services": {"openai": bool(Config.OPENAI_API_KEY), "anthropic": bool(Config.ANTHROPIC_API_KEY), "unsplash": bool(Config.UNSPLASH_ACCESS_KEY)}}

@app.get("/scheduler/status")
def scheduler_status():
    """Get current scheduler status and active jobs"""
    try:
        from scheduler import get_scheduler_status
        return get_scheduler_status()
    except Exception as e:
        return {"error": str(e), "running": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
