# Runs before any test file imports the app. The app refuses to start
# without a database address (see app/config.py). In CI, DATABASE_URL is
# already set to a real, throwaway Postgres container before pytest even
# starts, so the line below does nothing there. Locally, it defaults to a
# real local database (sb_lab_test) — real, not fake, because tests like
# test_ledger.py need to prove actual Postgres behavior (a unique
# constraint really stopping a duplicate, a transaction really leaving no
# half-written data), which a fake connection could never prove.

import os
import uuid
from collections.abc import AsyncGenerator, Callable

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault(
    "DATABASE_URL",
    f"postgresql+asyncpg://{os.environ.get('USER', 'postgres')}@localhost/sb_lab_test",
)

from app.config import settings


@pytest_asyncio.fixture
async def make_session() -> AsyncGenerator[Callable[[], AsyncSession], None]:
    # Hands out however many independent sessions a test needs, all backed
    # by the same connection pool. A single session isn't safe to use from
    # two operations happening at once — this is what the concurrency test
    # needs: two genuinely separate sessions racing each other, the way two
    # separate real requests would each get their own.
    #
    # Built fresh inside the fixture (not at module import time) so it's
    # always created within the current test's event loop — pytest-asyncio
    # gives each test its own loop, and an asyncpg connection created under
    # one loop can't be reused from another (that's the "another operation
    # is in progress" error you get if you build this at module scope).
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    yield session_factory
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(
    make_session: Callable[[], AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with make_session() as session:
        # Unlike CI's Postgres service container (thrown away after every
        # run), a local database persists between test runs. Without this,
        # a hardcoded idempotency key from a previous run (e.g. "charge-1")
        # would already exist, and the *next* run's charge() call would
        # correctly-but-confusingly treat it as a duplicate.
        await session.execute(text("DELETE FROM ledger_entries"))
        await session.commit()
        yield session


@pytest.fixture
def account_id() -> str:
    # A fresh, unique account per test avoids one test's data ever bleeding
    # into another test's balance calculation, without needing to wipe the
    # whole table between tests.
    return f"acct_{uuid.uuid4().hex[:12]}"
