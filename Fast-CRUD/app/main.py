import os
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
from fastapi.routing import APIRoute


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
    if table is None:
        continue
    table_name = table.name
    if isinstance(table_name, bytes):
        table_name = table_name.decode()
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


@app.get("/__routes", tags=["meta"])
def list_routes():
    out = []
    for r in app.routes:
        if isinstance(r, APIRoute):
            out.append({
                "path": r.path,
                "methods": sorted([m for m in r.methods if m not in {"HEAD","OPTIONS"}]),
                "name": r.name,
                "summary": (r.summary or "")[:120]
            })
    return sorted(out, key=lambda x: x["path"])

# Elenco tabelle viste a DB (indipendente dall’automap)
@app.get("/__tables", tags=["meta"])
def list_tables():
    return {"tables": sorted(inspector.get_table_names())}