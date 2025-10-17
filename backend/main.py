from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import draft as draft_route
from load_env import load_environment

# Load .env.local
load_environment()

app = FastAPI(title="Orla Marketing Suite API")

# Allow local dev + any dashboard origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "orla-backend-online"}

# Subsystem A — Draft Generation
app.include_router(draft_route.router)
