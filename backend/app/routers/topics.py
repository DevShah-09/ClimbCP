import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.topic import (
    TopicAnalyticsResponse,
    TopicMasteryResponse,
    WeaknessResponse,
    StrengthResponse,
    TopicSummaryResponse,
)
from app.services import topic_service

logger = logging.getLogger("topics_router")

topics_router = APIRouter(tags=["topics"])
weaknesses_router = APIRouter(tags=["topics"])
strengths_router = APIRouter(tags=["topics"])


# ── /topics/{handle} ──────────────────────────────────────────────────────────

@topics_router.get("/topics/{handle}", response_model=TopicAnalyticsResponse)
def get_topic_analytics(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return per-topic attempt/solve counts and accuracy for a given handle."""
    try:
        return topic_service.get_topic_analytics(db, handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in get_topic_analytics for {handle}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating topic analytics: {str(e)}",
        )


@topics_router.get("/topics/{handle}/mastery", response_model=TopicMasteryResponse)
def get_topic_mastery(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return mastery score (0–100) and level for every topic."""
    try:
        return topic_service.calculate_topic_mastery(db, handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in get_topic_mastery for {handle}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating topic mastery: {str(e)}",
        )


@topics_router.get("/topics/{handle}/summary", response_model=TopicSummaryResponse)
def get_topic_summary(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return aggregate mastery summary statistics."""
    try:
        return topic_service.get_topic_summary(db, handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in get_topic_summary for {handle}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating topic summary: {str(e)}",
        )


# ── /weaknesses/{handle} ──────────────────────────────────────────────────────

@weaknesses_router.get("/weaknesses/{handle}", response_model=WeaknessResponse)
def get_weaknesses(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return topics ordered by mastery score ascending with priority tags."""
    try:
        return topic_service.get_weaknesses(db, handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in get_weaknesses for {handle}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating weaknesses: {str(e)}",
        )


# ── /strengths/{handle} ───────────────────────────────────────────────────────

@strengths_router.get("/strengths/{handle}", response_model=StrengthResponse)
def get_strengths(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return topics with mastery score >= 75, ordered descending."""
    try:
        return topic_service.get_strengths(db, handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in get_strengths for {handle}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating strengths: {str(e)}",
        )
