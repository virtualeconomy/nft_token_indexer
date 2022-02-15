import asyncio

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, String, Integer

from conf import db_user, db_pass, db_ip, contract_ids

db_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_ip}"

engine = create_async_engine(db_url, echo=True)
Base = declarative_base()
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_models():

    async with engine.begin() as conn:

        for i in contract_ids:
  
            _ = Table(i, Base.metadata,
                            Column("token_idx", Integer, primary_key=True, index=True),
                            Column("user_addr", String, unique=True),
                            Column("amount", Integer),
                            )
        
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

asyncio.run(init_models())