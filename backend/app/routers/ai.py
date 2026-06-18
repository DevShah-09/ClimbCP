"""
AI Coaching Router — Phase 4

Endpoints:
  POST /ai/contest-review          → Detailed post-contest coaching report
  GET  /ai/rating-loss/{handle}    → Rating stagnation/drop explanation
  GET  /ai/bottlenecks/{handle}    → Performance bottleneck analysis
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.security import get_current_user
from app.core.rate_limit import ai_rate_limit
from app.models.user import User
from app.schemas.ai import (
    ContestReviewRequest,
    ContestReviewResponse,
    RatingLossResponse,
    BottleneckAnalysis,
)
from app.services import ai_coach_service

logger = logging.getLogger("ai_router")

ai_router = APIRouter(prefix="/ai", tags=["AI Coaching"])


# ── POST /ai/contest-review ───────────────────────────────────────────────────

@ai_router.post(
    "/contest-review",
    response_model=ContestReviewResponse,
    summary="Generate AI post-contest coaching report",
    description=(
        "Analyses a specific contest participation and generates a personalised coaching "
        "report including strengths, weaknesses, missed opportunities, and an action plan. "
        "Reports are cached for 6 hours to minimise LLM API cost."
    ),
    dependencies=[Depends(ai_rate_limit)],
)
def post_contest_review(
    request: ContestReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a detailed post-contest AI coaching report.

    The report references real contest data: rank, rating change, problems attempted,
    topic mastery scores, and submission patterns.
    """
    logger.info(
        f"AI contest review requested: handle={request.handle}, contest_id={request.contest_id} "
        f"by user={current_user.username}"
    )
    try:
        return ai_coach_service.generate_contest_review(
            db=db,
            handle=request.handle,
            contest_id=request.contest_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        # LLM-specific errors (timeout, provider unavailable, bad key)
        error_str = str(e)
        if "API key" in error_str or "not configured" in error_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LLM provider not configured: {error_str}",
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service temporarily unavailable: {error_str}",
        )
    except Exception:
        logger.exception(
            f"Unexpected error generating contest review for {request.handle}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the contest review.",
        )


# ── GET /ai/rating-loss/{handle} ──────────────────────────────────────────────

@ai_router.get(
    "/rating-loss/{handle}",
    response_model=RatingLossResponse,
    summary="Explain rating stagnation or rating drop",
    description=(
        "Analyses rating history, topic mastery scores, and submission patterns to explain "
        "why a user's rating is declining or stagnating. Returns major causes and "
        "concrete recommended actions grounded in real statistics."
    ),
    dependencies=[Depends(ai_rate_limit)],
)
def get_rating_loss_explanation(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Explain why a user's rating is not growing.

    Uses the last 10 contests, topic mastery scores, and activity statistics
    to identify root causes and provide targeted recommendations.
    """
    logger.info(
        f"AI rating loss explanation requested: handle={handle} "
        f"by user={current_user.username}"
    )
    try:
        return ai_coach_service.explain_rating_loss(db=db, handle=handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        error_str = str(e)
        if "API key" in error_str or "not configured" in error_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LLM provider not configured: {error_str}",
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service temporarily unavailable: {error_str}",
        )
    except Exception:
        logger.exception(
            f"Unexpected error generating rating loss explanation for {handle}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the rating loss explanation.",
        )


# ── GET /ai/bottlenecks/{handle} ──────────────────────────────────────────────

@ai_router.get(
    "/bottlenecks/{handle}",
    response_model=BottleneckAnalysis,
    summary="Identify performance bottlenecks blocking rating growth",
    description=(
        "Identifies the biggest factors preventing rating growth by combining "
        "algorithmic scoring of topic weaknesses, contest frequency, solving speed, "
        "and upsolving habits with AI-generated narrative coaching. "
        "Each bottleneck receives an impact score from 0 (no effect) to 100 (critical)."
    ),
    dependencies=[Depends(ai_rate_limit)],
)
def get_bottleneck_analysis(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyse what is limiting rating growth.

    Bottleneck categories include: topic weaknesses (DP, Graphs, Binary Search, etc.),
    Implementation Errors, Low Contest Frequency, Slow Solving Speed, and
    Poor Upsolving Habits.
    """
    logger.info(
        f"AI bottleneck analysis requested: handle={handle} "
        f"by user={current_user.username}"
    )
    try:
        return ai_coach_service.analyze_bottlenecks(db=db, handle=handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        error_str = str(e)
        if "API key" in error_str or "not configured" in error_str:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LLM provider not configured: {error_str}",
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service temporarily unavailable: {error_str}",
        )
    except Exception:
        logger.exception(
            f"Unexpected error generating bottleneck analysis for {handle}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the bottleneck analysis.",
        )
