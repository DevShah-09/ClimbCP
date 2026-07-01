import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services import recommendation_service

logger = logging.getLogger("recommendations_v2_router")

router = APIRouter(prefix="/recommendations/v2", tags=["recommendations"])

@router.get("/{handle}", status_code=status.HTTP_200_OK)
def get_recommendations_v2(handle: str, db: Session = Depends(get_db)):
    """Get V2 embedding-based recommendations tailored to failures."""
    try:
        return recommendation_service.get_recommendations_v2(db, handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Error fetching recommendations v2 for {handle}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching recommendations: {str(e)}")
