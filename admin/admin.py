import logging

from typing import Any, List

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.datastructures import FormData

from starlette_admin import action
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.exceptions import ActionFailed

from app.infrastructure.database.models.category import Category
from app.infrastructure.database.models.contact_form import ContactForm
from app.infrastructure.database.models.faq import FAQ
from app.infrastructure.database.models.product import (
    Product,
    ProductImage,
    CharacteristicType,
    ProductCharacteristic,
)
from app.infrastructure.database.models.review import Review
from app.infrastructure.database.models.settings import Settings
from app.infrastructure.database.adapters.sync_connection import sync_engine

Session = sessionmaker(bind=sync_engine)

logger = logging.getLogger("myadmin")
logger.setLevel(logging.INFO)


# -----------------------------------------------------------
# CATEGORY
# -----------------------------------------------------------
class CategoryAdmin(ModelView):
    label = "Категория"
    label_plural = "Категории"

    actions = ["discount_custom"]

    @action(
        name="discount_custom",
        text="Сделать индивидуальную скидку",
        confirmation="Укажите размер скидки в процентах",
        submit_btn_text="Применить",
        submit_btn_class="btn-primary",
        form="""
            <form>
                <div class="mt-3">
                    <label>Размер скидки (%)</label>
                    <input type="number" min="1" max="90" step="1"
                           class="form-control"
                           name="discount"
                           placeholder="Например: 15">
                </div>
            </form>
            """
    )
    async def discount_custom(self, request: Request, pks: List[Any]) -> str:
        form: FormData = await request.form()
        discount_str = form.get("discount")
        if not discount_str:
            raise ActionFailed("Не указан процент скидки.")
        try:
            discount = int(discount_str)
        except ValueError:
            raise ActionFailed("Процент должен быть целым числом.")

        if discount < 1 or discount > 99:
            raise ActionFailed("Процент должен быть от 1 до 99.")

        try:
            session = Session()
            result = session.query(Product).filter(Product.category_id.in_(pks)).all()
            logger.info(f"Result: {result}")
            logger.info(f"Selected pks: {pks}")
            for product in result:
                product.old_price = product.price
                product.price = round(product.price * (100 - discount) / 100, 2)
                logger.info(f"Old price: {product.old_price} New price: {product.price}")
            session.commit()
            return f"Цена снижена на {discount}% у выбранных категорий"
        except Exception as e:
            return str(e)


# -----------------------------------------------------------
# PRODUCT
# -----------------------------------------------------------
class ProductAdmin(ModelView):
    label = "Товар"
    label_plural = "Товары"

    actions = ["discount"]

    @action(
        name="discount",
        text="Сделать скидку выбранным товарам",
        confirmation="Применить скидку 10% выбранным товарам?",
        submit_btn_text="Да",
        submit_btn_class="btn-primary",
    )
    async def discount_action(self, request: Request, pks: List[Any]) -> str:
        async with self.session_maker() as session:
            for product_id in pks:
                result = await session.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = result.scalar_one_or_none()

                if not product:
                    continue

                if getattr(product, "is_discount_exempt", False):
                    continue

                product.old_price = product.price
                product.price = round(product.price * 0.9, 2)

            await session.commit()

        return "Скидка успешно применена!"


# -----------------------------------------------------------
# CONTACT FORM
# -----------------------------------------------------------
class ContactFormAdmin(ModelView):
    label = "Контакт"
    label_plural = "Контакты"


# -----------------------------------------------------------
# FAQ
# -----------------------------------------------------------
class FAQAdmin(ModelView):
    label = "FAQ"
    label_plural = "Частые вопросы"


# -----------------------------------------------------------
# PRODUCT IMAGE
# -----------------------------------------------------------
class ProductImageAdmin(ModelView):
    label = "Изображение товара"
    label_plural = "Изображения товаров"


# -----------------------------------------------------------
# CHARACTERISTIC TYPE
# -----------------------------------------------------------
class CharacteristicTypeAdmin(ModelView):
    label = "Тип характеристики"
    label_plural = "Типы характеристик"


# -----------------------------------------------------------
# PRODUCT CHARACTERISTIC
# -----------------------------------------------------------
class ProductCharacteristicAdmin(ModelView):
    label = "Характеристика товара"
    label_plural = "Характеристики товаров"


# -----------------------------------------------------------
# REVIEW
# -----------------------------------------------------------
class ReviewAdmin(ModelView):
    label = "Отзыв"
    label_plural = "Отзывы"


# -----------------------------------------------------------
# SETTINGS
# -----------------------------------------------------------
class SettingsAdmin(ModelView):
    label = "Настройки"
    label_plural = "Настройки"


# -----------------------------------------------------------
# INIT
# -----------------------------------------------------------
def create_admin(engine):
    """
    Создание админки для FastAPI.
    Версия старлет-админ < 0.18 → синтаксис старый.
    """
    admin = Admin(
        engine,
        title="Админ-панель",
    )

    admin.add_view(CategoryAdmin(Category))
    admin.add_view(ContactFormAdmin(ContactForm))
    admin.add_view(FAQAdmin(FAQ))
    admin.add_view(ProductAdmin(Product))
    admin.add_view(ProductImageAdmin(ProductImage))
    admin.add_view(CharacteristicTypeAdmin(CharacteristicType))
    admin.add_view(ProductCharacteristicAdmin(ProductCharacteristic))
    admin.add_view(ReviewAdmin(Review))
    admin.add_view(SettingsAdmin(Settings))

    return admin
