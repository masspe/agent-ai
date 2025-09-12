from __future__ import annotations
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
