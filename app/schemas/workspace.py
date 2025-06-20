from pydantic import BaseModel
from uuid import UUID

class WorkspaceCreate(BaseModel):
    name: str

class WorkspaceOut(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True
