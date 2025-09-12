# bootstrap_auto_backend_v2.py
from pathlib import Path

FILES = {
    "requirements.txt": '''fastapi==0.111.0
uvicorn[standard]==0.30.1
SQLAlchemy==2.0.30
pymysql==1.1.0
python-dotenv==1.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
mariadb==1.1.10
''',

    ".env.example": '''# Imposta una delle due:
#DATABASE_URL=mariadb+mariadbconnector://user:pass@localhost:3306/agent_app
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/agent_app

FRONTEND_ORIGIN=http://localhost:3000
SECRET_KEY=change_me_super_secret_and_long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
''',

    "app/__init__.py": "",

    "app/db.py": '''import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:pass@localhost:3306/agent_app")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',

    "app/security/__init__.py": "",

    "app/security/auth.py": '''import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_change_me")
ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {**data, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
''',

    "app/dependencies.py": '''from __future__ import annotations
import os
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from .db import get_db
from .models.user import User

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

def get_current_user(request: Request, token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
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
    user = db.query(User).filter(User.email == email).first()
    if not user or not getattr(user, "is_active", True):
        raise cred_exc
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if getattr(user, "role", "user") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user
''',

    "app/utils.py": '''from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal

def row_to_dict(obj):
    if hasattr(obj, "__table__"):
        cols = obj.__table__.columns.keys()
        d = {}
        for c in cols:
            v = getattr(obj, c)
            if isinstance(v, (datetime, date)):
                d[c] = v.isoformat()
            elif isinstance(v, Decimal):
                d[c] = float(v)
            else:
                d[c] = v
        return d
    return dict(obj)
''',

    "app/auto_router.py": '''from __future__ import annotations
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from .db import get_db
from .utils import row_to_dict

def build_router_for_model(Model, table_name: str, pk_cols: list[str], dependencies=None) -> APIRouter:
    deps = dependencies or []
    router = APIRouter(prefix=f"/{table_name}", tags=[table_name], dependencies=deps)

    @router.get("")
    def list_items(
        db: Session = Depends(get_db),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ):
        stmt = select(Model).limit(limit).offset(offset)
        rows = db.execute(stmt).scalars().all()
        return [row_to_dict(r) for r in rows]

    pk_path = "/".join([f"{{{c}}}" for c in pk_cols])

    @router.get(f"/{pk_path}")
    def get_item(request: Request, db: Session = Depends(get_db)):
        path_params = request.path_params
        filters = [getattr(Model, c) == path_params[c] for c in pk_cols]
        stmt = select(Model).where(and_(*filters))
        obj = db.execute(stmt).scalars().first()
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        return row_to_dict(obj)

    @router.post("", status_code=status.HTTP_201_CREATED)
    def create_item(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
        cols = Model.__table__.columns.keys()
        payload = {k: v for k, v in data.items() if k in cols}
        obj = Model(**payload)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return row_to_dict(obj)

    @router.put(f"/{pk_path}")
    def update_item(request: Request, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
        path_params = request.path_params
        filters = [getattr(Model, c) == path_params[c] for c in pk_cols]
        obj = db.execute(select(Model).where(and_(*filters))).scalars().first()
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        cols = Model.__table__.columns.keys()
        for k, v in data.items():
            if k in cols and k not in pk_cols:
                setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return row_to_dict(obj)

    @router.delete(f"/{pk_path}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(request: Request, db: Session = Depends(get_db)):
        path_params = request.path_params
        filters = [getattr(Model, c) == path_params[c] for c in pk_cols]
        obj = db.execute(select(Model).where(and_(*filters))).scalars().first()
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        db.delete(obj)
        db.commit()
        return None

    return router
''',

    "app/models/__init__.py": "",

    "app/models/base.py": '''from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)

class BaseApp(DeclarativeBase):
    metadata = metadata
''',

    "app/models/user.py": '''from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index, func, text
from .base import BaseApp

class User(BaseApp):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tenants.id"), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        Index("ix_users_email", "email"),
    )
''',

    "app/routers/__init__.py": "",

    "app/routers/auth.py": '''from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..db import get_db
from ..models.user import User
from ..security.auth import verify_password, create_access_token, get_password_hash

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
''',

    "app/routers/health.py": '''from fastapi import APIRouter
router = APIRouter(prefix="/health", tags=["health"])
@router.get("/ping")
def ping():
    return {"ok": True}
''',

    "app/routers/me.py": '''from fastapi import APIRouter, Depends
from ..dependencies import get_current_user
from ..models.user import User
router = APIRouter(tags=["me"])
@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role, "tenant_id": user.tenant_id, "is_active": user.is_active}
''',

    "app/routers/users.py": '''from typing import Dict, Any
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
''',

    "app/main.py": '''import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.automap import automap_base
from sqlalchemy import inspect

from .db import engine
from .dependencies import get_current_user, require_admin
from .auto_router import build_router_for_model
from .models.base import BaseApp
from .models.user import User  # dich. per tabella users

# crea 'users' se non esiste
BaseApp.metadata.create_all(bind=engine)

app = FastAPI(title="Agent Builder Auto-CRUD API", version="3.0.0")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routers import auth, health, me, users
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(me.router)
app.include_router(users.router)

Base = automap_base()
Base.prepare(autoload_with=engine)

EXCLUDE = {"users", "alembic_version"}

inspector = inspect(engine)
# ricava mappature in modo robusto (SQLAlchemy 2.x)
table_to_model = {}
for mapper in Base.registry.mappers:
    cls = mapper.class_
    table = getattr(cls, "__table__", None)
    if not table:
        continue
    table_name = table.name
    if table_name in EXCLUDE:
        continue
    table_to_model[table_name] = cls

for table_name, Model in table_to_model.items():
    pk_cols = inspector.get_pk_constraint(table_name).get("constrained_columns") or []
    if not pk_cols:
        continue
    deps = [Depends(get_current_user)]
    # Esempio: admin-only
    # if table_name in {"api_keys", "audits"}:
    #     deps = [Depends(require_admin)]
    router = build_router_for_model(Model, table_name=table_name, pk_cols=pk_cols, dependencies=deps)
    app.include_router(router)

@app.get("/")
def root():
    return {"ok": True, "auto_tables": sorted(table_to_model.keys())}
''',

    "README.md": '''# Agent Builder — Backend Auto-CRUD

## Setup rapido
```bash
python -m venv .venv
# Windows PowerShell
. .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# modifica DATABASE_URL in .env (mariadbconnector oppure pymysql)
python -m uvicorn app.main:app --reload
''',
}

def write_files():
    for path, content in FILES.items():
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    print("✅ Backend creato. Ora esegui i passaggi nel README.")

if __name__ == "__main__":
    write_files()