"""
Initialize Database
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import engine, Base
from app.database.init_data import init_sample_data


async def init_database():
    """Initialize the database"""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

    print("Initializing sample data...")
    await init_sample_data()
    print("Sample data initialized successfully!")
    print("Database initialization completed!")


if __name__ == "__main__":
    asyncio.run(init_database())
