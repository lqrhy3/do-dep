from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.settings import settings

async_engine = create_async_engine(settings.db.url, echo=False, future=True)
engine = create_engine(settings.db.url, echo=False, future=True)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

SessionLocal = sessionmaker(engine, autoflush=True, autocommit=False, future=True)


async def get_async_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
