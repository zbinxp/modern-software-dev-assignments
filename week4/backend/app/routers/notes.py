
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Note, Tag
from ..schemas import NoteCreate, NoteRead, TagRead

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/", response_model=list[NoteRead])
def list_notes(db: Session = Depends(get_db)) -> list[NoteRead]:
    rows = db.execute(select(Note)).scalars().all()
    return [NoteRead.model_validate(row) for row in rows]


@router.post("/", response_model=NoteRead, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteRead:
    note = Note(title=payload.title, content=payload.content)
    db.add(note)
    db.flush()

    # Add tags if tag_ids provided
    if payload.tag_ids:
        tags = db.execute(select(Tag).where(Tag.id.in_(payload.tag_ids))).scalars().all()
        note.tags.extend(tags)

    db.refresh(note)
    return NoteRead.model_validate(note)


@router.get("/search/", response_model=list[NoteRead])
def search_notes(q: str | None = None, db: Session = Depends(get_db)) -> list[NoteRead]:
    if not q:
        rows = db.execute(select(Note)).scalars().all()
    else:
        rows = (
            db.execute(select(Note).where((Note.title.contains(q)) | (Note.content.contains(q))))
            .scalars()
            .all()
        )
    return [NoteRead.model_validate(row) for row in rows]


@router.get("/tags/", response_model=list[TagRead])
def list_tags(db: Session = Depends(get_db)) -> list[TagRead]:
    rows = db.execute(select(Tag)).scalars().all()
    return [TagRead.model_validate(row) for row in rows]


@router.get("/{note_id}", response_model=NoteRead)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteRead.model_validate(note)
