# This file answers: "what does one row of the `notes` table look like?"
# Each class below is a Python stand-in for a real SQL table — SQLAlchemy (the
# library) translates between "a Note object in Python" and "a row in
# Postgres" automatically. This is called an ORM (Object-Relational Mapper).

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Every table class in the app inherits from this shared Base. SQLAlchemy
# uses it to collect "every table this app knows about" in one place —
# that collection is what the Alembic migration reads to build the schema.
class Base(DeclarativeBase):
    pass


# One Note = one row in the "notes" table.
class Note(Base):
    __tablename__ = "notes"

    # Auto-incrementing unique ID, and the table's primary key (how every
    # other table would reference "this specific note", if one needed to).
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # The note's actual content. nullable=False means Postgres will refuse
    # to save a note with no text — a safety net at the database level.
    text: Mapped[str] = mapped_column(String, nullable=False)

    # server_default=func.now() means Postgres itself fills in the
    # timestamp when a row is inserted — we never have to set this from
    # Python, so it can't be forgotten or set to the wrong clock.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# One row per money movement on an account: either a "charge" (money taken)
# or a "refund" (money given back). We never update a row after it's
# written — the account's balance is always recomputed from the full list
# of entries, so there's one source of truth instead of a balance number
# that could drift out of sync with what actually happened.
class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Which account this money movement belongs to.
    account_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # "charge" or "refund" — which direction the money moved.
    kind: Mapped[str] = mapped_column(String, nullable=False)

    # Always positive. A refund's direction comes from `kind`, not from a
    # negative number — negative amounts would let a bug (or a bad actor)
    # sneak a balance-increasing "charge" past validation meant for charges.
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    # The caller-supplied "don't do this twice" tag (see docs/specs/ledger.md).
    # unique=True is what makes idempotency airtight: Postgres itself refuses
    # a second row with the same key, even under concurrent requests — we
    # don't have to trust application code to check-then-insert safely.
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    # Only set on refund rows: which charge this refund is against. Lets us
    # ask "how much of this specific charge has already been refunded?"
    charge_id: Mapped[int | None] = mapped_column(
        ForeignKey("ledger_entries.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_ledger_entries_amount_positive"),
        CheckConstraint(
            "kind IN ('charge', 'refund')", name="ck_ledger_entries_kind_valid"
        ),
    )
