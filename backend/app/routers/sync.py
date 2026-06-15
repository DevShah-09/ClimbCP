from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.sync import SyncResponse
from app.services import codeforces_service
from app.services.codeforces_service import (
    InvalidHandleException,
    CodeforcesUnavailableException,
    CodeforcesTimeoutException,
    CodeforcesException
)

router = APIRouter(prefix="/sync", tags=["sync"])

@router.post("/codeforces/{handle}", response_model=SyncResponse)
def sync_codeforces(handle: str, db: Session = Depends(get_db)):
    """
    Triggers database synchronization for a user's Codeforces profile,
    rating history, and submissions.
    """
    try:
        result = codeforces_service.sync_user_data(db, handle)
        return result
    except InvalidHandleException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CodeforcesTimeoutException as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e)
        )
    except CodeforcesUnavailableException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except CodeforcesException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database or system error occurred: {str(e)}"
        )
