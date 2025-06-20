from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base
import uuid

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True)

    users = relationship("WorkspaceUser", back_populates="workspace", cascade="all, delete")
    chats = relationship("Chat", back_populates="workspace", cascade="all, delete")

