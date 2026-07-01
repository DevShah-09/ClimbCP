import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.database.database import create_db_and_tables
from app.core.rate_limit import default_rate_limit
from app.routers import (
    sync_router,
    analytics_router,
    ratings_router,
    topics_router,
    weaknesses_router,
    strengths_router,
    recommendations_router,
    ai_router,
    embeddings_router,
    problems_router,
    concepts_router,
    recommendations_v2_router,
    users_router,
)

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and seed data
    create_db_and_tables()
    yield
    # Shutdown logic (if any)

app = FastAPI(
    title="ClimbCP API",
    description="Backend API for ClimbCP platform",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_str:
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

allow_credentials = True
if "*" in allowed_origins:
    allow_credentials = False

local_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=local_origin_regex,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers — all public, no auth required
app.include_router(sync_router, dependencies=[Depends(default_rate_limit)])
app.include_router(analytics_router, dependencies=[Depends(default_rate_limit)])
app.include_router(ratings_router, dependencies=[Depends(default_rate_limit)])
app.include_router(topics_router, dependencies=[Depends(default_rate_limit)])
app.include_router(weaknesses_router, dependencies=[Depends(default_rate_limit)])
app.include_router(strengths_router, dependencies=[Depends(default_rate_limit)])
app.include_router(recommendations_router, dependencies=[Depends(default_rate_limit)])
app.include_router(ai_router)
app.include_router(embeddings_router, dependencies=[Depends(default_rate_limit)])
app.include_router(problems_router, dependencies=[Depends(default_rate_limit)])
app.include_router(concepts_router, dependencies=[Depends(default_rate_limit)])
app.include_router(recommendations_v2_router, dependencies=[Depends(default_rate_limit)])
app.include_router(users_router, dependencies=[Depends(default_rate_limit)])

@app.get("/")
def read_root():
    return {"message": "Welcome to ClimbCP API v2"}
