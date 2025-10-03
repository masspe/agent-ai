from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import Header, HTTPException
from prisma import Prisma

DEFAULT_SAMPLE_URL = "mysql://user:pass@localhost:3306/agent_app"


def _load_database_urls() -> Dict[str, str]:
    """Load database aliases from environment variables."""

    mapping: Dict[str, str] = {}

    raw = os.getenv("DATABASES")
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:  # pragma: no cover - configuration error
            raise RuntimeError("Invalid DATABASES value; expected JSON mapping of alias to URL.") from exc
        if not isinstance(parsed, dict):  # pragma: no cover - configuration error
            raise RuntimeError("DATABASES must be a JSON object mapping alias to URL.")
        mapping.update({str(k): str(v) for k, v in parsed.items()})

    default_url = os.getenv("DATABASE_URL")
    if default_url:
        mapping.setdefault("default", default_url)

    if not mapping:
        mapping["default"] = DEFAULT_SAMPLE_URL

    return mapping


@dataclass(slots=True)
class PrismaEntry:
    alias: str
    client: Prisma
    lock: asyncio.Lock


class PrismaManager:
    """Light-weight registry that keeps Prisma clients connected per alias."""

    def __init__(self, mapping: Dict[str, str], default_alias: Optional[str] = None) -> None:
        if not mapping:  # pragma: no cover - configuration error
            raise RuntimeError("At least one database URL is required")

        self._mapping = mapping
        self._default = default_alias or next(iter(mapping))
        if self._default not in mapping:
            self._default = next(iter(mapping))

        self._entries: Dict[str, PrismaEntry] = {}
        for alias, url in mapping.items():
            client = Prisma(datasource={"url": url})
            self._entries[alias] = PrismaEntry(alias=alias, client=client, lock=asyncio.Lock())

    @property
    def default_alias(self) -> str:
        return self._default

    @property
    def aliases(self) -> Dict[str, str]:
        return dict(self._mapping)

    async def _ensure_connected(self, entry: PrismaEntry) -> Prisma:
        if entry.client.is_connected():
            return entry.client
        async with entry.lock:
            if not entry.client.is_connected():
                await entry.client.connect()
        return entry.client

    async def get_client(self, alias: Optional[str] = None) -> Prisma:
        name = alias or self._default
        entry = self._entries.get(name)
        if entry is None:
            raise HTTPException(status_code=400, detail=f"Unknown database alias '{name}'")
        return await self._ensure_connected(entry)

    async def connect_all(self) -> None:
        for entry in self._entries.values():
            await self._ensure_connected(entry)

    async def disconnect_all(self) -> None:
        for entry in self._entries.values():
            if entry.client.is_connected():
                await entry.client.disconnect()


_manager = PrismaManager(_load_database_urls(), default_alias=os.getenv("DEFAULT_DATABASE"))


async def get_db(x_database: str | None = Header(default=None)):
    """FastAPI dependency that yields a Prisma client for the requested alias."""

    client = await _manager.get_client(x_database)
    try:
        yield client
    finally:
        # Clients stay connected for reuse; shutdown handler disconnects them.
        pass


async def connect_to_databases() -> None:
    await _manager.connect_all()


async def disconnect_from_databases() -> None:
    await _manager.disconnect_all()


def get_database_aliases() -> Dict[str, str]:
    return _manager.aliases


def get_default_alias() -> str:
    return _manager.default_alias


async def get_prisma(alias: Optional[str] = None) -> Prisma:
    return await _manager.get_client(alias)
