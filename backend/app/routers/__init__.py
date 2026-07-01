from app.routers.sync import router as sync_router
from app.routers.analytics import router as analytics_router
from app.routers.analytics import ratings_router
from app.routers.topics import topics_router, weaknesses_router, strengths_router
from app.routers.recommendations import recommendations_router
from app.routers.ai import ai_router
from app.routers.embeddings import router as embeddings_router
from app.routers.problems import router as problems_router
from app.routers.concepts import router as concepts_router
from app.routers.recommendations_v2 import router as recommendations_v2_router
from app.routers.users import router as users_router

__all__ = [
    "sync_router",
    "analytics_router",
    "ratings_router",
    "topics_router",
    "weaknesses_router",
    "strengths_router",
    "recommendations_router",
    "ai_router",
    "embeddings_router",
    "problems_router",
    "concepts_router",
    "recommendations_v2_router",
    "users_router",
]
