from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.settings import settings

engine = create_async_engine(settings.db.url, echo=False, future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_async_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
