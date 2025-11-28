from fastapi import APIRouter

from app.api.v1.routers.admin import admin_routers

api_v1_routers = APIRouter(prefix="/api/v1")
api_v1_routers.include_router(admin_routers)