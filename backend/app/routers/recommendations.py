"""
Recommendations Router — Phase 3

Endpoints:
  GET /recommendations/{handle}   → Problem recommendation list
  GET /practice-set/{handle}      → Balanced practice set
  GET /roadmap/{handle}           → 4-week learning roadmap
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import get_current_user, verify_handle_ownership
from app.models.user import User
from app.schemas.recommendation import (
    ProblemRecommendationResponse,
    PracticeSetResponse,
    RoadmapResponse,
)
from app.services import recommendation_service

logger = logging.getLogger("recommendations_router")

recommendations_router = APIRouter(tags=["recommendations"])


# ── GET /recommendations/{handle} ────────────────────────────────────────────

@recommendations_router.get(
    "/recommendations/{handle}",
    response_model=ProblemRecommendationResponse,
    summary="Get personalised problem recommendations",
    description=(
        "Returns a ranked list of problems tailored to the user's current rating, "
        "weak topics, and solving history. Every recommendation includes an "
        "explainable reason."
    ),
)
def get_recommendations(
    handle: str,
    limit: int = Query(default=10, ge=1, le=50, description="Number of recommendations to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recommend problems that maximise skill improvement.

    Priority formula:
      50% topic weakness weight + 35% difficulty match + 15% popularity
    """
    verify_handle_ownership(handle, current_user)
    try:
        return recommendation_service.get_problem_recommendations(db, handle, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error generating recommendations for {handle}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}",
        )


# ── GET /practice-set/{handle} ────────────────────────────────────────────────

@recommendations_router.get(
    "/practice-set/{handle}",
    response_model=PracticeSetResponse,
    summary="Generate a personalised practice set",
    description=(
        "Returns a balanced set of 10 problems: 5 from weak topics, "
        "3 from medium topics, 2 from strong topics. "
        "Difficulty is split 40% easy / 40% current / 20% challenge."
    ),
)
def get_practice_set(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a balanced 10-problem practice set with metadata.

    Metadata includes estimated completion time and primary focus topics.
    """
    verify_handle_ownership(handle, current_user)
    try:
        return recommendation_service.generate_practice_set(db, handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error generating practice set for {handle}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating practice set: {str(e)}",
        )


# ── GET /roadmap/{handle} ─────────────────────────────────────────────────────

@recommendations_router.get(
    "/roadmap/{handle}",
    response_model=RoadmapResponse,
    summary="Generate a 4-week learning roadmap",
    description=(
        "Analyses weak topics and user rating to produce a structured "
        "4-week training plan with weekly focus topics and actionable tasks."
    ),
)
def get_roadmap(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a 4-week learning roadmap.

    Week 1: Weakest topic
    Week 2: Second weakest topic
    Week 3: Combined practice
    Week 4: Virtual contest training
    """
    verify_handle_ownership(handle, current_user)
    try:
        return recommendation_service.generate_learning_roadmap(db, handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error generating roadmap for {handle}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating roadmap: {str(e)}",
        )
