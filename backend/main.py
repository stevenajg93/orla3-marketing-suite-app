from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import draft as draft_route
from load_env import load_environment
from routes import primer as primer_route
from routes import carousel as carousel_route
from routes import brand_voice as brand_voice_route
from routes import analytics as analytics_route
from routes import ads as ads_route
from routes import crm as crm_route
from routes import publisher as publisher_route
from routes import comments as comments_route
from routes import competitor as competitor_route
from routes import media as media_route
from routes import collaboration as collaboration_route
from routes import social as social_route
from routes import strategy as strategy_route
from routes import atomize as atomize_route
from routes import drive as drive_route
from routes import media as media_route
from routes import drive as drive_route

load_environment()

app = FastAPI(title="Orla Marketing Suite API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def read_root():
    return {"status": "orla-backend-online", "subsystems": 12}

app.include_router(draft_route.router)
app.include_router(primer_route.router)
app.include_router(carousel_route.router)
app.include_router(brand_voice_route.router)
app.include_router(analytics_route.router)
app.include_router(ads_route.router)
app.include_router(media_route.router)
app.include_router(drive_route.router)
app.include_router(crm_route.router)
app.include_router(drive_route.router)
app.include_router(atomize_route.router)
app.include_router(publisher_route.router)
app.include_router(comments_route.router)
app.include_router(competitor_route.router)
app.include_router(media_route.router)
app.include_router(collaboration_route.router)
app.include_router(social_route.router)
app.include_router(strategy_route.router)
