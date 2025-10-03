from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from prisma import Prisma

from ..db import get_db
from ..dependencies import require_admin
from ..security.auth import get_password_hash
from ..utils import row_to_dict

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])


async def _find_user_by_email(db: Prisma, email: str) -> Dict[str, Any] | None:
    rows = await db.query_raw("SELECT * FROM `users` WHERE email = ? LIMIT 1", email)
    return rows[0] if rows else None


async def _find_user_by_id(db: Prisma, user_id: int) -> Dict[str, Any] | None:
    rows = await db.query_raw("SELECT * FROM `users` WHERE id = ? LIMIT 1", user_id)
    return rows[0] if rows else None


def _sanitize_user(row: Dict[str, Any]) -> Dict[str, Any]:
    data = row_to_dict(row)
    data.pop("password_hash", None)
    return data


@router.get("")
async def list_users(db: Prisma = Depends(get_db)):
    rows = await db.query_raw("SELECT * FROM `users` ORDER BY id")
    return [_sanitize_user(row) for row in rows]


@router.get("/{user_id}")
async def get_user(user_id: int, db: Prisma = Depends(get_db)):
    row = await _find_user_by_id(db, user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return _sanitize_user(row)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(data: Dict[str, Any], db: Prisma = Depends(get_db)):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=422, detail="email and password are required")
    existing = await _find_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    tenant_id = data.get("tenant_id")
    role = data.get("role", "user")
    is_active = 1 if bool(data.get("is_active", True)) else 0

    await db.execute_raw(
        """
        INSERT INTO `users` (email, password_hash, role, is_active, tenant_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, NOW(), NOW())
        """,
        email,
        get_password_hash(password),
        role,
        is_active,
        tenant_id,
    )

    new_user = await _find_user_by_email(db, email)
    if not new_user:
        raise HTTPException(status_code=500, detail="Failed to create user")
    return _sanitize_user(new_user)


@router.put("/{user_id}")
async def update_user(user_id: int, data: Dict[str, Any], db: Prisma = Depends(get_db)):
    user = await _find_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates: Dict[str, Any] = {}
    params: List[Any] = []

    if "password" in data and data["password"]:
        updates["password_hash"] = get_password_hash(data.pop("password"))
    for field in ("email", "role", "tenant_id"):
        if field in data and data[field] is not None:
            updates[field] = data[field]
    if "is_active" in data:
        updates["is_active"] = 1 if bool(data["is_active"]) else 0

    if not updates:
        return _sanitize_user(user)

    set_parts = []
    for key, value in updates.items():
        set_parts.append(f"`{key}` = ?")
        params.append(value)
    set_parts.append("`updated_at` = NOW()")

    params.append(user_id)
    await db.execute_raw(
        f"UPDATE `users` SET {', '.join(set_parts)} WHERE id = ?",
        *params,
    )

    refreshed = await _find_user_by_id(db, user_id)
    if not refreshed:
        raise HTTPException(status_code=500, detail="Failed to load updated user")
    return _sanitize_user(refreshed)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Prisma = Depends(get_db)):
    user = await _find_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.execute_raw("DELETE FROM `users` WHERE id = ?", user_id)
    return None
