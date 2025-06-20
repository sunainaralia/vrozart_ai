from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String,nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspaces = relationship("WorkspaceUser", back_populates="user", lazy="dynamic", cascade="all, delete")
    messages = relationship("Message", back_populates="user", cascade="all, delete")

    organization_associations = relationship("UserOrganization", back_populates="user", cascade="all, delete")
    department_associations = relationship("UserDepartment", back_populates="user", cascade="all, delete")
    team_associations = relationship("UserTeam", back_populates="user", cascade="all, delete")
