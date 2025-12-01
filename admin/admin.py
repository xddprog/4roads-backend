from typing import Any, List
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.datastructures import FormData

from starlette_admin import action
from starlette_admin.fields import ImageField as BaseImageField, BaseField, StringField, EnumField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.exceptions import ActionFailed
from starlette_admin._types import RequestAction

from app.infrastructure.database.models.category import Category
from app.infrastructure.config.config import APP_CONFIG
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

from app.infrastructure.logging.logger import get_logger

from app.utils.enums import CharacteristicTypeEnum

Session = sessionmaker(bind=sync_engine)

logger = get_logger(__name__)


# -----------------------------------------------------------
# CUSTOM FIELDS
# -----------------------------------------------------------
@dataclass
class StaticImageField(BaseImageField):
    """Кастомное поле для отображения изображений из статической директории"""
    
    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> dict | None:
        """Сериализует путь к изображению в формат, понятный starlette-admin"""
        if not value:
            return None
        
        # Формируем полный URL к изображению
        image_url = f"{APP_CONFIG.STATIC_URL}/{value}"
        
        return {
            "url": image_url,
            "filename": str(value)
        }


@dataclass
class ProductImagesListField(BaseImageField):
    """Кастомное поле для отображения списка изображений продукта"""
    
    def __init__(self, name: str, label: str | None = None):
        super().__init__(name)
        if label:
            self.label = label
    
    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> list[dict] | None:
        if not value:
            return None
        
        images = []
        for img in value:
            if hasattr(img, 'image_path') and img.image_path:
                image_url = f"{APP_CONFIG.STATIC_URL}/{img.image_path}"
                images.append({
                    "url": image_url,
                    "filename": str(img.image_path)
                })
        
        return images[0] if images else None


@dataclass
class CategoryNameField(BaseField):
    """Кастомное поле для отображения названия категории вместо UUID"""
    
    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> str | None:
        """Возвращает название категории"""
        if not value:
            return None
        
        # value - это объект Category
        if hasattr(value, 'name'):
            return value.name
        
        return None


# -----------------------------------------------------------
# CATEGORY
# -----------------------------------------------------------
class CategoryAdmin(ModelView):
    label = "Категория"
    label_plural = "Категории"

    fields = [
        StringField("id", label="ID"),
        StringField("name", label="Название"),
        StringField("slug", label="URL-адрес"),
        StringField("description", label="Описание"),
        StaticImageField("image", label="Изображение"),
        StringField("products_count", label="Количество товаров")
    ]
    
    actions = ["discount_category", "remove_discount_categories"]

    @action(
        name="discount_category",
        text="Сделать индивидуальную скидку",
        confirmation="Укажите размер скидки в процентах",
        submit_btn_text="Применить",
        submit_btn_class="btn-primary",
        form="""
            <form>
                <div class="mt-3">
                    <label>Размер скидки (%)</label>
                    <input type="number" min="1" max="99" step="1"
                           class="form-control"
                           name="discount"
                           placeholder="Например: 15">
                </div>
            </form>
            """
    )
    async def discount_category(self, request: Request, pks: List[Any]) -> str:
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
                product.discount_percent = discount
                logger.info(f"Discount add: {product.discount_percent}")
            session.commit()
            return f"Скидка {discount}% применена у выбранных категорий"
        except Exception as e:
            raise ActionFailed(str(e))

    @action(
        name="remove_discount_categories",
        text="Убрать скидку на выбранные категории"
    )
    async def remove_discount_categories(self, request: Request, pks: List[Any]) -> str:
        try:
            session = Session()
            result = session.query(Product).filter(Product.category_id.in_(pks)).all()
            logger.info(f"Result: {result}")
            logger.info(f"Selected pks: {pks}")
            for product in result:
                old_discount = product.discount_percent
                product.discount_percent = None
                logger.info(f"Removed discount: {old_discount}")
            session.commit()
            return f"Скидка у выбранных категорий удалена"
        except Exception as e:
            raise ActionFailed(str(e))


# -----------------------------------------------------------
# PRODUCT
# -----------------------------------------------------------
class ProductAdmin(ModelView):
    label = "Товар"
    label_plural = "Товары"
    
    exclude_fields_from_list = ["characteristics", "reviews"]
    exclude_fields_from_create = ["images", "characteristics", "reviews"]
    exclude_fields_from_edit = ["images", "characteristics", "reviews"]
    
    fields = [
        StringField("id", label="ID"),
        StringField("name", label="Название"),
        StringField("slug", label="URL-адрес"),
        StringField("description", label="Описание"),
        StringField("price", label="Цена"),
        StringField("discount_percent", label="Скидка (%)"),
        StringField("is_active", label="Активен"),
        StringField("is_featured", label="Рекомендуемый"),
        CategoryNameField("category", label="Категория"),  # Показываем название категории вместо UUID
        ProductImagesListField("images", label="Изображения"),  # Показываем список изображений
        StringField("characteristics", label="Характеристики"),
    ]

    actions = ["discount_products", "remove_discount_products"]

    @action(
        name="discount_products",
        text="Сделать скидку на выбранные товары",
        confirmation="Укажите размер скидки в процентах",
        submit_btn_text="Применить",
        submit_btn_class="btn-primary",
        form="""
                <form>
                    <div class="mt-3">
                        <label>Размер скидки (%)</label>
                        <input type="number" min="1" max="99" step="1"
                               class="form-control"
                               name="discount"
                               placeholder="Например: 15">
                    </div>
                </form>
                """
    )
    async def discount_products(self, request: Request, pks: List[Any]) -> str:
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
            result = session.query(Product).filter(Product.id.in_(pks)).all()
            logger.info(f"Result: {result}")
            logger.info(f"Selected pks: {pks}")
            for product in result:
                product.discount_percent = discount
                logger.info(f"Discount add: {product.discount_percent}")
            session.commit()
            return f"Скидка {discount}% применена у выбранных товаров"
        except Exception as e:
            raise ActionFailed(str(e))

    @action(
        name="remove_discount_products",
        text="Убрать скидку на выбранные товары"
    )
    async def remove_discount_products(self, request: Request, pks: List[Any]) -> str:
        try:
            session = Session()
            result = session.query(Product).filter(Product.id.in_(pks)).all()
            logger.info(f"Result: {result}")
            logger.info(f"Selected pks: {pks}")
            for product in result:
                old_discount = product.discount_percent
                product.discount_percent = None
                logger.info(f"Removed discount: {old_discount}")
            session.commit()
            return f"Скидка у выбранных товаров удалена"
        except Exception as e:
            raise ActionFailed(str(e))


# -----------------------------------------------------------
# CONTACT FORM
# -----------------------------------------------------------
class ContactFormAdmin(ModelView):
    label = "Контакт"
    label_plural = "Контакты"
    
    fields = [
        StringField("id", label="ID"),
        StringField("name", label="Имя"),
        StringField("phone", label="Телефон"),
        StringField("message", label="Сообщение"),
        StringField("is_processed", label="Обработано")
    ]


# -----------------------------------------------------------
# FAQ
# -----------------------------------------------------------
class FAQAdmin(ModelView):
    label = "FAQ"
    label_plural = "Частые вопросы"
    
    fields = [
        StringField("id", label="ID"),
        StringField("question", label="Вопрос"),
        StringField("answer", label="Ответ"),
        StringField("is_active", label="Активен")
    ]


# -----------------------------------------------------------
# PRODUCT IMAGE
# -----------------------------------------------------------
class ProductImageAdmin(ModelView):
    label = "Изображение товара"
    label_plural = "Изображения товаров"
    
    fields = [
        StringField("id", label="ID"),
        StringField("product", label="Товар"),
        StaticImageField("image_path", label="Изображение"),  # Используем кастомное поле для изображений
        StringField("order", label="Порядок")
    ]


# -----------------------------------------------------------
# CHARACTERISTIC TYPE
# -----------------------------------------------------------
class CharacteristicTypeAdmin(ModelView):
    label = "Тип характеристики"
    label_plural = "Типы характеристик"
    
    
    fields = [
        StringField("id", label="ID"),
        EnumField("name", label="Название", choices=[(i, i.value) for i in CharacteristicTypeEnum]),
        StringField("slug", label="URL-адрес")
    ]

    actions = []
    
    def is_accessible(self, request: Request) -> bool:
        route = request.url.path.split("/")[-1]
        if route == "create":
            return False
        if route == "edit":
            return False
        if route == "delete":
            return False
        return True

# -----------------------------------------------------------
# PRODUCT CHARACTERISTIC
# -----------------------------------------------------------
class ProductCharacteristicAdmin(ModelView):
    label = "Характеристика товара"
    label_plural = "Характеристики товаров"
    
    fields = [
        StringField("id", label="ID"),
        StringField("value", label="Значение"),
        StringField("product", label="Товар"),
        StringField("characteristic_type", label="Тип характеристики")
    ]


# -----------------------------------------------------------
# REVIEW
# -----------------------------------------------------------
class ReviewAdmin(ModelView):
    label = "Отзыв"
    label_plural = "Отзывы"
    
    fields = [
        StringField("id", label="ID"),
        StringField("author_name", label="Имя автора"),
        StringField("content", label="Содержание"),
        StringField("rating", label="Рейтинг"),
        StaticImageField("image", label="Изображение"),  # Используем кастомное поле для изображений
        StringField("is_active", label="Активен"),
        StringField("product", label="Товар")
    ]


# -----------------------------------------------------------
# SETTINGS
# -----------------------------------------------------------
class SettingsAdmin(ModelView):
    label = "Настройки"
    label_plural = "Настройки"
    
    fields = [
        StringField("id", label="ID"),
        StringField("phone", label="Телефон"),
        StringField("email", label="Email"),
        StringField("address", label="Адрес"),
        StringField("vk_url", label="VK URL"),
        StringField("telegram_url", label="Telegram URL"),
        StringField("whatsapp_url", label="WhatsApp URL"),
        StringField("youtube_url", label="YouTube URL"),
        StringField("about_text", label="О нас"),
        StringField("work_hours", label="Время работы")
    ]


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
