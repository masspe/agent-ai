from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from prisma import Prisma


@dataclass(slots=True)
class ColumnMeta:
    name: str
    data_type: str
    is_nullable: bool
    is_primary: bool
    is_auto_increment: bool

    def convert(self, value: str | None) -> Any:
        if value is None:
            return None
        typ = self.data_type.lower()
        try:
            if typ in {"int", "integer", "mediumint", "smallint", "bigint"}:
                return int(value)
            if typ in {"float", "double", "decimal"}:
                return float(value)
            if typ in {"tinyint"}:
                return int(value)
        except (TypeError, ValueError):
            return value
        return value


@dataclass(slots=True)
class TableMeta:
    name: str
    columns: Dict[str, ColumnMeta]

    @property
    def primary_keys(self) -> List[str]:
        return [c.name for c in self.columns.values() if c.is_primary]

    def has_column(self, name: str) -> bool:
        return name in self.columns

    def column(self, name: str) -> ColumnMeta:
        return self.columns[name]


class SchemaRegistry:
    def __init__(self) -> None:
        self._tables: Dict[str, TableMeta] = {}

    def all_tables(self) -> Iterable[TableMeta]:
        return self._tables.values()

    def get(self, table_name: str) -> Optional[TableMeta]:
        return self._tables.get(table_name)

    async def refresh(self, client: Prisma) -> None:
        rows = await client.query_raw("SELECT DATABASE() AS db")
        if not rows:
            return
        database = rows[0]["db"]

        tables = await client.query_raw(
            """
            SELECT TABLE_NAME FROM information_schema.tables
            WHERE TABLE_SCHEMA = ?
            """,
            database,
        )

        table_names = [row["TABLE_NAME"] for row in tables]
        new_tables: Dict[str, TableMeta] = {}

        for table in table_names:
            columns = await client.query_raw(
                """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, EXTRA
                FROM information_schema.columns
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
                """,
                database,
                table,
            )

            colmap: Dict[str, ColumnMeta] = {}
            for col in columns:
                meta = ColumnMeta(
                    name=col["COLUMN_NAME"],
                    data_type=col["DATA_TYPE"],
                    is_nullable=str(col["IS_NULLABLE"]).upper() == "YES",
                    is_primary=str(col["COLUMN_KEY"]).upper() == "PRI",
                    is_auto_increment="auto_increment" in str(col["EXTRA"]).lower(),
                )
                colmap[meta.name] = meta

            new_tables[table] = TableMeta(name=table, columns=colmap)

        self._tables = new_tables
