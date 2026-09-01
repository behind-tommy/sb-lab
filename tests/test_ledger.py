# Proves the ledger rules from docs/specs/ledger.md actually hold: a charge
# moves money, the same idempotency key never gets applied twice, and a
# refund can never give back more than was charged.

import pytest
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


async def test_partial_refunds_cannot_exceed_charge_cumulatively(
    db_session: AsyncSession, account_id: str
) -> None:
    charged = await charge(db_session, account_id, 500, idempotency_key="charge-1")
    await refund(db_session, charged.entry_id, 300, idempotency_key="refund-1")

    with pytest.raises(RefundExceedsChargeError):
        await refund(db_session, charged.entry_id, 300, idempotency_key="refund-2")

    assert await get_balance(db_session, account_id) == -200
