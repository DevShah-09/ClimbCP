import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.rate_limit import ai_rate_limit
from app.schemas.ai import (
    ContestReviewRequest,
    ContestReviewResponse,
    RatingLossResponse,
    BottleneckAnalysis,
)
from app.services import ai_coach_service

logger = logging.getLogger("ai_router")

ai_router = APIRouter(prefix="/ai", tags=["AI Coaching"])


@ai_router.post(
    "/contest-review",
    response_model=ContestReviewResponse,
    summary="Generate AI post-contest coaching report",
    dependencies=[Depends(ai_rate_limit)],
)
def post_contest_review(
    request: ContestReviewRequest,
    db: Session = Depends(get_db),
):
    try:
        return ai_coach_service.generate_contest_review(db=db, handle=request.handle, contest_id=request.contest_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        error_str = str(e)
        if "API key" in error_str or "not configured" in error_str:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"LLM provider not configured: {error_str}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"AI service temporarily unavailable: {error_str}")
    except Exception:
        logger.exception(f"Unexpected error generating contest review for {request.handle}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@ai_router.get(
    "/rating-loss/{handle}",
    response_model=RatingLossResponse,
    summary="Explain rating stagnation or rating drop",
    dependencies=[Depends(ai_rate_limit)],
)
def get_rating_loss_explanation(handle: str, db: Session = Depends(get_db)):
    try:
        return ai_coach_service.explain_rating_loss(db=db, handle=handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        error_str = str(e)
        if "API key" in error_str or "not configured" in error_str:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"LLM provider not configured: {error_str}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"AI service temporarily unavailable: {error_str}")
    except Exception:
        logger.exception(f"Unexpected error generating rating loss explanation for {handle}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@ai_router.get(
    "/bottlenecks/{handle}",
    response_model=BottleneckAnalysis,
    summary="Identify performance bottlenecks blocking rating growth",
    dependencies=[Depends(ai_rate_limit)],
)
def get_bottleneck_analysis(handle: str, db: Session = Depends(get_db)):
    try:
        return ai_coach_service.analyze_bottlenecks(db=db, handle=handle)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        error_str = str(e)
        if "API key" in error_str or "not configured" in error_str:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"LLM provider not configured: {error_str}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"AI service temporarily unavailable: {error_str}")
    except Exception:
        logger.exception(f"Unexpected error generating bottleneck analysis for {handle}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")
