from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# echo True увидем какие логи - какие sql запросы отправляет приложение к БД 
engine = create_async_engine(settings.db.dsl, echo=True)

# Из движка нужно получить сессию (наш коннект), 
# sessionmaker принимает движок и передать параметр, что сессия будет асинхронной
# expire_on_commit - способ работы нашей сессии - как ей и когда закрываться  
# =False - оставалась открытой 

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()