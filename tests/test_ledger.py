# Proves the ledger rules from docs/specs/ledger.md actually hold: a charge
# moves money, the same idempotency key never gets applied twice, and a
# refund can never give back more than was charged.

import asyncio
from collections.abc import Callable

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ledger import RefundExceedsChargeError, charge, get_balance, refund


async def test_charge_deducts_balance(
    db_session: AsyncSession, account_id: str
) -> None:
    await charge(db_session, account_id, 500, idempotency_key="charge-1")

    assert await get_balance(db_session, account_id) == -500


async def test_duplicate_charge_idempotency_key_applies_once(
    db_session: AsyncSession, account_id: str
) -> None:
    first = await charge(db_session, account_id, 500, idempotency_key="charge-1")
    second = await charge(db_session, account_id, 500, idempotency_key="charge-1")

    assert second.duplicate is True
    assert second.entry_id == first.entry_id
    assert await get_balance(db_session, account_id) == -500


async def test_refund_credits_balance(
    db_session: AsyncSession, account_id: str
) -> None:
    charged = await charge(db_session, account_id, 500, idempotency_key="charge-1")
    await refund(
        db_session, charged.entry_id, 200, idempotency_key="refund-1"
    )

    assert await get_balance(db_session, account_id) == -300


async def test_duplicate_refund_idempotency_key_applies_once(
    db_session: AsyncSession, account_id: str
) -> None:
    charged = await charge(db_session, account_id, 500, idempotency_key="charge-1")
    first = await refund(
        db_session, charged.entry_id, 200, idempotency_key="refund-1"
    )
    second = await refund(
        db_session, charged.entry_id, 200, idempotency_key="refund-1"
    )

    assert second.duplicate is True
    assert second.entry_id == first.entry_id
    assert await get_balance(db_session, account_id) == -300


async def test_refund_cannot_exceed_charge(
    db_session: AsyncSession, account_id: str
) -> None:
    charged = await charge(db_session, account_id, 500, idempotency_key="charge-1")

    with pytest.raises(RefundExceedsChargeError):
        await refund(
            db_session, charged.entry_id, 600, idempotency_key="refund-1"
        )

    assert await get_balance(db_session, account_id) == -500


async def test_concurrent_double_submit_charges_once(
    db_session: AsyncSession,
    make_session: Callable[[], AsyncSession],
    account_id: str,
) -> None:
    # Two genuinely separate sessions, standing in for two separate real
    # requests (e.g. a client's original attempt and its retry after a
    # dropped connection) — racing each other with the SAME idempotency
    # key, fired at the same instant via asyncio.gather.
    async with make_session() as session_a, make_session() as session_b:
        result_a, result_b = await asyncio.gather(
            charge(session_a, account_id, 500, idempotency_key="race-1"),
            charge(session_b, account_id, 500, idempotency_key="race-1"),
        )

    # Which one "won" the race is unpredictable and must not matter to the
    # test — only that exactly one won, both agree on which row it was,
    # and the account was only ever charged once.
    assert {result_a.duplicate, result_b.duplicate} == {True, False}
    assert result_a.entry_id == result_b.entry_id
    assert await get_balance(db_session, account_id) == -500


async def test_failed_charge_leaves_no_trace(
    db_session: AsyncSession, account_id: str
) -> None:
    # A negative amount violates the amount_cents > 0 check constraint -
    # a failure that has nothing to do with idempotency. This must not be
    # silently swallowed as "must be a duplicate" (see app/ledger.py's
    # _commit_or_get_existing): the real error should surface, and the
    # account must be completely unaffected, not half-charged.
    with pytest.raises(IntegrityError):
        await charge(db_session, account_id, -100, idempotency_key="bad-amount")

    assert await get_balance(db_session, account_id) == 0


async def test_refund_of_a_refund_is_rejected(
    db_session: AsyncSession, account_id: str
) -> None:
    charged = await charge(db_session, account_id, 500, idempotency_key="charge-1")
    refunded = await refund(
        db_session, charged.entry_id, 200, idempotency_key="refund-1"
    )

    # refunded.entry_id is a refund row, not a charge - refunding it would
    # mean giving back money that was never taken from the account twice
    # over, or crediting an account for a refund of a refund. It's not a
    # charge at all, so it must be rejected outright.
    with pytest.raises(ValueError):
        await refund(db_session, refunded.entry_id, 100, idempotency_key="refund-2")

    assert await get_balance(db_session, account_id) == -300


async def test_partial_refunds_cannot_exceed_charge_cumulatively(
    db_session: AsyncSession, account_id: str
) -> None:
    charged = await charge(db_session, account_id, 500, idempotency_key="charge-1")
    await refund(db_session, charged.entry_id, 300, idempotency_key="refund-1")

    with pytest.raises(RefundExceedsChargeError):
        await refund(db_session, charged.entry_id, 300, idempotency_key="refund-2")

    assert await get_balance(db_session, account_id) == -200
