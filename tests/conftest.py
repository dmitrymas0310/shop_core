import pytest_asyncio
import aiohttp

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.core.config import settings


@pytest_asyncio.fixture(scope="function")
async def aiohttp_client():
    session = aiohttp.ClientSession(base_url="http://localhost:8000")
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(settings.db_test.dsl)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_schema_before_each_test(test_engine):
    """
    Полная очистка схемы между тестами.
    Это нужно, потому что тесты повторно регистрируют пользователя с тем же логином.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine):
    async_session_factory = sessionmaker(
        test_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session_factory() as session:
        yield session
