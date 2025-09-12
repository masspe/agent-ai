from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..db import get_db
from ..models.user import User
from ..security.auth import verify_password, create_access_token, get_password_hash, pwd_context
router = APIRouter(prefix="/auth", tags=["auth"])

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/token", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User disabled")

    # se l'hash esistente è vecchio (es. bcrypt), aggiorna ad Argon2
    if pwd_context.needs_update(user.password_hash):
        user.password_hash = get_password_hash(form.password)
        db.add(user)
        db.commit()

    token = create_access_token({"sub": user.email, "uid": user.id, "tid": user.tenant_id, "role": user.role})
    return TokenOut(access_token=token)
    
@router.post("/seed_admin")
def seed_admin(db: Session = Depends(get_db)):
    email = "admin@example.com"
    if db.query(User).filter(User.email == email).first():
        return {"ok": True, "msg": "admin exists"}
    u = User(email=email, password_hash=get_password_hash("admin123"), role="admin", is_active=True)
    db.add(u); db.commit(); db.refresh(u)
    return {"ok": True, "id": u.id, "email": u.email}
