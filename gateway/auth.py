"""API key authentication."""
from fastapi import Request, HTTPException, status

from .config import get_settings


def get_api_key(request: Request) -> str | None:
    """Extract API key from header or query param."""
    # Check X-API-Key header first
    key = request.headers.get("X-API-Key")
    if key:
        return key
    # Fallback to query param
    return request.query_params.get("api_key")


def validate_api_key(api_key: str | None) -> bool:
    """Validate API key against configured keys."""
    if not api_key:
        return False
    settings = get_settings()
    valid_keys = [k.strip() for k in settings.api_keys.split(",") if k.strip()]
    if not valid_keys:
        # No keys configured = allow all (dev mode)
        return True
    return api_key in valid_keys


def verify_api_key(api_key: str | None) -> bool:
    """Alias for validate_api_key."""
    return validate_api_key(api_key)


async def require_api_key(request: Request) -> str:
    """Raise 401 if no valid API key. Returns the validated key."""
    key = get_api_key(request)
    if not validate_api_key(key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-API-Key header or api_key query param.",
        )
    return key or ""
