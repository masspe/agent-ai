from fastapi import APIRouter, Depends
from ..dependencies import get_current_user
from ..models.user import User
router = APIRouter(tags=["me"])
@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role, "tenant_id": user.tenant_id, "is_active": user.is_active}
