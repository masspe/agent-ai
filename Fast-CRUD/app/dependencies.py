from __future__ import annotations
import os
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request, Header, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from prisma import Prisma

from .db import get_db

SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_change_me")
ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

def _extract_bearer_token(request: Request, authorization: str | None = Header(default=None)) -> str | None:
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
    cookie_token = request.cookies.get("token")
    if cookie_token:
        return cookie_token
    return None

async def _fetch_user_by_email(db: Prisma, email: str) -> Dict[str, Any] | None:
    rows = await db.query_raw("SELECT * FROM `users` WHERE email = ? LIMIT 1", email)
    return rows[0] if rows else None


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Prisma = Depends(get_db),
) -> Dict[str, Any]:
    cred_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials",
                             headers={"WWW-Authenticate": "Bearer"})
    token = token or _extract_bearer_token(request)
    if not token:
        raise cred_exc
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise cred_exc
    except JWTError:
        raise cred_exc
    user = await _fetch_user_by_email(db, email)
    if not user or not user.get("is_active", True):
        raise cred_exc
    return user

async def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user.get("role", "user") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user
