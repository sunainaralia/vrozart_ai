from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base

class WorkspaceUser(Base):
    __tablename__ = "workspace_users"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), primary_key=True)

    user = relationship("User", back_populates="workspaces")
    workspace = relationship("Workspace", back_populates="users")
