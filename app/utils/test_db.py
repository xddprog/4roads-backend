from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.infrastructure.database.models.admin import Admin
from app.infrastructure.database.models.settings import Settings
from app.infrastructure.database.models.product import CharacteristicType
from app.infrastructure.database.models.faq import FAQ
from app.utils.enums import CharacteristicTypeEnum
from app.infrastructure.logging.logger import get_logger


logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


async def init_admin(session: AsyncSession) -> None:
    """Инициализация тестового админа"""
    result = await session.execute(select(Admin))
    if result.scalars().first():
        logger.info("admin_already_exists")
        return
    
    admin = Admin(
        login="admin123",
        password=pwd_context.hash("admin123")
    )
    session.add(admin)
    logger.info("admin_created", login="admin123")


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
        CharacteristicType(name=CharacteristicTypeEnum.SIZE, slug="size"),
        CharacteristicType(name=CharacteristicTypeEnum.MATERIAL, slug="material"),
        CharacteristicType(name=CharacteristicTypeEnum.WEIGHT, slug="weight"),
        CharacteristicType(name=CharacteristicTypeEnum.VOLUME, slug="volume"),
        CharacteristicType(name=CharacteristicTypeEnum.COLOR, slug="color"),
        CharacteristicType(name=CharacteristicTypeEnum.BRAND, slug="brand"),
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


async def test_db(session: AsyncSession) -> None:
    try:
        await init_admin(session)
        await init_settings(session)
        await init_characteristic_types(session)
        await init_faq(session)
        
        await session.commit()
        logger.info("test_data_initialized")
        
    except Exception as e:
        await session.rollback()
        logger.error("test_data_initialization_failed", error=str(e), exc_info=True)
        raise
    finally:
        await session.close()
