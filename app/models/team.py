from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base
import uuid
from datetime import datetime

class Team(Base):
    __tablename__ = "teams"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="teams")
    user_associations = relationship("UserTeam", back_populates="team", cascade="all, delete") 