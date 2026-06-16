from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database.database import create_db_and_tables
from app.routers import sync_router, analytics_router, ratings_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and seed data
    create_db_and_tables()
    yield
    # Shutdown logic (if any)

app = FastAPI(
    title="ClimbCP API",
    description="Backend API for ClimbCP platform",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(sync_router)
app.include_router(analytics_router)
app.include_router(ratings_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to ClimbCP API"}
