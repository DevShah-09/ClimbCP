import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services import user_embedding_service

logger = logging.getLogger("users_router")

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{handle}/similar", status_code=status.HTTP_200_OK)
def get_similar_users(handle: str, db: Session = Depends(get_db)):
    """Find semantically similar users and retrieve peer learning insights."""
    try:
        similar_users = user_embedding_service.find_similar_users(db, handle, limit=5)
        insights_data = user_embedding_service.get_similar_user_insights(db, handle)
        return {
            "similar_users": similar_users,
            "insights": insights_data.get("insights", []),
            "recommended_problems": insights_data.get("recommended_problems", [])
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Error fetching similar users for {handle}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching similar users: {str(e)}")
