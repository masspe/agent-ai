from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from prisma import Prisma

from .db import get_db
from .dependencies import get_current_user
from .schema_registry import TableMeta
from .utils import row_to_dict


def slugify(value: str, maxlen: int = 120) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:maxlen]


def _quote(column: str) -> str:
    return f"`{column}`"


def _prepare_pk(meta: TableMeta, path_params: Dict[str, str]) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for name in meta.primary_keys:
        if name not in path_params:
            raise HTTPException(status_code=400, detail=f"Missing primary key segment '{name}'")
        col = meta.column(name)
        values[name] = col.convert(path_params[name])
    return values


def _build_conditions(pairs: Dict[str, Any]) -> tuple[str, List[Any]]:
    clauses: List[str] = []
    params: List[Any] = []
    for column, value in pairs.items():
        clauses.append(f"{_quote(column)} = ?")
        params.append(value)
    return " AND ".join(clauses), params


def _filter_payload(meta: TableMeta, data: Dict[str, Any]) -> Dict[str, Any]:
    allowed = meta.columns.keys()
    return {k: v for k, v in data.items() if k in allowed}


async def _ensure_unique_slug(
    meta: TableMeta,
    base_slug: str,
    db: Prisma,
    tenant_value: Any | None,
    exclude: Dict[str, Any] | None = None,
) -> str:
    if not base_slug:
        return base_slug
    base = base_slug[:120]
    slug = base
    index = 1
    while True:
        params: List[Any] = [slug]
        clause = "slug = ?"
        if meta.has_column("tenant_id") and tenant_value is not None:
            clause += " AND tenant_id = ?"
            params.append(tenant_value)
        if exclude:
            excl_clause, excl_params = _build_conditions(exclude)
            clause += f" AND NOT ({excl_clause})"
            params.extend(excl_params)
        rows = await db.query_raw(
            f"SELECT COUNT(*) AS cnt FROM {_quote(meta.name)} WHERE {clause}",
            *params,
        )
        count = rows[0]["cnt"] if rows else 0
        if int(count) == 0:
            return slug
        index += 1
        suffix = f"-{index}"
        slug = (base[: 120 - len(suffix)]) + suffix


async def _inject_defaults_on_create(meta: TableMeta, payload: Dict[str, Any], user: Dict[str, Any], db: Prisma) -> Dict[str, Any]:
    if meta.has_column("tenant_id") and payload.get("tenant_id") in (None, ""):
        tenant_id = user.get("tenant_id")
        if tenant_id is None:
            raise HTTPException(status_code=400, detail="Current user has no tenant context.")
        payload["tenant_id"] = tenant_id

    if meta.has_column("created_by") and not payload.get("created_by"):
        user_id = user.get("id")
        if user_id is not None:
            payload["created_by"] = user_id

    if meta.has_column("slug"):
        if not payload.get("slug") and payload.get("name"):
            payload["slug"] = slugify(str(payload["name"]))
        if payload.get("slug"):
            tenant_scope = payload.get("tenant_id") if meta.has_column("tenant_id") else None
            payload["slug"] = await _ensure_unique_slug(meta, payload["slug"], db, tenant_scope)

    return payload


async def _fetch_single(db: Prisma, table: TableMeta, conditions: Dict[str, Any]) -> Dict[str, Any] | None:
    clause, params = _build_conditions(conditions)
    rows = await db.query_raw(
        f"SELECT * FROM {_quote(table.name)} WHERE {clause} LIMIT 1",
        *params,
    )
    return rows[0] if rows else None


async def _list_rows(db: Prisma, table: TableMeta, clause: str, params: Iterable[Any], limit: int, offset: int) -> List[Dict[str, Any]]:
    sql = f"SELECT * FROM {_quote(table.name)}"
    if clause:
        sql += f" WHERE {clause}"
    if table.primary_keys:
        sql += " ORDER BY " + ",".join(_quote(pk) for pk in table.primary_keys)
    sql += " LIMIT ? OFFSET ?"
    params = list(params) + [limit, offset]
    return await db.query_raw(sql, *params)


async def _execute(db: Prisma, sql: str, params: Iterable[Any]) -> None:
    await db.execute_raw(sql, *params)


def build_router_for_table(meta: TableMeta, dependencies=None) -> APIRouter:
    deps = dependencies or []
    router = APIRouter(prefix=f"/{meta.name}", tags=[meta.name], dependencies=deps)

    @router.get("")
    async def list_items(
        db: Prisma = Depends(get_db),
        user: Dict[str, Any] = Depends(get_current_user),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ):
        clause = ""
        params: List[Any] = []
        if meta.has_column("tenant_id"):
            tenant_id = user.get("tenant_id")
            if tenant_id is None:
                raise HTTPException(status_code=400, detail="Current user has no tenant context.")
            clause, params = _build_conditions({"tenant_id": tenant_id})

        rows = await _list_rows(db, meta, clause, params, limit, offset)
        return [row_to_dict(r) for r in rows]

    pk_path = "/".join([f"{{{c}}}" for c in meta.primary_keys])

    @router.get(f"/{pk_path}")
    async def get_item(
        request: Request,
        db: Prisma = Depends(get_db),
        user: Dict[str, Any] = Depends(get_current_user),
    ):
        pk_values = _prepare_pk(meta, request.path_params)
        if meta.has_column("tenant_id"):
            tenant_id = user.get("tenant_id")
            if tenant_id is None:
                raise HTTPException(status_code=400, detail="Current user has no tenant context.")
            pk_values["tenant_id"] = tenant_id
        row = await _fetch_single(db, meta, pk_values)
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return row_to_dict(row)

    @router.post("", status_code=status.HTTP_201_CREATED)
    async def create_item(
        data: Dict[str, Any] = Body(...),
        db: Prisma = Depends(get_db),
        user: Dict[str, Any] = Depends(get_current_user),
    ):
        payload = _filter_payload(meta, data)
        payload = await _inject_defaults_on_create(meta, payload, user, db)

        if meta.has_column("tenant_id") and payload.get("tenant_id") != user.get("tenant_id"):
            raise HTTPException(status_code=403, detail="Forbidden tenant scope")

        columns = list(payload.keys())
        if not columns:
            raise HTTPException(status_code=400, detail="No valid columns provided")

        placeholders = ",".join("?" for _ in columns)
        quoted_cols = ",".join(_quote(col) for col in columns)
        values = [payload[col] for col in columns]

        try:
            await _execute(
                db,
                f"INSERT INTO {_quote(meta.name)} ({quoted_cols}) VALUES ({placeholders})",
                values,
            )
        except Exception as exc:  # pragma: no cover - relies on DB error codes
            if "Duplicate" in str(exc):
                raise HTTPException(status_code=409, detail="Unique constraint violation") from exc
            raise

        lookup_payload = dict(payload)
        row = None
        if len(meta.primary_keys) == 1:
            pk = meta.primary_keys[0]
            if lookup_payload.get(pk) in (None, "") and meta.column(pk).is_auto_increment:
                last = await db.query_raw("SELECT LAST_INSERT_ID() AS last_id")
                if last:
                    lookup_payload[pk] = last[0]["last_id"]
        if row is None:
            keys: Dict[str, Any] = {}
            for pk in meta.primary_keys:
                value = lookup_payload.get(pk)
                if value in (None, ""):
                    raise HTTPException(status_code=500, detail=f"Missing primary key value for '{pk}' after insert")
                keys[pk] = value
            if meta.has_column("tenant_id"):
                keys["tenant_id"] = payload.get("tenant_id", user.get("tenant_id"))
            row = await _fetch_single(db, meta, keys)

        if not row:
            raise HTTPException(status_code=500, detail="Failed to load inserted row")
        return row_to_dict(row)

    @router.put(f"/{pk_path}")
    async def update_item(
        request: Request,
        data: Dict[str, Any] = Body(...),
        db: Prisma = Depends(get_db),
        user: Dict[str, Any] = Depends(get_current_user),
    ):
        pk_values = _prepare_pk(meta, request.path_params)
        if meta.has_column("tenant_id"):
            tenant_id = user.get("tenant_id")
            if tenant_id is None:
                raise HTTPException(status_code=400, detail="Current user has no tenant context.")
            pk_values["tenant_id"] = tenant_id

        row = await _fetch_single(db, meta, pk_values)
        if not row:
            raise HTTPException(status_code=404, detail="Not found")

        payload = _filter_payload(meta, data)
        for pk in meta.primary_keys:
            payload.pop(pk, None)
        payload.pop("tenant_id", None)

        if meta.has_column("slug") and "slug" in payload:
            new_slug = payload.get("slug")
            if new_slug:
                normalized = slugify(str(new_slug))
                current_slug = row.get("slug")
                if normalized != current_slug:
                    tenant_scope = pk_values.get("tenant_id") if meta.has_column("tenant_id") else None
                    exclude = {pk: row[pk] for pk in meta.primary_keys if pk in row}
                    if meta.has_column("tenant_id") and "tenant_id" in pk_values:
                        exclude["tenant_id"] = pk_values["tenant_id"]
                    payload["slug"] = await _ensure_unique_slug(meta, normalized, db, tenant_scope, exclude=exclude)
                else:
                    payload["slug"] = current_slug
            else:
                payload.pop("slug", None)

        if not payload:
            return row_to_dict(row)

        assignments = []
        params: List[Any] = []
        for key, value in payload.items():
            assignments.append(f"{_quote(key)} = ?")
            params.append(value)

        where_clause, where_params = _build_conditions(pk_values)
        sql = f"UPDATE {_quote(meta.name)} SET {', '.join(assignments)} WHERE {where_clause}"

        try:
            await _execute(db, sql, params + where_params)
        except Exception as exc:  # pragma: no cover
            if "Duplicate" in str(exc):
                raise HTTPException(status_code=409, detail="Unique constraint violation") from exc
            raise

        updated = await _fetch_single(db, meta, pk_values)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to load updated row")
        return row_to_dict(updated)

    @router.delete(f"/{pk_path}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_item(
        request: Request,
        db: Prisma = Depends(get_db),
        user: Dict[str, Any] = Depends(get_current_user),
    ):
        pk_values = _prepare_pk(meta, request.path_params)
        if meta.has_column("tenant_id"):
            tenant_id = user.get("tenant_id")
            if tenant_id is None:
                raise HTTPException(status_code=400, detail="Current user has no tenant context.")
            pk_values["tenant_id"] = tenant_id

        row = await _fetch_single(db, meta, pk_values)
        if not row:
            raise HTTPException(status_code=404, detail="Not found")

        where_clause, params = _build_conditions(pk_values)
        await _execute(db, f"DELETE FROM {_quote(meta.name)} WHERE {where_clause}", params)
        return None

    return router
