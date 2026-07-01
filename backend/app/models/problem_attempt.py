import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.cf_user import CFUser
    from app.models.contest_participation import ContestParticipation
    from app.models.problem import Problem


class ProblemAttempt(Base):
    __tablename__ = "problem_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cf_users.id")
    )

    participation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contest_participations.id"),
        nullable=True
    )

    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id")
    )

    solved: Mapped[bool] = mapped_column(Boolean)

    attempts: Mapped[int] = mapped_column(Integer, default=1)

    time_to_solve: Mapped[int | None] = mapped_column()

    penalty: Mapped[int | None] = mapped_column()

    verdict: Mapped[str | None] = mapped_column(String(30))

    language: Mapped[str | None] = mapped_column(String(30))

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    # Relationships
    user: Mapped["CFUser"] = relationship(back_populates="attempts")
    participation: Mapped["ContestParticipation | None"] = relationship(back_populates="attempts")
    problem: Mapped["Problem"] = relationship(back_populates="attempts")