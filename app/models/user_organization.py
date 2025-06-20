from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base

class UserOrganization(Base):
    __tablename__ = "user_organizations"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), primary_key=True)
    role = Column(String, default="member")  # admin, manager, member, etc.

    user = relationship("User", back_populates="organization_associations")
    organization = relationship("Organization", back_populates="user_associations") 