from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_current_admin_dependency
from app.api.v1.routers.admin.auth_router import router as auth_router
from app.infrastructure.errors.auth_errors import AccessDenied, InvalidCredentials
from app.utils.error_extra import error_response


PROTECTED =Depends(get_current_admin_dependency)
AUTH_ERRORS = {
    **error_response(AccessDenied),
    **error_response(InvalidCredentials)
}
admin_routers = APIRouter(prefix="/admin")


admin_routers.include_router(auth_router, tags=["AUTH"], prefix="/auth")
