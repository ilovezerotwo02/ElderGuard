"""Database Session Management"""
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


# Create async engine (disable SQL logging in bundled environment)
is_frozen = getattr(sys, 'frozen', False)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG and not is_frozen,  # Disable SQL echo in bundled environment
    future=True
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Database base class"""
    pass


async def get_db():
    """Dependency function for getting a database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
