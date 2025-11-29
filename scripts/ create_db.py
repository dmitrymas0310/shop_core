import asyncio
from app.core.db import engine, Base

async def create_db():
    async with engine.begin() as connection:
        #await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    print("Database created or dropped successfully.")

if __name__ == "__main__":
    asyncio.run(create_db())
