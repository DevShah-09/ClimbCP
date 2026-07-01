import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.recommendation import (
    ProblemRecommendationResponse,
    PracticeSetResponse,
    RoadmapResponse,
)
from app.services import recommendation_service

logger = logging.getLogger("recommendations_router")

recommendations_router = APIRouter(tags=["recommendations"])


@recommendations_router.get(
    "/recommendations/{handle}",
    response_model=ProblemRecommendationResponse,
    summary="Get personalised problem recommendations",
)
def get_recommendations(
    handle: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    try:
        return recommendation_service.get_problem_recommendations(db, handle, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error generating recommendations for {handle}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating recommendations: {str(e)}")


@recommendations_router.get(
    "/practice-set/{handle}",
    response_model=PracticeSetResponse,
    summary="Generate a personalised practice set",
)
def get_practice_set(handle: str, db: Session = Depends(get_db)):
    try:
        return recommendation_service.generate_practice_set(db, handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error generating practice set for {handle}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating practice set: {str(e)}")


@recommendations_router.get(
    "/roadmap/{handle}",
    response_model=RoadmapResponse,
    summary="Generate a 4-week learning roadmap",
)
def get_roadmap(handle: str, db: Session = Depends(get_db)):
    try:
        return recommendation_service.generate_learning_roadmap(db, handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error generating roadmap for {handle}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating roadmap: {str(e)}")
