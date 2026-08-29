# This file answers: "how does the app talk to Postgres without opening a new,
# slow connection for every single request?"
# Answer: a connection pool — a small set of connections opened once and
# reused. Each incoming request borrows one, uses it, and returns it.

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# The "engine" is the pool itself. pool_size=1 means at most 1 connection to
# Postgres is open at once — deliberately shrunk from 5 for lesson 1's
# "break it" exercise, to demonstrate pool exhaustion under concurrent load.
# max_overflow=0 stops SQLAlchemy from quietly opening extra temporary
# connections beyond pool_size, which would hide the effect we're showing.
# pool_timeout=3 makes a starved request fail fast (3s) instead of hanging
# for SQLAlchemy's 30s default.
engine = create_async_engine(
    settings.database_url, pool_size=1, max_overflow=0, pool_timeout=3
)

# A factory for creating a "session" (a single conversation with the
# database — the thing you actually run queries through).
async_session = async_sessionmaker(engine, expire_on_commit=False)


# FastAPI calls this once per request (see Depends(get_session) in main.py).
# It hands the request one session, and automatically closes it — returning
# the connection to the pool — when the request is done, even if it crashed.
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
