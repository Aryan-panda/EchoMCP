from typing import Optional
from fastapi import Header, HTTPException, status
from app.config import settings

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Invalid or missing MCP Bearer Token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_token(token: str) -> bool:
    """Compare provided token against configured MCP_AUTH_TOKEN."""
    if not settings.MCP_AUTH_TOKEN:
        return True
    return token == settings.MCP_AUTH_TOKEN

async def require_auth(authorization: Optional[str] = Header(None)) -> str:
    """FastAPI dependency to enforce Bearer token authentication."""
    if not authorization:
        raise AuthenticationError("Authorization header is missing")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid Authorization header format. Expected 'Bearer <token>'")

    token = parts[1]
    if not verify_token(token):
        raise AuthenticationError("Invalid Bearer token")

    return token
