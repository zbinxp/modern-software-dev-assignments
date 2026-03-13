from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..db import get_db
from ..exceptions import NotFoundException
from ..models import ActionItem
from ..schemas import ActionItemCreate, ActionItemRead, SuccessResponse, PaginatedActionItemResponse

router = APIRouter(prefix="/action-items", tags=["action_items"])


# Redirect /action-items to /action-items/ for consistency
@router.get("")
def list_items_redirect():
    return RedirectResponse(url="/action-items/")


@router.get("/", response_model=SuccessResponse[PaginatedActionItemResponse])
def list_items(
    completed: Optional[bool] = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    # Cap page_size at 100
    page_size = min(page_size, 100)

    # Ensure page is at least 1
    page = max(page, 1)

    # Build base query
    query = select(ActionItem)
    count_query = select(func.count()).select_from(ActionItem)

    # Apply filter if provided
    if completed is not None:
        query = query.where(ActionItem.completed == completed)
        count_query = count_query.where(ActionItem.completed == completed)

    # Get total count
    total = db.execute(count_query).scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    rows = db.execute(
        query.offset(offset).limit(page_size)
    ).scalars().all()

    data = PaginatedActionItemResponse(
        items=[ActionItemRead.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size
    )
    return SuccessResponse(ok=True, data=data)


@router.post("/", response_model=SuccessResponse[ActionItemRead], status_code=201)
def create_item(payload: ActionItemCreate, db: Session = Depends(get_db)):
    item = ActionItem(description=payload.description, completed=False)
    db.add(item)
    db.flush()
    db.refresh(item)
    return SuccessResponse(ok=True, data=ActionItemRead.model_validate(item))


@router.put("/{item_id}/complete", response_model=SuccessResponse[ActionItemRead])
def complete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(ActionItem, item_id)
    if not item:
        raise NotFoundException("ActionItem", item_id)
    item.completed = True
    db.add(item)
    db.flush()
    db.refresh(item)
    return SuccessResponse(ok=True, data=ActionItemRead.model_validate(item))


class BulkCompleteRequest(BaseModel):
    ids: list[int]


@router.post("/bulk-complete", response_model=SuccessResponse[list[ActionItemRead]])
def bulk_complete_items(
    payload: BulkCompleteRequest,
    db: Session = Depends(get_db)
):
    try:
        items = []
        for item_id in payload.ids:
            item = db.get(ActionItem, item_id)
            if not item:
                raise NotFoundException("ActionItem", item_id)
            item.completed = True
            items.append(item)

        db.commit()
        data = [ActionItemRead.model_validate(item) for item in items]
        return SuccessResponse(ok=True, data=data)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to complete items - transaction rolled back"
        )
