import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.cf_user import CFUser
    from app.models.contest import Contest
    from app.models.problem_attempt import ProblemAttempt


class ContestParticipation(Base):
    __tablename__ = "contest_participations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cf_users.id")
    )

    contest_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contests.id")
    )

    rank: Mapped[int | None] = mapped_column()

    score: Mapped[float | None] = mapped_column()

    rating_before: Mapped[int | None] = mapped_column()

    rating_after: Mapped[int | None] = mapped_column()

    rating_change: Mapped[int | None] = mapped_column()

    problems_solved: Mapped[int | None] = mapped_column()

    # Relationships
    user: Mapped["CFUser"] = relationship(back_populates="participations")
    contest: Mapped["Contest"] = relationship(back_populates="participations")
    attempts: Mapped[list["ProblemAttempt"]] = relationship(
        back_populates="participation",
        cascade="all, delete-orphan"
    )