# This file answers: "how do we move money on an account without ever
# double-charging, double-refunding, or refunding more than was charged?"
# Every operation here runs as one all-or-nothing database transaction, so
# there's no moment where a crash could leave a half-finished charge behind.

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LedgerEntry


# Raised when a refund would give back more money than was actually
# charged (accounting for any refunds already applied to that same charge).
class RefundExceedsChargeError(Exception):
    pass


# What charge()/refund() hand back: which row it is, and whether this was
# a brand-new entry or just a replay of a request we'd already seen
# (duplicate=True means "nothing changed, here's what happened last time").
@dataclass
class LedgerResult:
    entry_id: int
    amount_cents: int
    duplicate: bool


# Records a charge against an account. "idempotency_key" is the caller's
# way of saying "this is one specific request" — if the same key shows up
# again (e.g. a retried network call), we don't charge a second time.
async def charge(
    session: AsyncSession,
    account_id: str,
    amount_cents: int,
    idempotency_key: str,
) -> LedgerResult:
    entry = LedgerEntry(
        account_id=account_id,
        kind="charge",
        amount_cents=amount_cents,
        idempotency_key=idempotency_key,
    )
    session.add(entry)
    try:
        await session.commit()
    except IntegrityError:
        # Someone already used this exact idempotency key. Postgres's
        # unique constraint is what actually caught this — not a
        # check-then-insert in Python, which could race under concurrent
        # requests. Roll back the failed attempt, then look up what
        # happened last time and report that instead.
        await session.rollback()
        existing = await _get_by_idempotency_key(session, idempotency_key)
        assert existing is not None
        return LedgerResult(
            entry_id=existing.id, amount_cents=existing.amount_cents, duplicate=True
        )

    return LedgerResult(entry_id=entry.id, amount_cents=entry.amount_cents, duplicate=False)


# Records a refund against a specific charge. Refuses if this refund, added
# to any refunds already made against that charge, would exceed what was
# originally charged.
async def refund(
    session: AsyncSession,
    charge_id: int,
    amount_cents: int,
    idempotency_key: str,
) -> LedgerResult:
    # Lock the charge row for the rest of this transaction so two
    # concurrent refunds against the same charge can't both read
    # "not exceeded yet" before either one commits (the exact "crash
    # between two writes" class of bug this lesson is about).
    charged = await session.get(LedgerEntry, charge_id, with_for_update=True)
    if charged is None or charged.kind != "charge":
        raise ValueError(f"no charge with id {charge_id}")

    already_refunded = await _sum_refunds_for_charge(session, charge_id)
    charge_amount_cents = charged.amount_cents  # read before rollback expires it
    if already_refunded + amount_cents > charge_amount_cents:
        # Release the row lock (and the SELECT FOR UPDATE's open
        # transaction) before raising, rather than leaving it held until
        # whatever the caller does next.
        await session.rollback()
        raise RefundExceedsChargeError(
            f"refund of {amount_cents} would exceed remaining refundable amount "
            f"({charge_amount_cents - already_refunded}) on charge {charge_id}"
        )

    entry = LedgerEntry(
        account_id=charged.account_id,
        kind="refund",
        amount_cents=amount_cents,
        idempotency_key=idempotency_key,
        charge_id=charge_id,
    )
    session.add(entry)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await _get_by_idempotency_key(session, idempotency_key)
        assert existing is not None
        return LedgerResult(
            entry_id=existing.id, amount_cents=existing.amount_cents, duplicate=True
        )

    return LedgerResult(entry_id=entry.id, amount_cents=entry.amount_cents, duplicate=False)


# The account's current balance: every charge lowers it, every refund
# raises it. Because a duplicate charge/refund never gets a second row (see
# above), a plain sum here is automatically correct — no separate
# "have we already counted this" bookkeeping needed.
async def get_balance(session: AsyncSession, account_id: str) -> int:
    result = await session.execute(
        select(LedgerEntry).where(LedgerEntry.account_id == account_id)
    )
    total = 0
    for entry in result.scalars():
        total += entry.amount_cents if entry.kind == "refund" else -entry.amount_cents
    return total


async def _get_by_idempotency_key(
    session: AsyncSession, idempotency_key: str
) -> LedgerEntry | None:
    result = await session.execute(
        select(LedgerEntry).where(LedgerEntry.idempotency_key == idempotency_key)
    )
    return result.scalar_one_or_none()


async def _sum_refunds_for_charge(session: AsyncSession, charge_id: int) -> int:
    result = await session.execute(
        select(LedgerEntry).where(
            LedgerEntry.charge_id == charge_id, LedgerEntry.kind == "refund"
        )
    )
    return sum(entry.amount_cents for entry in result.scalars())
