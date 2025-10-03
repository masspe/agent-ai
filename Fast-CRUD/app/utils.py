from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Mapping


def _serialize(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def row_to_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "__table__"):
        cols = obj.__table__.columns.keys()
        return {c: _serialize(getattr(obj, c)) for c in cols}
    if isinstance(obj, Mapping):
        return {str(k): _serialize(v) for k, v in obj.items()}
    raise TypeError(f"Unsupported row type: {type(obj)!r}")
