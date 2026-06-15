import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.problem import Problem
    from app.models.user_skill import UserSkill
    from app.models.recommendation import Recommendation


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    # Relationships
    problems: Mapped[list["Problem"]] = relationship(
        secondary="problem_topics",
        back_populates="topics"
    )
    user_skills: Mapped[list["UserSkill"]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="topic",
        cascade="all, delete-orphan"
    )