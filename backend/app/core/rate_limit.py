import os
import time
from threading import Lock
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException, status, Depends
from app.models.user import User

class InMemoryRateLimiter:
    """
    A thread-safe, in-memory sliding-window rate limiter.
    """
    def __init__(self):
        self._requests: Dict[str, List[float]] = {}
        self._lock = Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Check if a request is allowed for the given key under the rate limit rules.
        Returns a tuple of (allowed, retry_after_seconds).
        """
        now = time.time()
        with self._lock:
            # Get existing request timestamps for this key
            timestamps = self._requests.get(key, [])
            
            # Remove timestamps older than the sliding window
            cutoff = now - window_seconds
            timestamps = [ts for ts in timestamps if ts > cutoff]
            
            # Check if we have exceeded the limit
            if len(timestamps) >= max_requests:
                # Calculate the wait time until the oldest request falls out of the window
                if timestamps:
                    retry_after = int(timestamps[0] + window_seconds - now)
                    if retry_after <= 0:
                        retry_after = 1
                else:
                    retry_after = window_seconds
                self._requests[key] = timestamps
                return False, retry_after
            
            # Add the current timestamp and update the store
            timestamps.append(now)
            self._requests[key] = timestamps
            return True, 0

    def clear(self):
        """
        Clear all rate limit records. Used primarily for testing.
        """
        with self._lock:
            self._requests.clear()

# Global instance of the rate limiter
limiter = InMemoryRateLimiter()

def get_client_ip(request: Request) -> str:
    """
    Extract client IP address, checking the X-Forwarded-For header first.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs separated by commas, the first one is the client
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

def parse_rate_limit(value: str, default: Tuple[int, int]) -> Tuple[int, int]:
    """
    Parse a rate limit string formatted as 'max_requests/window_seconds'.
    Falls back to the default tuple if parsing fails.
    """
    try:
        parts = value.split("/")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except Exception:
        pass
    return default

# Load environment variable configurations with defaults
LIMIT_LOGIN = os.getenv("LIMIT_LOGIN", "5/60")
LIMIT_REGISTER = os.getenv("LIMIT_REGISTER", "3/3600")
LIMIT_AI = os.getenv("LIMIT_AI", "5/60")
LIMIT_DEFAULT = os.getenv("LIMIT_DEFAULT", "60/60")

RATE_LIMIT_CONFIGS = {
    "login": parse_rate_limit(LIMIT_LOGIN, (5, 60)),
    "register": parse_rate_limit(LIMIT_REGISTER, (3, 3600)),
    "ai": parse_rate_limit(LIMIT_AI, (5, 60)),
    "default": parse_rate_limit(LIMIT_DEFAULT, (60, 60)),
}

async def default_rate_limit(request: Request):
    """
    FastAPI dependency to rate limit standard API endpoints by client IP.
    """
    ip = get_client_ip(request)
    key = f"default:{ip}"
    max_requests, window_seconds = RATE_LIMIT_CONFIGS.get("default", (60, 60))
    
    allowed, retry_after = limiter.is_allowed(key, max_requests, window_seconds)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

# Import get_current_user here to avoid circular imports if needed
from app.core.security import get_current_user

async def ai_rate_limit(request: Request, current_user: User = Depends(get_current_user)):
    """
    FastAPI dependency to rate limit expensive AI endpoints by combined user ID and client IP.
    """
    ip = get_client_ip(request)
    key = f"ai:{current_user.id}:{ip}"
    max_requests, window_seconds = RATE_LIMIT_CONFIGS.get("ai", (5, 60))
    
    allowed, retry_after = limiter.is_allowed(key, max_requests, window_seconds)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
