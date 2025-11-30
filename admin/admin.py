from sqladmin import ModelView, action
from fastapi import Request
from typing import List

from sqlalchemy.future import select

from app.infrastructure.database.models.category import Category
from app.infrastructure.database.models.contact_form import ContactForm
from app.infrastructure.database.models.faq import FAQ
from app.infrastructure.database.models.product import (
    Product, ProductImage, CharacteristicType, ProductCharacteristic
)
from app.infrastructure.database.models.review import Review
from app.infrastructure.database.models.settings import Settings


# ---------------- CATEGORY ----------------
class CategoryAdmin(ModelView, model=Category):
    column_list = [
        Category.id,
        Category.created_at,
        Category.updated_at,
        Category.name,
        Category.slug,
        Category.description,
        Category.image,
        Category.order,
        Category.products,
    ]

    form_include_relationships = True

    form_columns = [
        Category.name,
        Category.slug,
        Category.description,
        Category.image,
        Category.order,
    ]

    name = "Категория"
    name_plural = "Категории"

    @action(
        name="discount"
    )
    async def bulk_discount_by_category(self, request: Request):
        """
        Применяем скидку discount_percent ко всем товарам категории,
        кроме товаров с is_discount_exempt=True
        """
        form = request
        print(form)
        # result = await self.session.execute(select(Product).where(Product.category_id == category_id))
        # products = result.scalars().all()
        # for product in products:
        #     if product.is_discount_exempt:
        #         continue
        #     product.old_price = product.price
        #     product.price = round(product.price * (1 - discount_percent / 100), 2)
        # await self.session.commit()


# ---------------- CONTACT FORM ----------------
class ContactFormAdmin(ModelView, model=ContactForm):
    column_list = [
        ContactForm.id,
        ContactForm.created_at,
        ContactForm.updated_at,
        ContactForm.name,
        ContactForm.phone,
        ContactForm.message,
        ContactForm.is_processed,
    ]

    form_columns = [
        ContactForm.name,
        ContactForm.phone,
        ContactForm.message,
        ContactForm.is_processed,
    ]

    name = "Контакт"
    name_plural = "Контакты"


# ---------------- FAQ ----------------
class FAQAdmin(ModelView, model=FAQ):
    column_list = [
        FAQ.id,
        FAQ.created_at,
        FAQ.updated_at,
        FAQ.question,
        FAQ.answer,
        FAQ.is_active,
    ]

    form_columns = [
        FAQ.question,
        FAQ.answer,
        FAQ.is_active,
    ]

    name = "Часто задаваемый вопрос"
    name_plural = "Часто задаваемые вопросы"


# ---------------- PRODUCT ----------------
class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id,
        Product.created_at,
        Product.updated_at,
        Product.name,
        Product.slug,
        Product.description,
        Product.price,
        Product.old_price,
        Product.is_active,
        Product.is_featured,
        Product.category_id,
        Product.category,
        Product.images,
        Product.characteristics,
        Product.reviews,
    ]

    form_include_relationships = True

    form_columns = [
        Product.name,
        Product.slug,
        Product.description,
        Product.price,
        Product.old_price,
        Product.is_active,
        Product.is_featured,
        Product.category_id,
    ]

    name = "Товар"
    name_plural = "Товары"

    async def bulk_apply_discount(self, request: Request, objs: List[Product], discount_percent: float = 10):
        """
        Применяем скидку discount_percent ко всем выбранным товарам,
        кроме тех, у которых is_discount_exempt=True
        """
        for product in objs:
            if product.is_discount_exempt:
                continue
            product.old_price = product.price
            product.price = round(product.price * (1 - discount_percent / 100), 2)
        await self.session.commit()

    action_list = ["bulk_apply_discount"]


# ---------------- PRODUCT IMAGE ----------------
class ProductImageAdmin(ModelView, model=ProductImage):
    column_list = [
        ProductImage.id,
        ProductImage.created_at,
        ProductImage.updated_at,
        ProductImage.image_path,
        ProductImage.order,
        ProductImage.product_id,
        ProductImage.product,
    ]

    form_include_relationships = True

    form_columns = [
        ProductImage.image_path,
        ProductImage.order,
        ProductImage.product_id,
    ]

    name = "Изображение товара"
    name_plural = "Изображения товаров"


# ---------------- CHARACTERISTIC TYPE ----------------
class CharacteristicTypeAdmin(ModelView, model=CharacteristicType):
    column_list = [
        CharacteristicType.id,
        CharacteristicType.created_at,
        CharacteristicType.updated_at,
        CharacteristicType.name,
        CharacteristicType.slug,
        CharacteristicType.characteristics,
    ]

    form_include_relationships = True

    form_columns = [
        CharacteristicType.name,
        CharacteristicType.slug,
    ]

    name = "Название характеристики"
    name_plural = "Названия характеристик"


# ---------------- PRODUCT CHARACTERISTIC ----------------
class ProductCharacteristicAdmin(ModelView, model=ProductCharacteristic):
    column_list = [
        ProductCharacteristic.id,
        ProductCharacteristic.created_at,
        ProductCharacteristic.updated_at,
        ProductCharacteristic.value,
        ProductCharacteristic.product_id,
        ProductCharacteristic.characteristic_type_id,
        ProductCharacteristic.product,
        ProductCharacteristic.characteristic_type,
    ]

    form_include_relationships = True

    form_columns = [
        ProductCharacteristic.value,
        ProductCharacteristic.product_id,
        ProductCharacteristic.characteristic_type_id,
    ]

    name = "Значение характеристики"
    name_plural = "Значения характеристик"


# ---------------- REVIEW ----------------
class ReviewAdmin(ModelView, model=Review):
    column_list = [
        Review.id,
        Review.created_at,
        Review.updated_at,
        Review.author_name,
        Review.content,
        Review.rating,
        Review.image,
        Review.is_active,
        Review.product_id,
        Review.product,
    ]

    form_include_relationships = True

    form_columns = [
        Review.author_name,
        Review.content,
        Review.rating,
        Review.image,
        Review.is_active,
        Review.product_id,
    ]

    name = "Отзыв"
    name_plural = "Отзывы"


# ---------------- SETTINGS ----------------
class SettingsAdmin(ModelView, model=Settings):
    # Что отображается в списке
    column_list = [
        Settings.id,
        Settings.created_at,
        Settings.updated_at,
        Settings.phone,
        Settings.email,
        Settings.vk_url,
        Settings.telegram_url,
        Settings.whatsapp_url,
        Settings.youtube_url,
        Settings.about_text,
        Settings.work_hours
    ]

    # Поля, доступные для редактирования
    form_columns = [
        Settings.phone,
        Settings.email,
        Settings.vk_url,
        Settings.telegram_url,
        Settings.whatsapp_url,
        Settings.youtube_url,
        Settings.about_text,
        Settings.work_hours,
    ]

    name = "Настройки"
    name_plural = "Настройки"
