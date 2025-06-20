from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base

class UserTeam(Base):
    __tablename__ = "user_teams"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), primary_key=True)
    role = Column(String, default="member")

    user = relationship("User", back_populates="team_associations")
    team = relationship("Team", back_populates="user_associations") 