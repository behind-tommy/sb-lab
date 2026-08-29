# This file answers: "what does one row of the `notes` table look like?"
# Each class below is a Python stand-in for a real SQL table — SQLAlchemy (the
# library) translates between "a Note object in Python" and "a row in
# Postgres" automatically. This is called an ORM (Object-Relational Mapper).

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
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
