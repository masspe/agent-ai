from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from prisma import Prisma

from ..db import get_db
from ..security.auth import verify_password, create_access_token, get_password_hash, pwd_context

router = APIRouter(prefix="/auth", tags=["auth"])

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

async def _find_user_by_email(db: Prisma, email: str) -> Dict[str, Any] | None:
    rows = await db.query_raw("SELECT * FROM `users` WHERE email = ? LIMIT 1", email)
    return rows[0] if rows else None


@router.post("/token", response_model=TokenOut)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: Prisma = Depends(get_db)):
    user = await _find_user_by_email(db, form.username)
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User disabled")

    # se l'hash esistente è vecchio (es. bcrypt), aggiorna ad Argon2
    if pwd_context.needs_update(user["password_hash"]):
        new_hash = get_password_hash(form.password)
        await db.execute_raw("UPDATE `users` SET password_hash = ?, updated_at = NOW() WHERE id = ?", new_hash, user["id"])
        user["password_hash"] = new_hash

    token = create_access_token({
        "sub": user["email"],
        "uid": user.get("id"),
        "tid": user.get("tenant_id"),
        "role": user.get("role"),
    })
    return TokenOut(access_token=token)

@router.post("/seed_admin")
async def seed_admin(db: Prisma = Depends(get_db)):
    email = "admin@example.com"
    existing = await _find_user_by_email(db, email)
    if existing:
        return {"ok": True, "msg": "admin exists"}
    password_hash = get_password_hash("admin123")
    await db.execute_raw(
        """
        INSERT INTO `users` (email, password_hash, role, is_active, created_at, updated_at)
        VALUES (?, ?, 'admin', 1, NOW(), NOW())
        """,
        email,
        password_hash,
    )
    user = await _find_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create admin user")
    return {"ok": True, "id": user.get("id"), "email": user.get("email")}
