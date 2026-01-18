import json
from json import dumps, loads
from typing import Any, List
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.datastructures import FormData

from starlette_admin import action, I18nConfig
from starlette_admin.fields import (ImageField as BaseImageField, BaseField, StringField, EnumField, IntegerField,
                                    BooleanField, TextAreaField, NumberField, RelationField, HasOne, HasMany)
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.exceptions import ActionFailed
from starlette_admin._types import RequestAction
from starlette_admin.auth import AdminUser, AuthProvider, AdminConfig, AuthMiddleware
from starlette_admin.i18n import SUPPORTED_LOCALES
from starlette_admin.exceptions import FormValidationError, LoginFailed
import secrets

from app.core.services.image_service import ImageService
from app.infrastructure.config.config import APP_CONFIG
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
from app.infrastructure.logging.logger import get_logger

from app.utils.enums import CharacteristicTypeEnum

Session = sessionmaker(bind=sync_engine)

logger = get_logger(__name__)

imgservice = ImageService()


def get_product_form():
    return f"""
            <form>
                <div class="mt-3">
                    <label>Категория</label>
                    <select name="category_id" class="form-control">
                        {"".join(f"""<option value="{cat.id}">{cat.name}</option>""" 
                                 for cat in Session().query(Category).order_by(Category.name).all())}
                    </select>
                </div>
            </form>
        """


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
        image_url = f"{APP_CONFIG.STATIC_URL}/images/{value}"
        
        return {
            "url": image_url,
            "filename": str(value)
        }


@dataclass
class ProductImagesListField(BaseImageField):
    """Кастомное поле для отображения списка изображений продукта"""
    
    multiple: bool = True  # Явно устанавливаем multiple как атрибут класса
    
    def __init__(self, name: str, label: str | None = None):
        super().__init__(name, multiple=True)  # Включаем поддержку множественных файлов
        self.multiple = True  # Гарантируем что multiple установлен
        if label:
            self.label = label
    
    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> list[dict]:
        # ВСЕГДА возвращаем список, даже если пустой
        if not value:
            return []
        
        images = []
        for img in value:
            if hasattr(img, 'image_path') and img.image_path:
                image_url = f"{APP_CONFIG.STATIC_URL}/images/{img.image_path}"
                # Извлекаем только имя файла без пути для отображения
                filename = img.image_path.split('/')[-1] if '/' in img.image_path else img.image_path
                images.append({
                    "url": image_url,
                    "filename": filename,
                    "content-type": "image/webp"
                })
        
        return images
    
    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> tuple[Any, bool]:
        """Получаем существующие изображения, обрабатываем удаление и добавляем новые"""
        from app.infrastructure.database.models.product import ProductImage, Product
        
        # Проверяем, нажата ли кнопка удаления всех изображений
        should_delete_all = form_data.get(f"_{self.name}-delete") == "on"
        if should_delete_all:
            print("✓ Запрошено удаление всех изображений")
            product_id = request.path_params.get('pk')
            db_session = getattr(request.state, 'session', None)
            
            if product_id and action == RequestAction.EDIT and db_session:
                try:
                    product = db_session.get(Product, product_id)
                    if product and product.images:
                        # Удаляем физические файлы и записи из БД
                        images_to_delete = list(product.images)
                        for img in images_to_delete:
                            if img.image_path:
                                try:
                                    await imgservice.delete_image(img.image_path)
                                    print(f"✓ Удален файл: {img.image_path}")
                                except Exception as e:
                                    print(f"✗ Ошибка удаления файла {img.image_path}: {e}")
                            
                            # Удаляем запись из БД вручную
                            db_session.delete(img)
                        
                        # Очищаем коллекцию, чтобы SQLAlchemy не ругался
                        product.images.clear()
                        
                        db_session.flush()  # Применяем изменения в рамках транзакции
                        print(f"✓ Удалено {len(images_to_delete)} изображений из БД")
                except Exception as e:
                    print(f"✗ Ошибка при удалении изображений: {e}")
            
            # Возвращаем пустой список
            return ([], False)
        
        # Получаем product_id из URL
        product_id = request.path_params.get('pk')
        
        # Получаем сессию starlette-admin из request.state
        db_session = getattr(request.state, 'session', None)
        
        existing_images = []
        max_order = -1
        
        # Загружаем существующие изображения из ТЕКУЩЕЙ сессии starlette-admin
        if product_id and action == RequestAction.EDIT and db_session:
            try:
                # Используем ту же сессию, что и starlette-admin
                product = db_session.get(Product, product_id)
                if product and product.images:
                    # Получаем существующие изображения из ЭТОЙ же сессии
                    existing_images = list(product.images)
                    max_order = max([img.order for img in existing_images], default=-1)
                    print(f"✓ Найдено существующих изображений: {len(existing_images)}, max_order: {max_order}")
            except Exception as e:
                print(f"✗ Ошибка получения существующих изображений: {e}")
        
        # Получаем загруженные файлы
        files = form_data.getlist(self.name)
        
        # Если нет новых файлов, возвращаем существующие (или пустой список)
        if not files or not any(hasattr(f, 'filename') and f.filename for f in files):
            return (existing_images if existing_images else [], False)
        
        # Создаём новые ProductImage объекты и добавляем к существующим
        order = max_order + 1
        
        for file in files:
            if hasattr(file, 'filename') and file.filename:
                try:
                    image_path = await imgservice.upload_and_convert(file, subfolder="products")
                    
                    product_image = ProductImage(
                        image_path=image_path,
                        order=order
                    )
                    existing_images.append(product_image)
                    order += 1
                    
                    print(f"✓ Изображение загружено: {image_path}, order: {product_image.order}")
                except Exception as e:
                    print(f"✗ Ошибка загрузки изображения: {e}")
        
        # Возвращаем ВСЕ изображения: старые + новые
        print(f"✓ Возвращаем всего изображений: {len(existing_images)}")
        return (existing_images, False)


# -----------------------------------------------------------
# CATEGORY
# -----------------------------------------------------------
class CategoryAdmin(ModelView):
    label = "Категория"
    label_plural = "Категории"

    exclude_fields_from_create = ["products_count", "image"]
    exclude_fields_from_edit = ["products_count", "image"]

    fields = [
        StringField("name", label="Название"),
        StringField("slug", label="URL-адрес"),
        TextAreaField("description", label="Описание"),
        StaticImageField("image", label="Изображение"),
        NumberField("products_count", label="Количество товаров"),
        HasMany("products", identity="products", label="Товары", required=True)
    ]
    
    actions = ["discount_category", "remove_discount_categories", "upload_category_image"]

    @action(
        name="discount_category",
        text="Сделать скидку на выбранные категории",
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
        except Exception as e:
            raise ActionFailed(str(e))

        try:
            result = session.query(Product).filter(Product.category_id.in_(pks)).all()
            logger.info(f"Result: {result}")
            logger.info(f"Selected pks: {pks}")
            for product in result:
                product.discount_percent = discount
                logger.info(f"Discount add: {product.discount_percent}")
            session.commit()
            return f"Скидка {discount}% применена у выбранных категорий"
        except Exception as e:
            session.rollback()
            raise ActionFailed(str(e))

    @action(
        name="remove_discount_categories",
        text="Убрать скидку на выбранные категории"
    )
    async def remove_discount_categories(self, request: Request, pks: List[Any]) -> str:
        try:
            session = Session()
        except Exception as e:
            raise ActionFailed(str(e))

        try:
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
            session.rollback()
            raise ActionFailed(str(e))

    @action(
        name="upload_category_image",
        text="Загрузить изображение",
        confirmation="Выберите изображение для категории",
        submit_btn_text="Загрузить",
        submit_btn_class="btn-primary",
        form="""
        <form enctype="multipart/form-data">
            <div class="mt-3">
                <label>Изображение</label>
                <input type="file"
                       class="form-control"
                       name="image"
                       accept="image/*">
            </div>
        </form>
        """
    )
    async def upload_category_image(self, request: Request, pks: List[Any]) -> str:
        form = await request.form()
        upload_file = form.get("image")

        if not upload_file or upload_file.filename == "":
            raise ActionFailed("Файл не выбран.")

        if len(pks) != 1:
            raise ActionFailed("Можно загружать изображение только для одной категории.")

        category_id = pks[0]

        try:
            session = Session()
        except Exception as e:
            raise ActionFailed(str(e))

        try:
            category = session.query(Category).filter(Category.id == category_id).first()

            if not category:
                raise ActionFailed("Категория не найдена.")

            image_path = await imgservice.upload_and_convert(
                upload_file
            )

            category.image = image_path
            session.commit()

            return "Изображение успешно загружено!"
        except Exception as e:
            session.rollback()
            raise ActionFailed(str(e))


# -----------------------------------------------------------
# PRODUCT
# -----------------------------------------------------------
class ProductAdmin(ModelView):
    label = "Товар"
    label_plural = "Товары"

    exclude_fields_from_create = ["id", "reviews"]
    exclude_fields_from_edit = ["id", "reviews"]
    exclude_fields_from_list = ["description", "images", "characteristics", "reviews"]

    fields = [
        StringField("name", label="Название"),
        StringField("slug", label="URL-адрес"),
        TextAreaField("description", label="Описание"),
        NumberField("price", label="Цена"),
        NumberField("discount_percent", label="Скидка (%)"),
        BooleanField("is_active", label="Активен"),
        BooleanField("is_featured", label="Рекомендуемый"),
        HasOne("category", label="Категория", identity="category"),
        ProductImagesListField("images", label="Изображения (можно выбрать несколько)"),
        HasMany("characteristics", identity="product-characteristic", label="Характеристики")
    ]

    searchable_fields = [Product.name, Product.slug]
    sortable_fields = [Product.name, Product.price, Product.discount_percent, Product.is_active, Product.is_featured]

    actions = ["discount_products", "remove_discount_products", "move_to_category", "activate_products",
               "deactivate_products"]

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
        except Exception as e:
            raise ActionFailed(str(e))

        try:
            result = session.query(Product).filter(Product.id.in_(pks)).all()
            logger.info(f"Result: {result}")
            logger.info(f"Selected pks: {pks}")
            for product in result:
                product.discount_percent = discount
                logger.info(f"Discount add: {product.discount_percent}")
            session.commit()
            return f"Скидка {discount}% применена у выбранных товаров"
        except Exception as e:
            session.rollback()
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

    @action(
        name="move_to_category",
        text="Перенести в категорию",
        confirmation="Выберите категорию, в которую перенести товары",
        submit_btn_text="Перенести",
        submit_btn_class="btn-warning",
        form=lambda: get_product_form()
    )
    async def move_to_category(self, request: Request, pks: List[Any]) -> str:
        form: FormData = await request.form()
        category_id = form.get('category_id')

        if not category_id:
            raise ActionFailed("Категория не выбрана.")

        logger.info(f"Категория: {category_id}")

        try:
            session = Session()
        except Exception as e:
            raise ActionFailed(str(e))

        try:
            products = session.query(Product).filter(Product.id.in_(pks)).all()
            for product in products:
                product.category_id = category_id
            category_name = session.query(Category).where(Category.id == category_id).first()
            session.commit()

            return f"Товары перенесены в категорию {category_name.name}"

        except Exception as e:
            session.rollback()
            raise ActionFailed(str(e))

    @action(
        name="activate_products",
        text="Активировать товары",
        confirmation="Активировать выбранные товары?",
        submit_btn_text="Активировать",
        submit_btn_class="btn-success",
    )
    async def activate_products(self, request: Request, pks: list[int]) -> str:
        try:
            session = Session()
        except Exception as e:
            raise ActionFailed(str(e))

        try:
            products = session.query(Product).filter(Product.id.in_(pks)).all()
            for product in products:
                product.is_active = True
            session.commit()

            return "Выбранные товары успешно активированы."
        except Exception as e:
            session.rollback()
            raise ActionFailed(str(e))

    @action(
        name="deactivate_products",
        text="Деактивировать товары",
        confirmation="Отключить выбранные товары?",
        submit_btn_text="Отключить",
        submit_btn_class="btn-danger",
    )
    async def deactivate_products(self, request: Request, pks: list[int]) -> str:
        try:
            session = Session()
        except Exception as e:
            raise ActionFailed(str(e))

        try:
            products = session.query(Product).filter(Product.id.in_(pks)).all()
            for product in products:
                product.is_active = False
                logger.info(f"Активность: {product.is_active}")
            session.commit()

            return "Выбранные товары успешно деактивированы."
        except Exception as e:
            session.rollback()
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
        TextAreaField("message", label="Сообщение"),
        BooleanField("is_processed", label="Обработано")
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
        BooleanField("is_active", label="Активен")
    ]


# -----------------------------------------------------------
# PRODUCT IMAGE
# -----------------------------------------------------------
class ProductImageAdmin(ModelView):
    label = "Изображение товара"
    label_plural = "Изображения товаров"
    
    fields = [
        StringField("id", label="ID"),
        HasOne("product", label="Товар", identity="products"),
        StaticImageField("image_path", label="Изображение"),  # Используем кастомное поле для изображений
        NumberField("order", label="Порядок")
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
        HasOne("product", label="Товар", identity="products"),
        HasOne("characteristic_type", label="Тип характеристики", identity="characteristic-type")
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
        TextAreaField("content", label="Содержание"),
        NumberField("rating", label="Рейтинг"),
        StaticImageField("image", label="Изображение"),  # Используем кастомное поле для изображений
        BooleanField("is_active", label="Активен"),
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
# AUTH PROVIDER
# -----------------------------------------------------------
class MyAuthProvider(AuthProvider):
    """
    Простой провайдер авторизации для админ-панели.
    Использует логин/пароль из переменных окружения или значения по умолчанию.
    """
    
    def setup_admin(self, admin) -> None:
        """Настройка админ-панели - добавляем middleware и роуты для login/logout"""
        # Добавляем middleware для авторизации
        admin.middlewares.append(self.get_middleware(admin=admin))
        
        # Добавляем роуты для login и logout
        login_route = self.get_login_route(admin=admin)
        logout_route = self.get_logout_route(admin=admin)
        
        # Устанавливаем имена роутов
        login_route.name = "login"
        logout_route.name = "logout"
        
        # Добавляем роуты в админку
        admin.routes.extend([login_route, logout_route])
    
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        """Проверка логина и пароля"""
        # Получаем логин/пароль из конфига
        admin_username = APP_CONFIG.ADMIN_USERNAME
        admin_password = APP_CONFIG.ADMIN_PASSWORD
        
        if username == admin_username and password == admin_password:
            # Генерируем токен сессии
            token = secrets.token_urlsafe(32)
            request.session.update({"token": token, "username": username})
            return response
        
        raise LoginFailed("Неверный логин или пароль")
    
    async def is_authenticated(self, request: Request) -> bool:
        """Проверка авторизован ли пользователь"""
        token = request.session.get("token")
        return token is not None
    
    def get_admin_user(self, request: Request) -> AdminUser | None:
        """Получить текущего пользователя"""
        username = request.session.get("username")
        if not username:
            return None
        
        return AdminUser(username=username)
    
    async def logout(self, request: Request, response: Response) -> Response:
        """Выход из системы"""
        request.session.clear()
        return response


# -----------------------------------------------------------
# INIT
# -----------------------------------------------------------
def create_admin(engine):
    """
    Создание админки для FastAPI.
    Версия старлет-админ < 0.18 → синтаксис старый.
    """
    default_locale = "ru" if "ru" in SUPPORTED_LOCALES else "en"
    i18n_config = I18nConfig(
        default_locale=default_locale,
        language_switcher=[default_locale],
    )

    # Создаем провайдер авторизации
    auth_provider = MyAuthProvider()
    
    admin = Admin(
        engine,
        title="Админ-панель 4Roads",
        base_url="/admin",
        route_name="admin",
        i18n_config=i18n_config,
        auth_provider=auth_provider,
        middlewares=[],  # Middleware будет добавлен через mount_to
        debug=True,
    )

    admin.add_view(CategoryAdmin(Category, identity="category"))
    admin.add_view(ContactFormAdmin(ContactForm))
    admin.add_view(FAQAdmin(FAQ))
    admin.add_view(ProductAdmin(Product, identity="products"))
    admin.add_view(ProductImageAdmin(ProductImage))
    admin.add_view(CharacteristicTypeAdmin(CharacteristicType))
    admin.add_view(ProductCharacteristicAdmin(ProductCharacteristic))
    admin.add_view(ReviewAdmin(Review))
    admin.add_view(SettingsAdmin(Settings))

    return admin
