import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.topic import Topic
    from app.models.problem_attempt import ProblemAttempt
    from app.models.recommendation import Recommendation


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    platform: Mapped[str] = mapped_column(
        String(30)
    )

    problem_code: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    difficulty: Mapped[int | None] = mapped_column()

    # Relationships
    topics: Mapped[list["Topic"]] = relationship(
        secondary="problem_topics",
        back_populates="problems"
    )
    attempts: Mapped[list["ProblemAttempt"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan"
    )