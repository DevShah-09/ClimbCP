from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.analytics import (
    UserAnalyticsResponse,
    RatingHistoryItem,
    ContestStatisticsResponse,
    ActivityStatisticsResponse
)
from app.services import analytics_service
from app.core.security import get_current_user, verify_handle_ownership
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/{handle}", response_model=UserAnalyticsResponse)
def get_user_analytics(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_handle_ownership(handle, current_user)
    try:
        return analytics_service.get_user_analytics(db, handle)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analytics: {str(e)}"
        )


@router.get("/{handle}/contests", response_model=ContestStatisticsResponse)
def get_contest_statistics(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_handle_ownership(handle, current_user)
    try:
        return analytics_service.get_contest_statistics(db, handle)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving contest statistics: {str(e)}"
        )


@router.get("/{handle}/activity", response_model=ActivityStatisticsResponse)
def get_activity_statistics(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_handle_ownership(handle, current_user)
    try:
        return analytics_service.get_activity_statistics(db, handle)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving activity statistics: {str(e)}"
        )


# Add ratings route here as well to keep router logic together, but we can make the prefix dynamic
# Wait, the prompt says endpoint is GET /ratings/{handle}
# I will create another router instance or just add it here with a different path

ratings_router = APIRouter(prefix="/ratings", tags=["analytics"])

@ratings_router.get("/{handle}", response_model=List[RatingHistoryItem])
def get_rating_history(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_handle_ownership(handle, current_user)
    try:
        return analytics_service.get_rating_history(db, handle)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving rating history: {str(e)}"
        )
