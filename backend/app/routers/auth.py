import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import get_db
from app.models.user import User
from app.models.platform_account import PlatformAccount
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.core.security import hash_password, verify_password, create_jwt, get_current_user
from app.services import codeforces_service
from app.services.codeforces_service import InvalidHandleException

logger = logging.getLogger("auth")
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # 1. Validate username unique
    existing_username = db.query(User).filter(
        func.lower(User.username) == user_in.username.lower()
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # 2. Validate email unique
    existing_email = db.query(User).filter(
        func.lower(User.email) == user_in.email.lower()
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 3. Validate Codeforces handle is unique
    existing_handle = db.query(User).filter(
        func.lower(User.codeforces_handle) == user_in.codeforces_handle.lower()
    ).first()
    if existing_handle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Codeforces handle already registered"
        )

    # 4. Validate Codeforces handle via Codeforces API (Step 2 of Registration Flow)
    try:
        cf_profile_info = codeforces_service.get_user_info(user_in.codeforces_handle)
        official_handle = cf_profile_info.get("handle", user_in.codeforces_handle)
    except InvalidHandleException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Codeforces handle"
        )
    except Exception as e:
        logger.error(f"Failed to validate Codeforces handle {user_in.codeforces_handle}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to validate handle: {str(e)}"
        )

    # 5. Create user (Step 3 of Registration Flow)
    hashed_pwd = hash_password(user_in.password)
    user = User(
        username=user_in.username,
        email=user_in.email.lower().strip(),
        password_hash=hashed_pwd,
        codeforces_handle=official_handle,
        is_active=True
    )
    db.add(user)
    db.flush()  # Populate user.id

    # 6. Store Codeforces handle in platform_accounts (Step 4 of Registration Flow)
    profile = PlatformAccount(
        user_id=user.id,
        platform="codeforces",
        handle=official_handle,
        current_rating=cf_profile_info.get("rating"),
        max_rating=cf_profile_info.get("maxRating")
    )
    db.add(profile)
    db.flush()

    # Commit user registration first so it is persisted
    db.commit()
    db.refresh(user)

    # 7. Trigger initial Codeforces sync (Step 5 of Registration Flow)
    try:
        codeforces_service.sync_user_data(db, official_handle)
    except Exception as e:
        # Log the error but do not fail registration, since the user was already created
        # and handle was validated in Step 2.
        logger.error(f"Initial Codeforces sync failed for handle {official_handle} during registration: {e}")

    return user


@router.post("/login", response_model=TokenResponse)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    # Find user by username or email
    user = db.query(User).filter(
        (func.lower(User.username) == login_in.username.lower()) |
        (func.lower(User.email) == login_in.username.lower())
    ).first()

    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This user account has been deactivated"
        )

    # Generate JWT token
    access_token = create_jwt({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
