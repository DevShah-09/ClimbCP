import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.cp_profile import CPProfile
    from app.models.contest_participation import ContestParticipation
    from app.models.user_skill import UserSkill
    from app.models.recommendation import Recommendation
    from app.models.ai_report import AIReport
    from app.models.problem_attempt import ProblemAttempt


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    # Relationships
    cp_profiles: Mapped[list["CPProfile"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
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