
from sqlalchemy import select
from passlib.context import CryptContext

from app.infrastructure.database.models.admin import Admin
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker


async def test_db(session: AsyncSession):
    try:
        is_exist = (await session.execute(select(Admin))).scalars().all()
        if is_exist:
            return
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        admin = Admin(login="admin123", password=pwd_context.hash("admin123"))
        session.add(admin)

        await session.commit()
    except Exception as e:
        raise e
    finally:
        await session.close()
