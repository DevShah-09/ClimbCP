import os
import base64
import json
import hmac
import hashlib
import time
import uuid
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.user import User

# Load environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-for-climbcp-jwt-tokens-123456")
ACCESS_TOKEN_EXPIRE_SECONDS = 3600 * 24 * 7  # 7 days

security_scheme = HTTPBearer()


# Password Hashing with standard hashlib (PBKDF2-HMAC-SHA256)
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"pbkdf2:sha256:100000${salt.hex()}${key.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        parts = hashed.split('$')
        if len(parts) != 3:
            return False
        algo_iter, salt_hex, key_hex = parts
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        iterations = int(algo_iter.split(':')[-1])
        new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(key, new_key)
    except Exception:
        return False


# JWT helpers using base64url and hmac
def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').replace('=', '')


def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_jwt(payload: dict, secret: str = JWT_SECRET, expires_in: int = ACCESS_TOKEN_EXPIRE_SECONDS) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = payload.copy()
    payload["exp"] = int(time.time()) + expires_in
    
    header_b64 = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload).encode('utf-8'))
    
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
    signature_b64 = base64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_jwt(token: str, secret: str = JWT_SECRET) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        
        header_b64, payload_b64, signature_b64 = parts
        
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
        expected_sig_b64 = base64url_encode(expected_sig)
        
        if not hmac.compare_digest(signature_b64.encode('utf-8'), expected_sig_b64.encode('utf-8')):
            raise ValueError("Invalid signature")
            
        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        
        if payload.get("exp", 0) < time.time():
            raise ValueError("Token has expired")
            
        return payload
    except Exception as e:
        raise ValueError(f"Invalid token: {e}")


# FastAPI dependency for getting current authenticated user
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = decode_jwt(token, JWT_SECRET)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials payload"
            )
        user_id = uuid.UUID(user_id_str)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive"
        )
    return user


def verify_handle_ownership(handle: str, current_user: User) -> None:
    """
    Verifies that the requested competitive programming handle matches
    the authenticated user's registered Codeforces handle (case-insensitive).
    Raises HTTPException 403 Forbidden if they do not match.
    """
    if not current_user.codeforces_handle or handle.lower() != current_user.codeforces_handle.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to access data for this competitive programming handle."
        )

