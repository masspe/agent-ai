import os
from typing import List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from .auto_router import build_router_for_table
from .db import (
    connect_to_databases,
    disconnect_from_databases,
    get_database_aliases,
    get_default_alias,
    get_prisma,
)
from .dependencies import get_current_user
from .schema_registry import SchemaRegistry

load_dotenv()

app = FastAPI(title="Agent Builder Auto-CRUD API", version="4.0.0")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routers import auth, health, me, users  # noqa: E402

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(me.router)
app.include_router(users.router)

EXCLUDE_TABLES = {"users", "alembic_version"}

schema_registry = SchemaRegistry()


async def _ensure_users_table() -> None:
    client = await get_prisma()
    await client.execute_raw(
        """
        CREATE TABLE IF NOT EXISTS `users` (
            id INT UNSIGNED NOT NULL AUTO_INCREMENT,
            tenant_id INT NULL,
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(32) NOT NULL DEFAULT 'user',
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uq_users_tenant_email (tenant_id, email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


async def _register_dynamic_routers() -> None:
    if getattr(app.state, "auto_routes_registered", False):
        return

    await schema_registry.refresh(await get_prisma())

    for table in schema_registry.all_tables():
        if table.name in EXCLUDE_TABLES:
            continue
        if not table.primary_keys:
            continue
        deps = [Depends(get_current_user)]
        router = build_router_for_table(table, dependencies=deps)
        app.include_router(router)

    app.state.auto_routes_registered = True


@app.on_event("startup")
async def on_startup() -> None:
    await connect_to_databases()
    await _ensure_users_table()
    await _register_dynamic_routers()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await disconnect_from_databases()


@app.get("/")
async def root():
    tables: List[str] = [table.name for table in schema_registry.all_tables() if table.name not in EXCLUDE_TABLES]
    return {
        "ok": True,
        "auto_tables": sorted(tables),
        "default_database": get_default_alias(),
        "databases": get_database_aliases(),
    }


@app.get("/__routes", tags=["meta"])
async def list_routes():
    out = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = sorted([m for m in route.methods if m not in {"HEAD", "OPTIONS"}])
            out.append({
                "path": route.path,
                "methods": methods,
                "name": route.name,
                "summary": (route.summary or "")[:120],
            })
    return sorted(out, key=lambda item: item["path"])


@app.get("/__tables", tags=["meta"])
async def list_tables():
    return {"tables": sorted(table.name for table in schema_registry.all_tables())}
