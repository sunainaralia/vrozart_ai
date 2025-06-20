from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base

class UserDepartment(Base):
    __tablename__ = "user_departments"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), primary_key=True)
    role = Column(String, default="member")

    user = relationship("User", back_populates="department_associations")
    department = relationship("Department", back_populates="user_associations") 