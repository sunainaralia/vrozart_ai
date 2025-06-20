from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base
from datetime import datetime
import uuid

class Chat(Base):
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    model = Column(String)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    workspace = relationship("Workspace", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete")
    documents = relationship("Document", back_populates="chat", cascade="all, delete")
