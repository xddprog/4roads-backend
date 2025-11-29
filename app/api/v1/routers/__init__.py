from fastapi import APIRouter

from app.api.v1.routers.product import router as product_router
from app.api.v1.routers.faq import router as faq_router
from app.api.v1.routers.contact_form import router as contact_form_router
from app.api.v1.routers.settings import router as settings_router
from app.api.v1.routers.review import router as review_router
from app.api.v1.routers.filters import router as filters_router


api_v1_routers = APIRouter(prefix="/api/v1")
api_v1_routers.include_router(product_router, prefix="/product", tags=["product"])
api_v1_routers.include_router(faq_router, prefix="/faq", tags=["faq"])
api_v1_routers.include_router(contact_form_router, prefix="/contact", tags=["contact_form"])
api_v1_routers.include_router(settings_router, prefix="/settings", tags=["settings"])
api_v1_routers.include_router(review_router, prefix="/review", tags=["review"])
api_v1_routers.include_router(filters_router, prefix="/filters", tags=["filters"])