from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str


class TagRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    title: str
    content: str
    tag_ids: list[int] = []


class NoteRead(BaseModel):
    id: int
    title: str
    content: str
    tags: list[TagRead] = []

    class Config:
        from_attributes = True


class ActionItemCreate(BaseModel):
    description: str


class ActionItemRead(BaseModel):
    id: int
    description: str
    completed: bool

    class Config:
        from_attributes = True
