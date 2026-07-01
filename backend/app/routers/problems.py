import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services import problem_embedding_service

logger = logging.getLogger("problems_router")

router = APIRouter(prefix="/problems", tags=["problems"])

@router.get("/{problem_id}/similar", status_code=status.HTTP_200_OK)
def get_similar_problems(
    problem_id: str,
    db: Session = Depends(get_db)
):
    """
    Find top 10 semantically similar problems based on vector distance.
    """
    try:
        similar = problem_embedding_service.find_similar_problems(db, problem_id, limit=10)
        return {
            "problem_id": problem_id,
            "similar_problems": similar
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error fetching similar problems for {problem_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching similar problems: {str(e)}"
        )
