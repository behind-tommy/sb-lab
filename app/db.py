# This file answers: "how does the app talk to Postgres without opening a new,
# slow connection for every single request?"
# Answer: a connection pool — a small set of connections opened once and
# reused. Each incoming request borrows one, uses it, and returns it.

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# The "engine" is the pool itself. pool_size=5 means at most 5 connections to
# Postgres are open at once, no matter how many requests arrive concurrently.
# This doesn't connect to the database yet — it just prepares to.
engine = create_async_engine(settings.database_url, pool_size=5)

# A factory for creating a "session" (a single conversation with the
# database — the thing you actually run queries through).
async_session = async_sessionmaker(engine, expire_on_commit=False)


# FastAPI calls this once per request (see Depends(get_session) in main.py).
# It hands the request one session, and automatically closes it — returning
# the connection to the pool — when the request is done, even if it crashed.
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
