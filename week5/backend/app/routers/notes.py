from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Note, Tag, ActionItem
from ..schemas import NoteCreate, NoteRead, NoteSearchResponse, NoteSearchResponseWithTags, NoteReadWithTags, TagRead, NoteUpdate, ExtractionResult, ExtractRequest
from ..services.extract import extract_all

router = APIRouter(prefix="/notes", tags=["notes"])


# Request model for attaching tags
class TagAttachRequest(BaseModel):
    tag_ids: list[int]


# Note-Tag relationship endpoints (under /notes prefix)

@router.post("/{note_id}/tags", response_model=NoteReadWithTags)
def attach_tags_to_note(note_id: int, payload: TagAttachRequest, db: Session = Depends(get_db)) -> NoteReadWithTags:
    """Attach tags to a note."""
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Fetch all tags by IDs
    tags = db.query(Tag).filter(Tag.id.in_(payload.tag_ids)).all()
    if len(tags) != len(payload.tag_ids):
        raise HTTPException(status_code=404, detail="One or more tags not found")

    # Replace tags
    note.tags = tags
    db.flush()
    db.refresh(note)
    return NoteReadWithTags.model_validate(note)


@router.delete("/{note_id}/tags/{tag_id}", status_code=204)
def detach_tag_from_note(note_id: int, tag_id: int, db: Session = Depends(get_db)) -> None:
    """Detach a tag from a note."""
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if tag in note.tags:
        note.tags.remove(tag)
    db.flush()


@router.post("/{note_id}/extract", response_model=ExtractionResult)
def extract_from_note(note_id: int, payload: ExtractRequest, db: Session = Depends(get_db)) -> ExtractionResult:
    """Extract hashtags, checkbox tasks, and legacy items from a note."""
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Extract all patterns
    result = extract_all(note.content)

    if payload.apply:
        # Create tags first and commit them
        tag_ids = []
        for tag_name in result["hashtags"]:
            existing_tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not existing_tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
                tag_ids.append(tag.id)
            else:
                tag_ids.append(existing_tag.id)

        # Re-query note to ensure clean state
        note = db.query(Note).filter(Note.id == note_id).first()

        # Fetch tags by IDs and assign
        if tag_ids:
            tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
            note.tags = list(tags)

        # Create action items for checkbox tasks
        existing_action_descriptions = {item.description for item in note.action_items}
        for task_description in result["action_items"]:
            if task_description not in existing_action_descriptions:
                action_item = ActionItem(description=task_description, completed=False, note_id=note_id)
                db.add(action_item)

        db.flush()

    return ExtractionResult(**result)


@router.get("/by-tag/{tag_id}", response_model=list[NoteReadWithTags])
def get_notes_by_tag(tag_id: int, db: Session = Depends(get_db)) -> list[NoteReadWithTags]:
    """Get all notes with a specific tag."""
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    notes = db.execute(
        select(Note).where(Note.tags.any(Tag.id == tag_id))
    ).scalars().all()

    return [NoteReadWithTags.model_validate(note) for note in notes]


# Redirect /notes to /notes/ for consistency
@router.get("")
def list_notes_redirect():
    return RedirectResponse(url="/notes/")


@router.get("/", response_model=list[NoteReadWithTags])
def list_notes(db: Session = Depends(get_db)) -> list[NoteReadWithTags]:
    rows = db.execute(select(Note)).scalars().all()
    return [NoteReadWithTags.model_validate(row) for row in rows]


@router.post("/", response_model=NoteRead, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteRead:
    note = Note(title=payload.title, content=payload.content)
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.get("/search", response_model=list[NoteRead])
def search_notes_redirect():
    return RedirectResponse(url="/notes/search/")


@router.get("/search/", response_model=NoteSearchResponseWithTags)
def search_notes(
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    sort: str = "created_desc",
    db: Session = Depends(get_db)
) -> NoteSearchResponseWithTags:
    # Cap page_size at 100
    page_size = min(page_size, 100)

    # Ensure page is at least 1
    page = max(page, 1)

    # Build base query
    query = select(Note)
    count_query = select(func.count()).select_from(Note)

    # Add case-insensitive search filter if query provided
    if q:
        search_filter = (func.lower(Note.title).contains(q.lower())) | (func.lower(Note.content).contains(q.lower()))
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Get total count
    total = db.execute(count_query).scalar() or 0

    # Apply sorting
    sort_options = {
        "created_asc": Note.id.asc(),
        "created_desc": Note.id.desc(),
        "title_asc": Note.title.asc(),
        "title_desc": Note.title.desc(),
    }
    order_by = sort_options.get(sort, Note.id.desc())
    query = query.order_by(order_by)

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    rows = db.execute(query).scalars().all()

    return NoteSearchResponseWithTags(
        items=[NoteReadWithTags.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{note_id}", response_model=NoteReadWithTags)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteReadWithTags:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteReadWithTags.model_validate(note)


@router.put("/{note_id}", response_model=NoteRead)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)) -> NoteRead:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.title = payload.title
    note.content = payload.content
    db.flush()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> None:
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.flush()
