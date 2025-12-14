import uuid
from datetime import datetime
from typing import AsyncGenerator


from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, declarative_mixin
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.core.config import settings

class Base(DeclarativeBase):
    pass

@declarative_mixin
class BaseModelMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


db_dsn = (
    settings.db_test.dsl
    if settings.app.mode == "test"
    else settings.db.dsl
)

# echo True увидем какие логи - какие sql запросы отправляет приложение к БД 
engine = create_async_engine(db_dsn, echo=True)

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