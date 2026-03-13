from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..exceptions import NotFoundException
from ..models import Tag
from ..schemas import TagCreate, TagRead, SuccessResponse

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=SuccessResponse[list[TagRead]])
def list_tags(db: Session = Depends(get_db)):
    """List all tags."""
    tags = db.query(Tag).order_by(Tag.name).all()
    data = [TagRead.model_validate(tag) for tag in tags]
    return SuccessResponse(ok=True, data=data)


@router.post("/", response_model=SuccessResponse[TagRead], status_code=201)
def create_tag(payload: TagCreate, db: Session = Depends(get_db)):
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
    return SuccessResponse(ok=True, data=TagRead.model_validate(tag))


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a tag by ID."""
    tag = db.get(Tag, tag_id)
    if not tag:
        raise NotFoundException("Tag", tag_id)
    db.delete(tag)
    db.flush()
