from typing import Any, Dict

from fastapi import APIRouter, Depends

from ..dependencies import get_current_user

router = APIRouter(tags=["me"])


@router.get("/me")
async def me(user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "role": user.get("role"),
        "tenant_id": user.get("tenant_id"),
        "is_active": user.get("is_active"),
    }
