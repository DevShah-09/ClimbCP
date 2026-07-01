import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services import problem_embedding_service, user_embedding_service

logger = logging.getLogger("embeddings_router")

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

@router.post("/problems/generate", status_code=status.HTTP_200_OK)
def generate_problem_embeddings(db: Session = Depends(get_db)):
    """Generate embeddings for all problems that do not have vectors in the database."""
    try:
        count = problem_embedding_service.generate_embeddings_for_new_problems(db)
        return {"status": "success", "generated_count": count}
    except Exception as e:
        logger.exception("Error generating problem embeddings")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating problem embeddings: {str(e)}")

@router.post("/users/generate/{handle}", status_code=status.HTTP_200_OK)
def generate_user_embedding(handle: str, db: Session = Depends(get_db)):
    """Generate a 128-dimensional embedding vector representing the user's profile."""
    try:
        embedding = user_embedding_service.generate_user_embedding(db, handle)
        return {"status": "success", "embedding_length": len(embedding)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Error generating user embedding for {handle}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating user embedding: {str(e)}")
