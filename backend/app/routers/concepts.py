import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.core.security import get_current_user, verify_handle_ownership
from app.models.user import User
from app.services import concept_clustering_service

logger = logging.getLogger("concepts_router")

router = APIRouter(prefix="/concepts", tags=["concepts"])

@router.get("/{handle}", status_code=status.HTTP_200_OK)
def get_user_concepts(
    handle: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user mastery scores for all semantic concept clusters.
    """
    verify_handle_ownership(handle, current_user)
    try:
        masteries = concept_clustering_service.get_user_concept_mastery(db, handle)
        return {
            "weak_concepts": [m for m in masteries if m["mastery"] < 60],
            "all_concepts": masteries
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error fetching concepts for {handle}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching concepts: {str(e)}"
        )
