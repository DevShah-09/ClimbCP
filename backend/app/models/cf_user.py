import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.contest_participation import ContestParticipation
    from app.models.user_skill import UserSkill
    from app.models.recommendation import Recommendation
    from app.models.ai_report import AIReport
    from app.models.problem_attempt import ProblemAttempt
    from app.models.user_embedding import UserEmbedding


class CFUser(Base):
    __tablename__ = "cf_users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    handle: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    current_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    max_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    # Relationships
    participations: Mapped[list["ContestParticipation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    skills: Mapped[list["UserSkill"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    reports: Mapped[list["AIReport"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    attempts: Mapped[list["ProblemAttempt"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    embedding_rel: Mapped["UserEmbedding"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
