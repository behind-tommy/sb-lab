# This file is the app's front door: it lists every URL the outside world can
# call (the "routes"), and wires together config, the database, and logging
# (the other files in this folder) into one running program.

from datetime import datetime

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.logging import RequestIDMiddleware, logger
from app.models import Note

app = FastAPI()
# Every request now passes through RequestIDMiddleware first (see logging.py).
app.add_middleware(RequestIDMiddleware)


# The simplest possible route: "are you alive?" Railway pings this after
# every deploy to decide whether the new version is healthy enough to start
# receiving real traffic.
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# "Shape of the data allowed IN" when creating a note — FastAPI rejects a
# request automatically if the JSON body doesn't match this (e.g. no `text`).
class NoteIn(BaseModel):
    text: str


# "Shape of the data sent OUT" — separate from NoteIn because a note we're
# returning has an id and created_at that Postgres assigned, which a note
# we're creating doesn't have yet.
class NoteOut(BaseModel):
    id: int
    text: str
    created_at: datetime

    # Lets FastAPI build a NoteOut directly from a Note database object
    # (an ORM row), not just from a plain dict.
    model_config = {"from_attributes": True}


# GET /notes — fetch every note, oldest first.
@app.get("/notes", response_model=list[NoteOut])
async def list_notes(session: AsyncSession = Depends(get_session)) -> list[Note]:
    result = await session.execute(select(Note).order_by(Note.id))
    notes = list(result.scalars().all())
    logger.info("notes_listed", count=len(notes))
    return notes


# POST /notes — create one note and save it.
@app.post("/notes", response_model=NoteOut, status_code=201)
async def create_note(
    note: NoteIn, session: AsyncSession = Depends(get_session)
) -> Note:
    db_note = Note(text=note.text)
    session.add(db_note)            # stage the insert
    await session.commit()          # actually write it to Postgres
    await session.refresh(db_note)  # pull back the id/created_at Postgres generated
    logger.info("note_created", note_id=db_note.id)
    return db_note
