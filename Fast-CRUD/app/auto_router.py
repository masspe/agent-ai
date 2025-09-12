# app/auto_router.py
from __future__ import annotations
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import select as sa_select, and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.schema import Column

from .db import get_db
from .utils import row_to_dict
from .dependencies import get_current_user

import re

# --------------------
# Helpers base
# --------------------

def slugify(s: str, maxlen: int = 120) -> str:
    s = s.strip().lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s[:maxlen]

def _has_col(Model, name: str) -> bool:
    return name in Model.__table__.columns.keys()

def _pk_filters(Model, pk_cols: List[str], path_params: Dict[str, str]):
    filters = []
    for c in pk_cols:
        raw = path_params[c]
        col: Column = Model.__table__.c[c]
        try:
            pytype = col.type.python_type
        except Exception:
            pytype = str
        val = raw
        try:
            if pytype is int:
                val = int(raw)
            elif pytype is float:
                val = float(raw)
            elif pytype is bool:
                val = str(raw).lower() in {"1", "true", "t", "yes", "y"}
        except Exception:
            val = raw
        filters.append(col == val)
    return filters

def _scope_stmt_by_tenant(Model, stmt, user):
    if _has_col(Model, "tenant_id"):
        tenant_id = getattr(user, "tenant_id", None)
        if tenant_id is None:
            raise HTTPException(status_code=400, detail="Current user has no tenant_id; cannot access multitenant tables.")
        stmt = stmt.where(Model.__table__.c.tenant_id == tenant_id)
    return stmt

def _ensure_unique_slug(Model, base_slug: str, db: Session) -> str:
    """Rende unico lo slug: test -> test, test-2, test-3, ... considerando vincolo UNIQUE globale sulla colonna."""
    col = Model.__table__.c.get("slug")
    if col is None:
        return base_slug
    base = base_slug[:120]
    slug = base
    i = 1
    while True:
        exists_stmt = sa_select(func.count()).select_from(Model).where(col == slug)
        count = db.execute(exists_stmt).scalar() or 0
        if count == 0:
            return slug
        i += 1
        suffix = f"-{i}"
        slug = (base[: 120 - len(suffix)]) + suffix

def _inject_defaults_on_create(Model, payload: Dict[str, Any], user, db: Session):
    cols = Model.__table__.columns.keys()

    if "tenant_id" in cols and (payload.get("tenant_id") in (None, "")):
        tenant_id = getattr(user, "tenant_id", None)
        if tenant_id is None:
            raise HTTPException(status_code=400, detail="Current user has no tenant_id; provide tenant_id or assign one to the user.")
        payload["tenant_id"] = tenant_id

    if "created_by" in cols and not payload.get("created_by"):
        user_id = getattr(user, "id", None)
        if user_id is not None:
            payload["created_by"] = user_id

    if "slug" in cols:
        # genera da name se mancante
        if not payload.get("slug") and payload.get("name"):
            payload["slug"] = slugify(str(payload["name"]))
        # garantisci unicità (vincolo UNIQUE su slug)
        if payload.get("slug"):
            payload["slug"] = _ensure_unique_slug(Model, payload["slug"], db)

    return payload

# --------------------
# Router factory
# --------------------

def build_router_for_model(Model, table_name: str, pk_cols: List[str], dependencies=None) -> APIRouter:
    """
    CRUD semplice con scoping tenant e slug unico:
      - LIST   GET /{table}?limit&offset
      - GET    GET /{table}/{pk}
      - CREATE POST /{table}        (inietta tenant_id/created_by, slug unico)
      - UPDATE PUT /{table}/{pk}    (slug unico se cambiato, no cambio tenant_id)
      - DELETE DELETE /{table}/{pk}
    """
    deps = dependencies or []
    router = APIRouter(prefix=f"/{table_name}", tags=[table_name], dependencies=deps)

    @router.get("")
    def list_items(
        db: Session = Depends(get_db),
        user=Depends(get_current_user),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ):
        stmt = sa_select(Model)
        stmt = _scope_stmt_by_tenant(Model, stmt, user)
        stmt = stmt.limit(limit).offset(offset)
        rows = db.execute(stmt).scalars().all()
        return [row_to_dict(r) for r in rows]

    pk_path = "/".join([f"{{{c}}}" for c in pk_cols])

    @router.get(f"/{pk_path}")
    def get_item(
        request: Request,
        db: Session = Depends(get_db),
        user=Depends(get_current_user),
    ):
        filters = _pk_filters(Model, pk_cols, request.path_params)
        stmt = sa_select(Model).where(and_(*filters))
        stmt = _scope_stmt_by_tenant(Model, stmt, user)
        obj = db.execute(stmt).scalars().first()
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        return row_to_dict(obj)

    @router.post("", status_code=status.HTTP_201_CREATED)
    def create_item(
        data: Dict[str, Any] = Body(...),
        db: Session = Depends(get_db),
        user=Depends(get_current_user),
    ):
        cols = Model.__table__.columns.keys()
        payload = {k: v for k, v in data.items() if k in cols}
        payload = _inject_defaults_on_create(Model, payload, user, db)

        # non permettere tenant_id diverso
        if "tenant_id" in cols and payload.get("tenant_id") != getattr(user, "tenant_id", None):
            raise HTTPException(status_code=403, detail="Forbidden tenant_id.")

        obj = Model(**payload)
        db.add(obj)
        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            # se c'è qualche vincolo unique (es. slug) fallito
            raise HTTPException(status_code=409, detail="Unique constraint violation") from e

        db.refresh(obj)
        return row_to_dict(obj)

    @router.put(f"/{pk_path}")
    def update_item(
        request: Request,
        data: Dict[str, Any] = Body(...),
        db: Session = Depends(get_db),
        user=Depends(get_current_user),
    ):
        filters = _pk_filters(Model, pk_cols, request.path_params)
        stmt = sa_select(Model).where(and_(*filters))
        stmt = _scope_stmt_by_tenant(Model, stmt, user)
        obj = db.execute(stmt).scalars().first()
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")

        cols = Model.__table__.columns.keys()
        for k, v in data.items():
            if k in pk_cols or k == "tenant_id":
                continue
            if k == "slug" and v:
                v = _ensure_unique_slug(Model, slugify(str(v)), db)
            if k in cols:
                setattr(obj, k, v)

        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=409, detail="Unique constraint violation") from e

        db.refresh(obj)
        return row_to_dict(obj)

    @router.delete(f"/{pk_path}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(
        request: Request,
        db: Session = Depends(get_db),
        user=Depends(get_current_user),
    ):
        filters = _pk_filters(Model, pk_cols, request.path_params)
        stmt = sa_select(Model).where(and_(*filters))
        stmt = _scope_stmt_by_tenant(Model, stmt, user)
        obj = db.execute(stmt).scalars().first()
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        db.delete(obj)
        db.commit()
        return None

    return router
