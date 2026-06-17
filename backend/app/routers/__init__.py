from app.routers.sync import router as sync_router
from app.routers.analytics import router as analytics_router
from app.routers.analytics import ratings_router
from app.routers.auth import router as auth_router
from app.routers.topics import topics_router, weaknesses_router, strengths_router
from app.routers.recommendations import recommendations_router

__all__ = [
    "sync_router",
    "analytics_router",
    "ratings_router",
    "auth_router",
    "topics_router",
    "weaknesses_router",
    "strengths_router",
    "recommendations_router",
]
