from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.settings import Settings
from app.infrastructure.database.models.category import Category
from app.infrastructure.database.models.product import (
    CharacteristicType,
    Product,
    ProductImage,
    ProductCharacteristic
)
from app.infrastructure.database.models.faq import FAQ
from app.infrastructure.database.models.review import Review
from app.utils.enums import CharacteristicTypeEnum
from app.infrastructure.logging.logger import get_logger


logger = get_logger(__name__)


async def init_settings(session: AsyncSession) -> None:
    result = await session.execute(select(Settings).where(Settings.id == 1))
    if result.scalars().first():
        logger.info("settings_already_exist")
        return
    
    settings = Settings(
        id=1,
        phone="+7 (123) 456-78-90",
        email="info@4roads.su",
        address="Москва, ул. Примерная, д. 1",
        vk_url="https://vk.com/4roads",
        telegram_url="https://t.me/4roads",
        whatsapp_url="https://wa.me/79123456789",
        youtube_url="https://youtube.com/@4roads",
        about_text="Добро пожаловать в 4roads!",
        work_hours={
            "weekdays": {"start": "09:00", "end": "18:00"},
            "weekend": {"start": "10:00", "end": "16:00"},
            "note": "Без перерыва"
        }
    )
    session.add(settings)
    logger.info("settings_created")


async def init_characteristic_types(session: AsyncSession) -> None:
    result = await session.execute(select(CharacteristicType))
    if result.scalars().first():
        logger.info("characteristic_types_already_exist")
        return
    
    characteristic_types = [
        CharacteristicType(name=CharacteristicTypeEnum.SIZE.value, slug="size"),
        CharacteristicType(name=CharacteristicTypeEnum.MATERIAL.value, slug="material"),
        CharacteristicType(name=CharacteristicTypeEnum.COLOR.value, slug="color"),
    ]
    
    session.add_all(characteristic_types)
    logger.info("characteristic_types_created", count=len(characteristic_types))


async def init_faq(session: AsyncSession) -> None:
    result = await session.execute(select(FAQ))
    if result.scalars().first():
        logger.info("faq_already_exist")
        return
    
    faqs = [
        FAQ(
            question="Как сделать заказ?",
            answer="Вы можете оставить заявку на сайте или связаться с нами по телефону.",
            is_active=True
        ),
        FAQ(
            question="Какие способы оплаты доступны?",
            answer="Мы принимаем оплату наличными, банковской картой и безналичный расчёт.",
            is_active=True
        ),
        FAQ(
            question="Как долго доставка?",
            answer="Доставка по Москве занимает 1-2 дня, по России - 3-7 дней.",
            is_active=True
        ),
    ]
    
    session.add_all(faqs)
    logger.info("faq_created", count=len(faqs))


async def init_test_products(session: AsyncSession) -> None:
    """Создание тестовых категорий и продуктов"""
    # Проверяем, есть ли уже продукты
    result = await session.execute(select(Product))
    if result.scalars().first():
        logger.info("products_already_exist")
        return
    
    # Создаем категории
    categories_data = [
        {"name": "Чемоданы", "slug": "chemodany", "description": "Пластиковые и тканевые чемоданы на колесах"},
        {"name": "Сумки", "slug": "sumki", "description": "Дорожные сумки, бьюти-кейсы, спортивные сумки"},
        {"name": "Рюкзаки", "slug": "ryukzaki", "description": "Обычные рюкзаки и рюкзаки на колесах"},
        {"name": "Кейс-пилоты", "slug": "keys-piloty", "description": "Компактные чемоданы для ручной клади"},
        {"name": "Аксессуары", "slug": "aksessuary", "description": "Чехлы для чемоданов и прочие аксессуары"},
    ]
    
    categories = {}
    for cat_data in categories_data:
        category = Category(**cat_data)
        session.add(category)
        await session.flush()
        categories[cat_data["slug"]] = category
    
    # Получаем типы характеристик
    char_types_result = await session.execute(select(CharacteristicType))
    char_types = {ct.slug: ct for ct in char_types_result.scalars().all()}
    
    # Создаем 30 продуктов
    products_data = [
        # Чемоданы (12 продуктов)
        {
            "category": "chemodany",
            "name": "Чемодан 8802 (L) Темно-синий",
            "slug": "chemodan-8802-l-temno-siniy",
            "description": "Большой пластиковый чемодан на 4 колесах. Прочный поликарбонат, телескопическая ручка",
            "price": 7220,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": True,
            "characteristics": {"size": "L", "material": "Поликарбонат", "color": "Темно-синий"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "chemodany",
            "name": "Чемодан 8802 (L) Пурпурный",
            "slug": "chemodan-8802-l-purpurnyy",
            "description": "Большой пластиковый чемодан на 4 колесах. Яркий дизайн, встроенный кодовый замок",
            "price": 7220,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": True,
            "characteristics": {"size": "L", "material": "Поликарбонат", "color": "Пурпурный"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "chemodany",
            "name": "Чемодан 8103 (L) Вишневый",
            "slug": "chemodan-8103-l-vishnevyy",
            "description": "Облегченный чемодан большого размера. Алюминиевая выдвижная ручка",
            "price": 6600,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": True,
            "characteristics": {"size": "L", "material": "ABS-пластик", "color": "Вишневый"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "chemodany",
            "name": "Чемодан 8103 (L) Серый",
            "slug": "chemodan-8103-l-seryy",
            "description": "Стильный серый чемодан на 4 колесах. Вместительный и надежный",
            "price": 6600,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"size": "L", "material": "ABS-пластик", "color": "Серый"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "chemodany",
            "name": "Чемодан 8001 (S) Коралловый",
            "slug": "chemodan-8001-s-korallovyy",
            "description": "Маленький чемодан для ручной клади. Подходит для недельных поездок",
            "price": 4200,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"size": "S", "material": "Полипропилен", "color": "Коралловый"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "chemodany",
            "name": "Чемодан Р-02 (M) Черный",
            "slug": "chemodan-p02-m-chernyy",
            "description": "Средний тканевый чемодан. Множество карманов, расширяемый объем",
            "price": 4100,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"size": "M", "material": "Полиэстер", "color": "Черный"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "chemodany",
            "name": "Чемодан Р-02 (L) Темно-синий",
            "slug": "chemodan-p02-l-temno-siniy",
            "description": "Большой тканевый чемодан на 4 колесах. Водоотталкивающая ткань",
            "price": 4740,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"size": "L", "material": "Полиэстер", "color": "Темно-синий"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "chemodany",
            "name": "Чемодан Р-02 (L) Красный",
            "slug": "chemodan-p02-l-krasnyy",
            "description": "Яркий красный чемодан из прочной ткани. Легко узнать на багажной ленте",
            "price": 4740,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"size": "L", "material": "Полиэстер", "color": "Красный"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "chemodany",
            "name": "Чемодан Р-02 (L) Голубой",
            "slug": "chemodan-p02-l-goluboy",
            "description": "Нежный голубой оттенок. Идеален для путешествий",
            "price": 4740,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"size": "L", "material": "Полиэстер", "color": "Голубой"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "chemodany",
            "name": "Чемодан Р-02 (L) Бордовый",
            "slug": "chemodan-p02-l-bordovyy",
            "description": "Элегантный бордовый чемодан. Классика для деловых поездок",
            "price": 4740,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"size": "L", "material": "Полиэстер", "color": "Бордовый"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "chemodany",
            "name": "Чемодан 5501 (M) Золотой",
            "slug": "chemodan-5501-m-zolotoy",
            "description": "Роскошный золотой чемодан среднего размера. Зеркальное покрытие",
            "price": 8500,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": True,
            "characteristics": {"size": "M", "material": "Поликарбонат", "color": "Золотой"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "chemodany",
            "name": "Чемодан 7702 (S) Розовый",
            "slug": "chemodan-7702-s-rozovyy",
            "description": "Маленький розовый чемодан для ручной клади. Идеален для коротких поездок",
            "price": 3900,
            "discount_percent": 30,
            "is_active": False,
            "is_featured": False,
            "characteristics": {"size": "S", "material": "ABS-пластик", "color": "Розовый"},
            "images": ["test_image.jpg"]
        },
        
        # Сумки (8 продуктов)
        {
            "category": "sumki",
            "name": "Дорожная сумка на колесах 65 л Черная",
            "slug": "dorozhnaya-sumka-65l-chernaya",
            "description": "Вместительная дорожная сумка на 2 колесах. Удобные ручки и плечевой ремень",
            "price": 3200,
            "discount_percent": 0   ,
            "is_active": True,
            "is_featured": True,
            "characteristics": {"material": "Полиэстер", "color": "Черный"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "sumki",
            "name": "Дорожная сумка на колесах 80 л Синяя",
            "slug": "dorozhnaya-sumka-80l-sinyaya",
            "description": "Большая дорожная сумка. Выдвижная телескопическая ручка",
            "price": 3600,
            "discount_percent": 0,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Полиэстер", "color": "Синий"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "sumki",
            "name": "Бьюти-кейс Розовый",
            "slug": "byuti-keys-rozovyy",
            "description": "Косметичка с зеркалом. Множество отделений для косметики",
            "price": 1850,
            "discount_percent": 0,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Полиэстер", "color": "Розовый"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "sumki",
            "name": "Спортивная сумка 45 л Серая",
            "slug": "sportivnaya-sumka-45l-seraya",
            "description": "Сумка для спортзала с отделением для обуви. Влагостойкий материал",
            "price": 2100,
            "discount_percent": 0,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Нейлон", "color": "Серый"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "sumki",
            "name": "Сумка для документов А4 Черная",
            "slug": "sumka-dokumenty-a4-chernaya",
            "description": "Деловая сумка для ноутбука и документов формата А4",
            "price": 2800,
            "discount_percent": 0,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Кожзам", "color": "Черный"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "sumki",
            "name": "Сумка на пояс Хаки",
            "slug": "sumka-poyas-khaki",
            "description": "Компактная поясная сумка. Несколько карманов на молнии",
            "price": 890,
            "discount_percent": 0,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Нейлон", "color": "Хаки"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "sumki",
            "name": "Молодежная сумка через плечо Синяя",
            "slug": "molodezhnaya-sumka-sinyaya",
            "description": "Стильная молодежная сумка-мессенджер",
            "price": 1650,
            "discount_percent": 0,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Полиэстер", "color": "Синий"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "sumki",
            "name": "Дорожная сумка складная 40 л",
            "slug": "sumka-skladnaya-40l",
            "description": "Складная дорожная сумка. Компактно складывается в чехол",
            "price": 1200,
            "discount_percent": 0,
            "is_active": False,
            "is_featured": False,
            "characteristics": {"material": "Нейлон", "color": "Черный"},
            "images": ["test_image.jpg"]
        },
        
        # Рюкзаки (4 продукта)
        {
            "category": "ryukzaki",
            "name": "Рюкзак на колесах 35 л Черный",
            "slug": "ryukzak-kolesa-35l-chernyy",
            "description": "Универсальный рюкзак-трансформер на колесах. Выдвижная ручка",
            "price": 4200,
            "discount_percent": 0,
            "is_active": True,
            "is_featured": True,
            "characteristics": {"material": "Полиэстер", "color": "Черный"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "ryukzaki",
            "name": "Рюкзак на колесах 45 л Синий",
            "slug": "ryukzak-kolesa-45l-siniy",
            "description": "Большой рюкзак на колесах для путешествий. Анатомическая спинка",
            "price": 4800,
            "discount_percent": 0,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Полиэстер", "color": "Синий"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "ryukzaki",
            "name": "Городской рюкзак 25 л Серый",
            "slug": "gorodskoy-ryukzak-25l-seryy",
            "description": "Компактный городской рюкзак с отделением для ноутбука 15.6",
            "price": 2600,
            "discount_percent": 10,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Полиэстер", "color": "Серый"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "ryukzaki",
            "name": "Туристический рюкзак 55 л Зеленый",
            "slug": "turisticheskiy-ryukzak-55l-zelenyy",
            "description": "Походный рюкзак с влагозащитной пропиткой. Регулируемые лямки",
            "price": 3900,
            "discount_percent": 0,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Нейлон", "color": "Зеленый"},
            "images": ["test_image.jpg"]
        },
        
        # Кейс-пилоты (4 продукта)
        {
            "category": "keys-piloty",
            "name": "Кейс-пилот на 4 колесах Черный",
            "slug": "keys-pilot-4-kolesa-chernyy",
            "description": "Компактный кейс для ручной клади. Отделение для ноутбука",
            "price": 5400,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": True,
            "characteristics": {"material": "Поликарбонат", "color": "Черный"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "keys-piloty",
            "name": "Кейс-пилот деловой Коричневый",
            "slug": "keys-pilot-delovoy-korichnevyy",
            "description": "Классический деловой кейс на 2 колесах. Кожаная отделка",
            "price": 6800,
            "discount_percent": 0,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Кожзам", "color": "Коричневый"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "keys-piloty",
            "name": "Кейс-пилот облегченный Серый",
            "slug": "keys-pilot-oblegchennyy-seryy",
            "description": "Легкий кейс из ABS-пластика. Вместительный и надежный",
            "price": 4900,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "ABS-пластик", "color": "Серый"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "keys-piloty",
            "name": "Кейс-пилот расширяемый Синий",
            "slug": "keys-pilot-rasshiryaemyy-siniy",
            "description": "Кейс с возможностью расширения объема. USB-порт для зарядки",
            "price": 7200,
            "discount_percent": 0,
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Полипропилен", "color": "Синий"},
            "images": ["test_image.jpg"]
        },
        
        # Аксессуары (2 продукта)
        {
            "category": "aksessuary",
            "name": "Чехол для чемодана размер L",
            "slug": "chekhol-chemodan-razmer-l",
            "description": "Защитный чехол из эластичной ткани. Защита от царапин и грязи",
            "price": 890,
            "discount_percent": 30,
            "is_active": True,
            "is_featured": True,
            "characteristics": {"size": "L", "material": "Спандекс", "color": "Черный"},
            "images": ["test_image.jpg"]
        },
        {
            "category": "aksessuary",
            "name": "Чехол для чемодана размер M",
            "slug": "chekhol-chemodan-razmer-m",
            "description": "Универсальный чехол среднего размера. Легко надевается",
            "price": 750,
            "discount_percent": 0,   
            "is_active": True,
            "is_featured": False,
            "characteristics": {"material": "Спандекс", "color": "Серый"},
            "images": ["test_image.jpg"]
        },
    ]
    
    for product_data in products_data:
        # Создаем продукт
        product = Product(
            name=product_data["name"],
            slug=product_data["slug"],
            description=product_data["description"],
            price=product_data["price"],
            discount_percent=product_data["discount_percent"],
            is_active=product_data["is_active"],
            is_featured=product_data["is_featured"],
            category_id=categories[product_data["category"]].id
        )
        session.add(product)
        await session.flush()  # Получаем ID продукта
        
        # Добавляем изображения
        for idx, image_path in enumerate(product_data["images"]):
            image = ProductImage(
                image_path=image_path,
                order=idx,
                product_id=product.id
            )
            session.add(image)
        
        # Добавляем характеристики
        for char_slug, char_value in product_data["characteristics"].items():
            if char_slug in char_types:
                characteristic = ProductCharacteristic(
                    value=char_value,
                    product_id=product.id,
                    characteristic_type_id=char_types[char_slug].id
                )
                session.add(characteristic)
    
    logger.info("test_products_created", count=len(products_data))


async def init_reviews(session: AsyncSession) -> None:
    """Создание тестовых отзывов"""
    # Проверяем, есть ли уже отзывы
    result = await session.execute(select(Review))
    if result.scalars().first():
        logger.info("reviews_already_exist")
        return
    
    # Получаем первые 3 продукта для отзывов
    products_result = await session.execute(select(Product).limit(3))
    products = list(products_result.scalars().all())
    
    if not products:
        logger.warning("no_products_found_for_reviews")
        return
    
    reviews_data = [
        {
            "author_name": "Анна Смирнова",
            "content": "Отличный чемодан! Купила для отпуска в Турцию. Очень вместительный, легко катится на колесиках. Материал прочный, не царапается. Рекомендую!",
            "rating": 5,
            "image": None,
            "is_active": True,
            "product_id": products[0].id
        },
        {
            "author_name": "Дмитрий Петров",
            "content": "Хороший чемодан за свои деньги. Брал в командировку, всё поместилось. Единственный минус - замок туговат, но это не критично. В целом доволен покупкой.",
            "rating": 4,
            "image": "test_image.jpg",
            "is_active": True,
            "product_id": products[0].id
        },
        {
            "author_name": "Елена Васильева",
            "content": "Заказывала для дочери в университет. Чемодан легкий, удобный. Цвет яркий, сразу заметно на багажной ленте. Доставка быстрая, упаковка хорошая. Спасибо!",
            "rating": 5,
            "image": None,
            "is_active": True,
            "product_id": products[1].id if len(products) > 1 else products[0].id
        },
    ]
    
    for review_data in reviews_data:
        review = Review(**review_data)
        session.add(review)
    
    logger.info("test_reviews_created", count=len(reviews_data))


async def test_db(session: AsyncSession) -> None:
    try:
        await init_settings(session)
        await init_characteristic_types(session)
        await init_faq(session)
        await init_test_products(session)
        await init_reviews(session)
        
        await session.commit()
        logger.info("test_data_initialized")
        
    except Exception as e:
        await session.rollback()
        logger.error("test_data_initialization_failed", error=str(e), exc_info=True)
        raise
    finally:
        await session.close()
