import os
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-at-least-thirty-two-characters"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["STORAGE_MODE"] = "memory"

from app.core.dependencies import get_db
from app.db.base import Base
from app.main import app


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite://")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record: object) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_engine) -> AsyncIterator[AsyncClient]:
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()
