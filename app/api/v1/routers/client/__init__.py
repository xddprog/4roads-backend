from fastapi import APIRouter

from app.api.v1.routers.client.settings import router as settings_router
from app.api.v1.routers.client.contact_form import router as contact_form_router
from app.api.v1.routers.client.faq import router as faq_router
from app.api.v1.routers.client.product import router as product_router


client_routers = APIRouter()


client_routers.include_router(settings_router, prefix="/settings", tags=["Settings"])
client_routers.include_router(contact_form_router, prefix="/contact", tags=["Contact Form"])
client_routers.include_router(faq_router, prefix="/faq", tags=["FAQ"])
client_routers.include_router(product_router, prefix="/products", tags=["Products"])
