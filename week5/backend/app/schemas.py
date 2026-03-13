from pydantic import BaseModel, Field
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class NoteUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class NoteRead(BaseModel):
    id: int
    title: str
    content: str

    class Config:
        from_attributes = True


class NoteSearchResponse(BaseModel):
    items: list[NoteRead]
    total: int
    page: int
    page_size: int


class ActionItemCreate(BaseModel):
    description: str = Field(..., min_length=1)


class ActionItemRead(BaseModel):
    id: int
    description: str
    completed: bool

    class Config:
        from_attributes = True


# Tag schemas
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1)


class TagRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class NoteReadWithTags(BaseModel):
    id: int
    title: str
    content: str
    tags: list[TagRead] = []

    class Config:
        from_attributes = True


class NoteSearchResponseWithTags(BaseModel):
    items: list[NoteReadWithTags]
    total: int
    page: int
    page_size: int


# Paginated list responses
class PaginatedNoteResponse(BaseModel):
    items: list[NoteReadWithTags]
    total: int
    page: int
    page_size: int


class PaginatedActionItemResponse(BaseModel):
    items: list[ActionItemRead]
    total: int
    page: int
    page_size: int


# Extraction schemas
class ExtractionResult(BaseModel):
    hashtags: list[str] = []
    action_items: list[str] = []
    legacy_items: list[str] = []


class ExtractRequest(BaseModel):
    apply: bool = False


# Response envelope schemas
class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    ok: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[T]):
    ok: bool = True
    data: T
