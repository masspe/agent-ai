from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db import get_db
from ..dependencies import require_admin
from ..models.user import User
from ..utils import row_to_dict
from ..security.auth import get_password_hash

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])

@router.get("")
def list_users(db: Session = Depends(get_db)):
    rows = db.execute(select(User)).scalars().all()
    return [{k: v for k, v in row_to_dict(r).items() if k != "password_hash"} for r in rows]

@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    d = row_to_dict(u)
    d.pop("password_hash", None)
    return d

@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(data: Dict[str, Any], db: Session = Depends(get_db)):
    if "email" not in data or "password" not in data:
        raise HTTPException(422, "email and password are required")
    if db.query(User).filter(User.email == data["email"]).first():
        raise HTTPException(409, "Email already exists")
    u = User(
        email=data["email"],
        password_hash=get_password_hash(data["password"]),
        role=data.get("role", "user"),
        is_active=bool(data.get("is_active", True)),
        tenant_id=data.get("tenant_id"),
    )
    db.add(u); db.commit(); db.refresh(u)
    d = row_to_dict(u); d.pop("password_hash", None)
    return d

@router.put("/{user_id}")
def update_user(user_id: int, data: Dict[str, Any], db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    if "password" in data and data["password"]:
        u.password_hash = get_password_hash(data.pop("password"))
    for k in ("email","role","is_active","tenant_id"):
        if k in data:
            setattr(u, k, data[k])
    db.commit(); db.refresh(u)
    d = row_to_dict(u); d.pop("password_hash", None)
    return d

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    db.delete(u); db.commit()
    return None
