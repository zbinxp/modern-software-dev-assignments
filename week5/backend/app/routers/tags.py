from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Tag
from ..schemas import TagCreate, TagRead

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=list[TagRead])
def list_tags(db: Session = Depends(get_db)) -> list[TagRead]:
    """List all tags."""
    tags = db.query(Tag).order_by(Tag.name).all()
    return [TagRead.model_validate(tag) for tag in tags]


@router.post("/", response_model=TagRead, status_code=201)
def create_tag(payload: TagCreate, db: Session = Depends(get_db)) -> TagRead:
    """Create a new tag."""
    # Normalize tag name to lowercase
    tag_name = payload.name.lower().strip()

    # Check if tag with same name already exists
    existing = db.query(Tag).filter(Tag.name == tag_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag with this name already exists")

    tag = Tag(name=tag_name)
    db.add(tag)
    db.commit()  # Commit immediately to ensure the tag is saved
    db.refresh(tag)
    return TagRead.model_validate(tag)


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a tag by ID."""
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.flush()
