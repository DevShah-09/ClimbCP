import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.contest_participation import ContestParticipation
    from app.models.ai_report import AIReport


class Contest(Base):
    __tablename__ = "contests"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    platform: Mapped[str] = mapped_column(
        String(30)
    )

    contest_code: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    contest_name: Mapped[str] = mapped_column(
        String(255)
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime
    )

    # Relationships
    participations: Mapped[list["ContestParticipation"]] = relationship(
        back_populates="contest",
        cascade="all, delete-orphan"
    )
    reports: Mapped[list["AIReport"]] = relationship(
        back_populates="contest"
    )